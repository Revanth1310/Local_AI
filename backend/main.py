from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.safety_controller import SafetyController
from model.memory_chat import MemoryChat
from backend.setting_store import load_settings

app = FastAPI(
    title="Local AI Control Center",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# CONTROLLERS
# =========================================================

saved_settings = load_settings()

controller = SafetyController(
    check_interval=saved_settings["check_interval"],
    offline_only=saved_settings["offline_only"],
    pre_start_check=saved_settings["pre_start_check"],
    auto_stop_on_internet=saved_settings[
        "auto_stop_on_internet"
    ]
)

memory_chat = MemoryChat()


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "name": "Local AI Control Center",
        "status": "running"
    }


# =========================================================
# COMPLETE STATUS
# =========================================================

@app.get("/api/status")
def status():

    return controller.status()


# =========================================================
# NETWORK STATUS
# =========================================================

@app.get("/api/network/status")
def network_status():

    return {
        "internet_available":
            controller.network.is_internet_available()
    }


# =========================================================
# SERVER STATUS
# =========================================================

@app.get("/api/server/status")
def server_status():

    return {
        "running":
            controller.ollama.is_running(),

        "pid":
            controller.ollama.pid,

        "owned_by_controller":
            controller.ollama.process is not None,

        "monitoring":
            controller.monitoring
    }


# =========================================================
# SETTINGS
# =========================================================

class SettingsUpdate(BaseModel):

    offline_only: bool | None = None

    pre_start_check: bool | None = None

    auto_stop_on_internet: bool | None = None

    check_interval: float | None = Field(
        default=None,
        ge=0.5,
        le=60
    )


@app.get("/api/settings")
def get_settings():

    return controller.settings()


@app.put("/api/settings")
def update_settings(settings: SettingsUpdate):

    updated = controller.update_settings(
        offline_only=settings.offline_only,
        pre_start_check=settings.pre_start_check,
        auto_stop_on_internet=settings.auto_stop_on_internet,
        check_interval=settings.check_interval
    )

    from backend.setting_store import save_settings

    save_settings(updated)

    return updated
# =========================================================
# START SERVER
# =========================================================

@app.post("/api/server/start")
def start_server():

    return controller.start_ollama()


# =========================================================
# STOP SERVER
# =========================================================

@app.post("/api/server/stop")
def stop_server():

    return controller.stop_ollama()


# =========================================================
# CHAT
# =========================================================

class ChatRequest(BaseModel):

    message: str


@app.post("/api/chat")
def chat(request: ChatRequest):

    # Safety check
    if not controller.ollama.is_running():

        return {
            "success": False,
            "message": "Ollama is not running."
        }

    result = memory_chat.chat(
        request.message
    )

    return {
        "success": True,
        "data": result
    }
class AISettingsUpdate(BaseModel):

    num_predict: int = Field(
        ge=64,
        le=4096
    )

    think: bool | None = None
@app.get("/api/ai/settings")
def get_ai_settings():

    return {
        "num_predict":
            memory_chat.get_num_predict(),

        "think":
            memory_chat.get_think()
    }


@app.put("/api/ai/settings")
def update_ai_settings(
    settings: AISettingsUpdate
):

    num_predict = (
        memory_chat.set_num_predict(
            settings.num_predict
        )
    )

    think = memory_chat.get_think()

    if settings.think is not None:

        think = memory_chat.set_think(
            settings.think
        )

    return {
        "success": True,

        "num_predict":
            num_predict,

        "think":
            think
    }