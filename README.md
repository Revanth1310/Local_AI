# Local AI Control Center

A **privacy-focused local AI chatbot and control center** built to run an LLM locally through **Ollama**, with a persistent long-term memory system, semantic memory search, conversation storage, and an offline-only safety controller.

The project is designed around the idea:

> **Run the AI locally, keep user memory locally, and prevent the local model from running while Internet connectivity is available.**

The application currently uses **Qwen3 4B** through Ollama and is designed to work on CPU-based systems.

---

## 1. Project Overview

Local AI Control Center combines four major systems:

1. **Local LLM Chat**
   - Uses Ollama as the local model server.
   - Uses `qwen3:4b` as the configured model.
   - No cloud LLM API is required for normal chat generation.

2. **Long-Term Memory**
   - Stores user memories in SQLite.
   - Converts memories into semantic embeddings.
   - Uses FAISS for fast similarity search.
   - Classifies memories into categories such as preferences, projects, personal information, interests, and general information.
   - Assigns importance and confidence scores.
   - Supports memory updates, deletion, and version history.

3. **Offline Safety Controller**
   - Checks whether Internet connectivity is available before starting Ollama.
   - Can automatically stop Ollama if Internet connectivity appears while the local AI server is running.
   - Monitors connectivity in a background thread.
   - Does **not** turn Wi-Fi/Ethernet on or off. Network disconnection remains a manual user action.

4. **Desktop-Style Web Control Center**
   - React + TypeScript + Vite frontend.
   - FastAPI backend.
   - Start/stop Ollama from the UI.
   - Chat with the local model.
   - View AI and safety settings.
   - Display Ollama status, PID, network state, and safety events.

---

## 2. Main Architecture

```text
                         ┌──────────────────────────┐
                         │        React UI          │
                         │   React + TypeScript     │
                         │        + Vite            │
                         └────────────┬─────────────┘
                                      │ HTTP
                                      ▼
                         ┌──────────────────────────┐
                         │       FastAPI API        │
                         │      backend/main.py     │
                         └────────────┬─────────────┘
                                      │
                 ┌────────────────────┼────────────────────┐
                 │                    │                    │
                 ▼                    ▼                    ▼
        ┌────────────────┐   ┌─────────────────┐   ┌─────────────────┐
        │ Safety         │   │ MemoryChat      │   │ Settings        │
        │ Controller     │   │                 │   │ Store           │
        └───────┬────────┘   └────────┬────────┘   └─────────────────┘
                │                     │
        ┌───────┴────────┐            │
        ▼                ▼            ▼
 NetworkGuard      OllamaManager   MemoryStore
        │                │            │
        ▼                ▼            ├──────────────┐
 Internet Check     Ollama Server     │              │
                                     ▼              ▼
                                  SQLite          FAISS
                                     │              │
                                     ▼              ▼
                                Memory Data    Embeddings
                                                    │
                                                    ▼
                                             BGE-small-en-v1.5

                                      │
                                      ▼
                              Ollama / Qwen3 4B
```

---

# 3. Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- Requests
- SQLite
- Sentence Transformers
- BAAI BGE-small-en-v1.5
- FAISS
- python-dotenv

## Local AI

- Ollama
- Qwen3 4B

## Frontend

- React
- TypeScript
- Vite
- Lucide React

## Operating System Integration

The current Ollama process-management implementation is designed primarily for **Windows**.

It uses:

- PowerShell
- `Get-NetTCPConnection`
- `Get-Process`
- `taskkill`
- Windows process management

---

# 4. Key Features

## 4.1 Local LLM Chat

The chatbot sends prompts to:

```text
http://127.0.0.1:11434/api/generate
```

The configured model is:

```text
qwen3:4b
```

The application requests non-streaming responses and cleans Qwen `<think>...</think>` sections before displaying the final answer.

The model generation settings include:

- `num_predict`
- `temperature`
- optional thinking mode

The frontend currently exposes response-length presets:

| UI Option | Maximum Tokens |
|---|---:|
| Short | 256 |
| Normal | 512 |
| Detailed | 1024 |
| Very Detailed | 2048 |

The backend permits a range of:

```text
64 - 4096
```

---

# 5. Long-Term Memory System

One of the main purposes of this project is to make the local chatbot behave more like a persistent personal assistant rather than a stateless chatbot.

The memory pipeline is:

```text
User Message
     │
     ▼
Memory Extraction
     │
     ▼
Memory Classification
     │
     ▼
Importance + Confidence
     │
     ▼
Semantic Embedding
     │
     ▼
SQLite + FAISS
     │
     ▼
Future User Query
     │
     ▼
Semantic Search
     │
     ▼
Memory Ranking
     │
     ▼
Relevant Memory Context
     │
     ▼
Qwen3
     │
     ▼
Final Answer
```

---

# 6. Memory Storage

SQLite is used as the persistent database.

Main database:

```text
memory.db
```

The memory database contains:

### `memories`

Stores the current active version of a memory.

Important fields include:

- `id`
- `content`
- `memory_type`
- `importance`
- `confidence`
- `source`
- `version`
- `created_at`
- `updated_at`
- `is_active`

### `memory_history`

Stores previous versions of memories.

This allows the system to maintain a history of changes instead of simply overwriting information.

### `conversations`

Stores:

- user message
- assistant response
- creation time

---

# 7. Memory Types

The current rule-based classifier supports:

```text
preference
project
personal
interest
general
```

Examples:

```text
"I prefer Python for backend development."
```

→ `preference`

```text
"I am building a local AI assistant."
```

→ `project`

```text
"I am interested in computer vision."
```

→ `interest`

The classifier is intentionally lightweight and does not require an LLM.

---

# 8. Memory Extraction

The current memory extractor uses regular-expression rules.

It looks for patterns such as:

```text
I prefer ...
I like ...
I love ...
I use ...
I want to use ...

I'm building ...
I am building ...
I'm developing ...
I am developing ...
I'm working on ...

I'm interested in ...
I enjoy ...
I'm learning ...

I want to learn ...
I want to build ...
I plan to ...
```

This makes the first version of the memory system deterministic and inexpensive.

The assistant response is not used by the current extraction logic; extraction is primarily performed from the user's message.

---

# 9. Importance and Confidence

Each memory receives:

- Importance
- Confidence

### Importance

Current rule-based values include approximately:

| Memory Type | Importance |
|---|---:|
| Personal | 0.9 |
| Preference | 0.8 |
| Project | 0.8 |
| Interest | 0.6 |
| General | 0.3 |

### Confidence

The system lowers confidence when uncertainty phrases are detected, such as:

```text
maybe
might
possibly
probably
perhaps
I think
I guess
not sure
could be
```

Otherwise the current default confidence is high.

---

# 10. Embedding System

The project uses:

```text
BAAI/bge-small-en-v1.5
```

through Sentence Transformers.

Embeddings are generated on:

```text
CPU
```

The embedding vector size used by the FAISS layer is:

```text
384 dimensions
```

Embeddings are normalized before storage/search.

The `.env` file is currently expected to contain:

```env
HF_TOKEN=your_huggingface_token
```

A Hugging Face token is used by the current embedding-loading implementation.

---

# 11. FAISS Semantic Search

FAISS is used for vector similarity search.

The current index is:

```text
IndexFlatIP
```

with:

```text
384 dimensions
```

Files:

```text
memory.index
faiss_mapping.pkl
```

The mapping maintains the relationship:

```text
FAISS vector position
        ↓
SQLite memory ID
```

This is important because FAISS stores vectors while SQLite stores the actual memory metadata/content.

---

# 12. Memory Ranking

Memory search does more than simply return the closest vector.

The system combines:

- semantic similarity
- importance
- confidence

The current ranking formula is:

```text
Final Score =
    0.70 × similarity
  + 0.20 × importance
  + 0.10 × confidence
```

This means semantic relevance is the strongest factor while important and reliable memories receive additional weight.

---

# 13. Memory Updating

When new information is learned, the `MemoryManager` searches existing memories.

The current update threshold is:

```text
0.75
```

Conceptually:

```text
New Memory
     │
     ▼
Search Existing Memories
     │
     ├── Similarity >= 0.75
     │        │
     │        ▼
     │      UPDATE
     │
     └── Similarity < 0.75
              │
              ▼
            CREATE
```

This helps avoid storing many semantically duplicated memories.

---

# 14. Conversation Learning

After the assistant responds, the application starts background processing.

The background workflow is:

```text
User Query
    +
Assistant Answer
       │
       ▼
Save Conversation
       │
       ▼
Extract Potential Memories
       │
       ▼
MemoryManager
       │
       ▼
Create / Update Memory
```

This work is submitted through a `ThreadPoolExecutor`, so the main chat response does not intentionally wait for the memory-learning operation to finish.

---

# 15. Context Injection

For every new user query:

1. Search the long-term memory.
2. Retrieve the top relevant memories.
3. Rank them.
4. Build a compact memory context.
5. Insert only relevant memory information into the Qwen prompt.
6. Generate the answer.

The model is instructed not to reveal the internal memory mechanism to the user.

Conceptually:

```text
Question
   │
   ▼
Memory Search
   │
   ▼
Relevant Memories
   │
   ▼
Prompt Context
   │
   ▼
Qwen3
   │
   ▼
Answer
```

---

# 16. Offline Safety System

The project includes a dedicated safety layer designed for an offline-first local AI workflow.

The important principle is:

> **The application checks Internet connectivity; it does not control the network adapter.**

It does not automatically:

- disable Wi-Fi
- enable Wi-Fi
- disconnect Ethernet
- change network adapter settings

The user is responsible for manually disconnecting the computer from the Internet.

---

# 17. Pre-Start Internet Check

When the user clicks:

```text
Start Server
```

the backend can first check Internet connectivity.

If Internet is detected, startup is blocked and the user receives a message similar to:

```text
Internet connection detected.
Disconnect Internet manually and try again.
```

This behavior is controlled by:

```text
offline_only
pre_start_check
```

---

# 18. Automatic Stop on Internet Detection

If Ollama is running in offline-only mode, a background monitoring thread periodically checks connectivity.

If Internet becomes available:

```text
Internet detected
       │
       ▼
Safety Controller
       │
       ▼
Stop Ollama
       │
       ▼
Record safety event
```

The default check interval is:

```text
1 second
```

The UI currently provides selectable intervals from:

```text
0.5 sec
1 sec
2 sec
3 sec
5 sec
10 sec
30 sec
60 sec
```

---

# 19. Ollama Process Management

`OllamaManager` is responsible for:

- detecting whether Ollama is running
- starting `ollama serve`
- finding an existing Ollama process
- identifying the process using port `11434`
- adopting an already-running Ollama server
- stopping Ollama
- returning server status

The default local Ollama API is:

```text
http://127.0.0.1:11434
```

---

# 20. Existing Ollama Server Detection

If Ollama is already running before the application starts, the controller attempts to find the process listening on:

```text
11434
```

It then verifies that the process is actually:

```text
ollama.exe
```

This allows the application to recognize an existing local Ollama server rather than blindly starting another server.

---

# 21. Frontend

The frontend is located at:

```text
frontend/
```

It uses:

- React
- TypeScript
- Vite
- Lucide React

The main UI includes:

### Chat

- Chat with the local AI.
- Send messages.
- Show user/AI responses.
- Disable chat while Ollama is stopped.
- Show a thinking/loading state.

### Server Control

- Start Server
- Stop Server
- Show Ollama PID
- Show server state

### Settings

AI settings:

- response length

Safety settings:

- offline-only mode
- pre-start Internet check
- automatic stop on Internet
- monitoring interval
- safety monitor status
- current safety mode
- last safety event

### History

The UI already contains a History section intended to display conversation history stored in SQLite.

The current frontend implementation presents this as a placeholder rather than loading the stored conversations.

---

# 22. Backend API

Base URL:

```text
http://127.0.0.1:8000
```

## Root

```http
GET /
```

Returns basic application status.

---

## Complete Status

```http
GET /api/status
```

Returns:

- Internet status
- Ollama status
- PID
- controller ownership
- safety settings
- monitoring state
- last safety event

---

## Network Status

```http
GET /api/network/status
```

Returns current Internet availability.

---

## Ollama Status

```http
GET /api/server/status
```

Returns:

- running state
- PID
- controller ownership
- monitoring state

---

## Start Ollama

```http
POST /api/server/start
```

Runs the safety checks and starts Ollama if permitted.

---

## Stop Ollama

```http
POST /api/server/stop
```

Stops Ollama and its safety monitor.

---

## Chat

```http
POST /api/chat
```

Example request:

```json
{
  "message": "What backend technology do I prefer?"
}
```

The endpoint:

1. Checks Ollama.
2. Searches memory.
3. Builds memory context.
4. Calls Qwen3.
5. Cleans the response.
6. Starts background conversation saving and memory learning.

---

## Safety Settings

```http
GET /api/settings
```

and:

```http
PUT /api/settings
```

Supported settings:

```text
offline_only
pre_start_check
auto_stop_on_internet
check_interval
```

---

## AI Settings

```http
GET /api/ai/settings
```

and:

```http
PUT /api/ai/settings
```

Supported settings include:

```text
num_predict
think
```

---

# 23. Project Structure

```text
local_ai/
│
├── backend/
│   ├── main.py
│   ├── network_guard.py
│   ├── ollama_manager.py
│   ├── safety_controller.py
│   ├── setting_store.py
│   └── settings.json
│
├── model/
│   ├── llm.py
│   └── memory_chat.py
│
├── memory/
│   ├── classifier.py
│   ├── context_builder.py
│   ├── conversation_store.py
│   ├── database.py
│   ├── embeddings.py
│   ├── embedding_store.py
│   ├── faiss_store.py
│   ├── memory_extractor.py
│   ├── memory_learning.py
│   ├── memory_manager.py
│   ├── memory_scoring.py
│   ├── memory_store.py
│   └── search.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── test_files/
│   ├── test_database.py
│   ├── test_embeddings.py
│   ├── test_faiss.py
│   ├── test_memory_chat.py
│   ├── test_memory_learning.py
│   ├── test_memory_manager.py
│   ├── test_memory_store.py
│   ├── test_search.py
│   ├── test_ranking.py
│   └── ...
│
├── memory.db
├── memory.index
├── faiss_mapping.pkl
└── .env
```

---

# 24. Installation

## Prerequisites

Recommended environment:

- Windows 10/11
- Python 3.11
- Node.js
- npm
- Ollama
- Git

A CPU-only system can run the architecture, although local LLM and embedding generation performance depends heavily on CPU speed and available RAM.

---

# 25. Install Ollama

Install Ollama for Windows and verify:

```powershell
ollama --version
```

Pull the configured model:

```powershell
ollama pull qwen3:4b
```

Verify the model:

```powershell
ollama list
```

The application expects:

```text
qwen3:4b
```

---

# 26. Python Environment

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Or use your existing Conda environment.

Example:

```powershell
conda create -n local_ai python=3.11
conda activate local_ai
```

---

# 27. Python Dependencies

The uploaded project does not currently contain a `requirements.txt`.

Install the required packages manually or create a requirements file containing the project's backend dependencies.

Typical dependencies for this implementation are:

```text
fastapi
uvicorn
pydantic
requests
python-dotenv
numpy
faiss-cpu
sentence-transformers
```

Example:

```powershell
pip install fastapi uvicorn pydantic requests python-dotenv numpy faiss-cpu sentence-transformers
```

Depending on the installed versions of Sentence Transformers and Hugging Face libraries, additional compatible dependencies may be installed automatically.

---

# 28. Environment Variables

Create:

```text
.env
```

in the project root.

Current embedding implementation expects:

```env
HF_TOKEN=your_huggingface_token
```

Do **not** commit real API/access tokens to Git.

The `.env` file should remain ignored by Git.

---

# 29. Start the Backend

From the project root:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The API should become available at:

```text
http://127.0.0.1:8000
```

The FastAPI documentation should be available at:

```text
http://127.0.0.1:8000/docs
```

---

# 30. Start the Frontend

Open another terminal.

Go to:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start Vite:

```powershell
npm run dev
```

Vite will display the local development URL in the terminal.

Open that URL in your browser.

---

# 31. Recommended Startup Order

For a clean first run:

### Step 1

Make sure Internet is disconnected manually if offline-only mode is enabled.

### Step 2

Start the FastAPI backend:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 3

Start the frontend:

```powershell
cd frontend
npm run dev
```

### Step 4

Open the frontend.

### Step 5

Click:

```text
Start Server
```

The backend checks Internet connectivity first.

### Step 6

If the computer is offline, Ollama starts.

### Step 7

Start chatting with the local AI.

---

# 32. Example Memory Flow

Suppose the user says:

```text
I prefer Python and FastAPI for backend development.
```

The system can conceptually process it as:

```text
User message
      ↓
Memory extraction
      ↓
Preference
      ↓
Importance ≈ 0.8
      ↓
Confidence ≈ 0.9
      ↓
BGE embedding
      ↓
SQLite
      +
FAISS
```

Later:

```text
What backend technology do I prefer?
```

The semantic search can retrieve the earlier memory.

The retrieved memory is inserted into the Qwen prompt, allowing the assistant to answer based on the stored preference.

---

# 33. Testing

The project contains multiple test scripts covering the memory architecture.

Examples:

```powershell
python test_files/test_database.py
```

```powershell
python test_files/test_embeddings.py
```

```powershell
python test_files/test_faiss.py
```

```powershell
python test_files/test_search.py
```

```powershell
python test_files/test_ranking.py
```

```powershell
python test_files/test_memory_manager.py
```

```powershell
python test_files/test_memory_learning.py
```

```powershell
python test_files/test_memory_chat.py
```

The test files cover:

- database creation
- memory creation
- memory retrieval
- memory update
- memory deletion
- history tracking
- embedding generation
- embedding storage
- FAISS creation
- FAISS search
- semantic ranking
- filtering
- memory classification
- memory scoring
- conversation learning
- LLM calls
- end-to-end memory chat behavior

---

# 34. Important Design Decisions

## Local-first

The primary language-model generation happens locally through Ollama.

## CPU-friendly architecture

The embedding model is explicitly configured to use CPU.

## Semantic memory

Memory retrieval is based on embeddings rather than only keyword matching.

## Deterministic memory extraction

The current memory extractor uses rules instead of another LLM, reducing additional local model requirements.

## Persistent storage

SQLite provides persistent structured storage.

## Vector search

FAISS provides efficient semantic retrieval.

## Memory history

Changes to memories can be preserved through version history.

## Safety-first server control

The application can prevent Ollama from starting when Internet connectivity is detected and can stop Ollama if connectivity appears later.

---

# 35. Current Limitations

This is an actively developed project and several areas can be improved.

### 1. No Python requirements file

The repository currently does not include a `requirements.txt`.

A future version should add one with pinned versions.

### 2. History UI is not fully connected

Conversation data is stored in SQLite, but the frontend History screen currently acts as a placeholder.

A future version can add:

- history API
- conversation list
- conversation search
- conversation reopening
- delete conversation
- date grouping

### 3. Memory management UI is not implemented

The backend already supports memory operations, but the frontend could expose:

- view memories
- search memories
- edit memories
- delete memories
- importance
- confidence
- memory type
- memory history

### 4. Windows-specific process control

The current Ollama process manager uses Windows commands such as:

```text
PowerShell
Get-NetTCPConnection
Get-Process
taskkill
```

Linux/macOS support would require a different process-management layer.

### 5. Internet detection is endpoint-based

Connectivity is tested against external endpoints. This means network availability detection depends on those endpoints being reachable.

### 6. Rule-based memory extraction

The current extractor handles predefined sentence patterns. More natural language variations may not be detected.

### 7. English-focused embedding model

The current embedding model is:

```text
BAAI/bge-small-en-v1.5
```

For multilingual Telugu/English conversations, a multilingual embedding model could be evaluated in a future version.

### 8. No authentication

The FastAPI backend is intended for local use and does not currently implement authentication.

### 9. CORS is permissive

The current backend uses:

```text
allow_origins=["*"]
```

This is convenient during development but should be restricted for a production deployment.

---

# 36. Security Notes

Before making this application accessible beyond the local machine:

- restrict CORS
- add authentication
- protect the API
- validate user input
- avoid exposing Ollama unnecessarily
- keep `.env` out of Git
- do not commit Hugging Face tokens
- review subprocess permissions
- add structured logging
- add API rate limits if externally exposed
- use HTTPS if remote access is ever introduced

This project is currently best treated as a **local personal AI application**, not an Internet-facing production service.

---

# 37. Data and Privacy

The intended architecture keeps important chatbot data on the local computer:

```text
User message
      ↓
FastAPI
      ↓
Memory system
      ↓
SQLite
      +
FAISS
```

The local model is accessed through:

```text
Ollama
```

The project does not require a cloud LLM API for normal Qwen chat generation.

However, the current embedding implementation loads the Hugging Face model through the Sentence Transformers ecosystem and uses a Hugging Face token. Model acquisition may therefore require Internet access during initial setup.

Once the required model files are available locally, the runtime architecture can be operated offline.

---

# 38. ChatGPT Assistance / Development Note

This project was developed with **ChatGPT used as an AI development assistant**.

ChatGPT was used during development for activities such as:

- understanding architecture
- discussing implementation approaches
- debugging Python issues
- designing the memory pipeline
- improving code structure
- explaining libraries and concepts
- generating and refining code
- troubleshooting Ollama integration
- designing the frontend/backend interaction
- documenting the project

The implementation, testing, configuration, and final integration were performed as part of the project development process.

> **Development assistance disclosure:** ChatGPT was used as an assistant during the development of this project. It should be considered a development aid, not the sole author of the system.

---

# 39. Future Roadmap

Potential next development stages:

## Phase 1 — Current Foundation

- Local Qwen chatbot
- Ollama control
- SQLite memory
- BGE embeddings
- FAISS retrieval
- memory classification
- memory scoring
- conversation storage
- offline safety controller
- React control center

## Phase 2 — Memory Management

- Memory dashboard
- Memory search
- Memory editing
- Memory deletion
- Memory history viewer
- Memory statistics

## Phase 3 — Conversation History

- Real history API
- Search conversations
- Open previous conversations
- Conversation titles
- Delete conversations
- Conversation export

## Phase 4 — Better Memory Intelligence

- multilingual embeddings
- improved memory extraction
- contradiction detection
- memory expiration
- temporal memories
- confidence decay
- duplicate memory merging

## Phase 5 — Local Agent System

Potential future agent capabilities:

```text
Local Chat
     │
     ├── Memory Agent
     ├── File Agent
     ├── System Agent
     ├── Automation Agent
     └── Tool Agent
```

The safety controller could remain the central gatekeeper for local model execution.

---

# 40. Development Philosophy

The project follows several principles:

### Local-first

Prefer local computation whenever practical.

### User-controlled networking

The application checks connectivity but does not take control of the user's network adapter.

### Persistent memory

The assistant should improve its usefulness through relevant long-term context.

### Modular architecture

LLM, memory, vector search, safety, process management, API, and UI are separated into different modules.

### Explainable memory

Memories have explicit types, importance, confidence, and history rather than being stored as opaque vector data only.

### Safety before execution

The local model server should pass the configured safety checks before being started.

---

# 41. License

No explicit license is currently included in the uploaded project.

If this repository will be published publicly, add an appropriate license such as MIT, Apache-2.0, or another license matching the intended use.

---

# 42. Summary

Local AI Control Center is a local personal AI platform combining:

```text
                 Local AI Control Center
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
   Local LLM          Long-Term Memory     Safety Layer
   Qwen3 + Ollama     SQLite + FAISS       Internet Guard
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                     FastAPI Backend
                           │
                           ▼
                    React Control UI
```

The central goal is to create a **personal local AI assistant with persistent memory and controlled offline execution**, rather than simply building a basic chatbot interface.

---

## Author / Developer

**Chandika Purna Revanth**

Project focus:

- Local AI
- LLMs
- Long-term memory
- Semantic search
- FAISS
- Ollama
- FastAPI
- React
- AI safety/control systems

---

**Status:** Active development
