import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Bot,
  MessageSquare,
  History,
  Settings,
  Play,
  Square,
  Send,
  Wifi,
  WifiOff,
  Cpu,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";

import "./App.css";

const API = "http://127.0.0.1:8000";

// =========================================================
// TYPES
// =========================================================

type Status = {
  internet: {
    available: boolean;
  };

  ollama: {
    running: boolean;
    pid: number | null;
    owned_by_controller: boolean;
  };

  safety: {
    offline_only: boolean;
    pre_start_check: boolean;
    auto_stop_on_internet: boolean;
    check_interval: number;
    monitoring: boolean;
  };

  last_event: string | null;
};

type Message = {
  role: "user" | "assistant";
  content: string;
};

type SettingsUpdate = {
  offline_only?: boolean;
  pre_start_check?: boolean;
  auto_stop_on_internet?: boolean;
  check_interval?: number;
};

type AISettings = {
  num_predict: number;
};

// =========================================================
// APP
// =========================================================

function App() {

  // =======================================================
  // STATE
  // =======================================================

  const [status, setStatus] =
    useState<Status | null>(null);

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [message, setMessage] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [activeTab, setActiveTab] =
    useState("chat");

  const [settingsLoading, setSettingsLoading] =
    useState(false);

  // AI settings
  const [aiSettings, setAISettings] =
    useState<AISettings | null>(null);

  const [aiSettingsLoading, setAISettingsLoading] =
    useState(false);

  // Server operation state
  const [serverLoading, setServerLoading] =
    useState(false);

  // Tells the UI which server operation is running
  const [serverAction, setServerAction] =
    useState<"starting" | "stopping" | null>(
      null
    );

  // Used to prevent background polling from
  // overwriting status during Start/Stop.
  const serverBusyRef =
    useRef(false);

  // =======================================================
  // LOAD STATUS
  // =======================================================

  const loadStatus = async (
    force = false
  ) => {

    // Do not allow background polling to
    // overwrite the state during Start/Stop.
    if (
      serverBusyRef.current &&
      !force
    ) {
      return;
    }

    try {

      const response = await fetch(
        `${API}/api/status`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          "Status request failed"
        );
      }

      const data: Status =
        await response.json();

      setStatus(data);

    } catch {

      // Don't destroy the current UI state
      // while a server operation is running.
      if (!serverBusyRef.current) {
        setStatus(null);
      }

    }
  };

  // =======================================================
  // LOAD AI SETTINGS
  // =======================================================

  const loadAISettings = async () => {

    try {

      const response = await fetch(
        `${API}/api/ai/settings`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          "AI settings request failed"
        );
      }

      const data: AISettings =
        await response.json();

      setAISettings(data);

    } catch (error) {

      console.error(
        "Failed to load AI settings:",
        error
      );

    }
  };

  // =======================================================
  // STATUS POLLING
  // =======================================================

  useEffect(() => {

    loadStatus(true);

    loadAISettings();

    const interval = setInterval(
      () => {
        loadStatus();
      },
      1000
    );

    return () => {
      clearInterval(interval);
    };

  }, []);

  // =======================================================
  // START SERVER
  // =======================================================

  const startServer = async () => {

    // Already processing
    if (serverBusyRef.current) {
      return;
    }

    serverBusyRef.current = true;

    setServerLoading(true);

    setServerAction("starting");

    try {

      const response = await fetch(
        `${API}/api/server/start`,
        {
          method: "POST",
          cache: "no-store",
        }
      );

      const data =
        await response.json();

      // Backend blocked the start
      if (!data.success) {

        alert(
          data.message ||
          "Ollama could not be started."
        );

        return;
      }

      // Server successfully started.
      // Get the final status while the
      // polling lock is still active.
      await loadStatus(true);

    } catch (error) {

      console.error(
        "Start server error:",
        error
      );

      alert(
        "Cannot connect to Local AI backend."
      );

    } finally {

      // Release operation lock
      serverBusyRef.current = false;

      setServerLoading(false);

      setServerAction(null);

      // One final status refresh
      await loadStatus(true);
    }
  };

  // =======================================================
  // STOP SERVER
  // =======================================================

  const stopServer = async () => {

    // Already processing
    if (serverBusyRef.current) {
      return;
    }

    serverBusyRef.current = true;

    setServerLoading(true);

    setServerAction("stopping");

    try {

      const response = await fetch(
        `${API}/api/server/stop`,
        {
          method: "POST",
          cache: "no-store",
        }
      );

      const data =
        await response.json();

      if (!data.success) {

        alert(
          data.message ||
          "Ollama could not be stopped."
        );

        return;
      }

      // Get final stopped state
      await loadStatus(true);

    } catch (error) {

      console.error(
        "Stop server error:",
        error
      );

      alert(
        "Cannot connect to Local AI backend."
      );

    } finally {

      serverBusyRef.current = false;

      setServerLoading(false);

      setServerAction(null);

      await loadStatus(true);
    }
  };

  // =======================================================
  // UPDATE SAFETY SETTINGS
  // =======================================================

  const updateSettings = async (
    changes: SettingsUpdate
  ) => {

    if (!status) {
      return;
    }

    if (settingsLoading) {
      return;
    }

    setSettingsLoading(true);

    try {

      const response = await fetch(
        `${API}/api/settings`,
        {
          method: "PUT",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify(changes),
        }
      );

      if (!response.ok) {

        const errorText =
          await response.text();

        throw new Error(errorText);
      }

      const updatedSettings =
        await response.json();

      setStatus((previous) => {

        if (!previous) {
          return previous;
        }

        return {

          ...previous,

          safety: {

            ...previous.safety,

            offline_only:
              updatedSettings
                .offline_only,

            pre_start_check:
              updatedSettings
                .pre_start_check,

            auto_stop_on_internet:
              updatedSettings
                .auto_stop_on_internet,

            check_interval:
              updatedSettings
                .check_interval,
          },

        };
      });

    } catch (error) {

      console.error(
        "Settings update failed:",
        error
      );

      alert(
        "Could not update safety settings."
      );

    } finally {

      setSettingsLoading(false);
    }
  };

  // =======================================================
  // UPDATE AI SETTINGS
  // =======================================================

  const updateAISettings = async (
    num_predict: number
  ) => {

    if (aiSettingsLoading) {
      return;
    }

    setAISettingsLoading(true);

    try {

      const response = await fetch(
        `${API}/api/ai/settings`,
        {
          method: "PUT",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            num_predict,
          }),
        }
      );

      if (!response.ok) {

        const errorText =
          await response.text();

        throw new Error(errorText);
      }

      const data =
        await response.json();

      setAISettings({
        num_predict:
          data.num_predict,
      });

    } catch (error) {

      console.error(
        "AI settings update failed:",
        error
      );

      alert(
        "Could not update AI response length."
      );

    } finally {

      setAISettingsLoading(false);
    }
  };

  // =======================================================
  // SEND CHAT MESSAGE
  // =======================================================

  const sendMessage = async () => {

    const text =
      message.trim();

    if (!text || loading) {
      return;
    }

    if (!status?.ollama.running) {

      alert(
        "Ollama is not running."
      );

      return;
    }

    setMessages((previous) => [

      ...previous,

      {
        role: "user",
        content: text,
      },

    ]);

    setMessage("");

    setLoading(true);

    try {

      const response = await fetch(
        `${API}/api/chat`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            message: text,
          }),
        }
      );

      const data =
        await response.json();

      if (data.success) {

        setMessages((previous) => [

          ...previous,

          {
            role: "assistant",
            content:
              data.data.answer,
          },

        ]);

      } else {

        alert(data.message);
      }

    } catch {

      alert(
        "Cannot connect to Local AI backend."
      );

    } finally {

      setLoading(false);

      await loadStatus();
    }
  };

  // =======================================================
  // ENTER KEY
  // =======================================================

  const handleKeyDown = (
    event:
      React.KeyboardEvent<HTMLTextAreaElement>
  ) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      sendMessage();
    }
  };

  // =======================================================
  // RENDER
  // =======================================================

  return (

    <div className="app">

      {/* ==================================================
          HEADER
      ================================================== */}

      <header className="header">

        <div className="brand">

          <div className="brand-icon">
            <Bot size={19} />
          </div>

          <div>

            <div className="brand-title">
              Local AI
            </div>

            <div className="brand-subtitle">
              Control Center
            </div>

          </div>

        </div>

        <button
          type="button"
          className="settings-button"
          onClick={() =>
            setActiveTab("settings")
          }
          title="Settings"
        >
          <Settings size={18} />
        </button>

      </header>


      {/* ==================================================
          STATUS
      ================================================== */}

      <section className="status-panel">

        <div className="status-item">

          {status?.internet.available ? (
            <Wifi size={17} />
          ) : (
            <WifiOff size={17} />
          )}

          <div>

            <span className="status-label">
              Internet
            </span>

            <span
              className={
                status?.internet.available
                  ? "status-value online"
                  : "status-value offline"
              }
            >
              {status?.internet.available
                ? "Online"
                : "Offline"}
            </span>

          </div>

        </div>


        <div className="status-item">

          <Cpu size={17} />

          <div>

            <span className="status-label">
              Ollama
            </span>

            <span
              className={
                status?.ollama.running
                  ? "status-value online"
                  : "status-value offline"
              }
            >
              {status?.ollama.running
                ? "Running"
                : "Stopped"}
            </span>

          </div>

        </div>

      </section>


      {/* ==================================================
          SERVER CONTROLS
      ================================================== */}

      <section className="server-controls">

        {/* STARTING */}

        {serverLoading &&
        serverAction === "starting" ? (

          <button
            type="button"
            className="server-button start"
            disabled
          >

            <Play size={16} />

            Starting...

          </button>


        ) : serverLoading &&
          serverAction === "stopping" ? (

          /* STOPPING */

          <button
            type="button"
            className="server-button stop"
            disabled
          >

            <Square size={15} />

            Stopping...

          </button>


        ) : !status?.ollama.running ? (

          /* START */

          <button
            type="button"
            className="server-button start"
            onClick={startServer}
          >

            <Play size={16} />

            Start Server

          </button>


        ) : (

          /* STOP */

          <button
            type="button"
            className="server-button stop"
            onClick={stopServer}
          >

            <Square size={15} />

            Stop Server

          </button>

        )}


        {/* PID */}

        {status?.ollama.running && (

          <div className="pid">
            PID {status.ollama.pid}
          </div>

        )}

      </section>


      {/* ==================================================
          MAIN CONTENT
      ================================================== */}

      <main className="content">


        {/* =================================================
            CHAT
        ================================================= */}

        {activeTab === "chat" && (

          <section className="chat-section">

            <div className="section-title">

              <MessageSquare size={17} />

              Chat

            </div>


            <div className="messages">

              {messages.length === 0 && (

                <div className="empty-chat">

                  <Bot size={32} />

                  <p>
                    Your local AI assistant
                  </p>

                  <span>
                    Start Ollama to begin
                    chatting.
                  </span>

                </div>

              )}


              {messages.map(
                (item, index) => (

                  <div
                    key={index}
                    className={
                      `message ${item.role}`
                    }
                  >

                    <div className="message-role">

                      {item.role === "user"
                        ? "You"
                        : "AI"}

                    </div>

                    <div className="message-content">

                      {item.content}

                    </div>

                  </div>

                )
              )}


              {loading && (

                <div className="message assistant">

                  <div className="message-role">
                    AI
                  </div>

                  <div className="typing">
                    Thinking...
                  </div>

                </div>

              )}

            </div>


            <div className="input-area">

              <textarea
                value={message}

                onChange={(event) =>
                  setMessage(
                    event.target.value
                  )
                }

                onKeyDown={handleKeyDown}

                placeholder="Ask your local AI..."

                disabled={
                  !status?.ollama.running ||
                  loading
                }
              />


              <button
                type="button"
                className="send-button"

                onClick={sendMessage}

                disabled={
                  !message.trim() ||
                  !status?.ollama.running ||
                  loading
                }
              >

                <Send size={17} />

              </button>

            </div>

          </section>

        )}


        {/* =================================================
            HISTORY
        ================================================= */}

        {activeTab === "history" && (

          <section className="placeholder">

            <History size={30} />

            <h3>
              Conversation History
            </h3>

            <p>
              Your existing SQLite
              conversation history
              will appear here.
            </p>

          </section>

        )}


        {/* =================================================
            SETTINGS
        ================================================= */}

        {activeTab === "settings" && (

          <section className="settings-section">


            {/* =================================================
                AI SETTINGS
            ================================================= */}

            <div className="section-title">

              <Bot size={17} />

              AI Settings

            </div>


            <div className="settings-content">

              <div className="settings-description">

                Configure how much detail the
                local AI generates in its
                responses.

                <br />

                Longer responses may take more
                time on CPU.

              </div>


              {/* RESPONSE LENGTH */}

              <div className="setting-card">

                <div>

                  <div className="setting-title">
                    Response length
                  </div>

                  <div className="setting-description">

                    Controls the maximum amount
                    of text the AI can generate.

                  </div>

                </div>


                <select
                  className="interval-select"

                  value={
                    aiSettings?.num_predict ??
                    512
                  }

                  disabled={
                    aiSettingsLoading
                  }

                  onChange={(event) =>
                    updateAISettings(
                      Number(
                        event.target.value
                      )
                    )
                  }
                >

                  <option value="256">
                    Short
                  </option>

                  <option value="512">
                    Normal
                  </option>

                  <option value="1024">
                    Detailed
                  </option>

                  <option value="2048">
                    Very Detailed
                  </option>

                </select>

              </div>

            </div>


            {/* =================================================
                SAFETY SETTINGS
            ================================================= */}

            <div className="section-title">

              <Settings size={17} />

              Safety Settings

            </div>


            <div className="settings-content">

              <div className="settings-description">

                These controls configure how
                Local AI reacts to Internet
                connectivity.

                <br />

                They <strong>
                  do not control your Wi-Fi,
                  Ethernet, or network adapter.
                </strong>

              </div>


              {/* OFFLINE ONLY */}

              <div className="setting-card">

                <div>

                  <div className="setting-title">
                    Offline-only mode
                  </div>

                  <div className="setting-description">

                    Ollama is intended to run
                    only when Internet
                    connectivity is unavailable.

                  </div>

                </div>


                <button
                  type="button"

                  className={
                    status?.safety.offline_only
                      ? "toggle on"
                      : "toggle"
                  }

                  onClick={() =>
                    updateSettings({
                      offline_only:
                        !status?.safety
                          .offline_only,
                    })
                  }

                  disabled={settingsLoading}

                  title={
                    status?.safety.offline_only
                      ? "Disable"
                      : "Enable"
                  }
                >

                  <div className="toggle-dot" />

                </button>

              </div>


              {/* PRE START */}

              <div className="setting-card">

                <div>

                  <div className="setting-title">
                    Pre-start Internet check
                  </div>

                  <div className="setting-description">

                    Check Internet before
                    starting Ollama.

                  </div>

                </div>


                <button
                  type="button"

                  className={
                    status?.safety.pre_start_check
                      ? "toggle on"
                      : "toggle"
                  }

                  onClick={() =>
                    updateSettings({
                      pre_start_check:
                        !status?.safety
                          .pre_start_check,
                    })
                  }

                  disabled={settingsLoading}

                  title={
                    status?.safety.pre_start_check
                      ? "Disable"
                      : "Enable"
                  }
                >

                  <div className="toggle-dot" />

                </button>

              </div>


              {/* AUTO STOP */}

              <div className="setting-card">

                <div>

                  <div className="setting-title">
                    Auto-stop on Internet
                  </div>

                  <div className="setting-description">

                    Automatically stop Ollama
                    when Internet connectivity
                    is detected.

                  </div>

                </div>


                <button
                  type="button"

                  className={
                    status?.safety
                      .auto_stop_on_internet
                      ? "toggle on"
                      : "toggle"
                  }

                  onClick={() =>
                    updateSettings({
                      auto_stop_on_internet:
                        !status?.safety
                          .auto_stop_on_internet,
                    })
                  }

                  disabled={settingsLoading}

                  title={
                    status?.safety
                      .auto_stop_on_internet
                      ? "Disable"
                      : "Enable"
                  }
                >

                  <div className="toggle-dot" />

                </button>

              </div>


              {/* CHECK INTERVAL */}

              <div className="setting-card">

                <div>

                  <div className="setting-title">
                    Check interval
                  </div>

                  <div className="setting-description">

                    How often the safety
                    monitor checks Internet
                    connectivity.

                  </div>

                </div>


                <select
                  className="interval-select"

                  value={
                    status?.safety
                      .check_interval ?? 1
                  }

                  disabled={settingsLoading}

                  onChange={(event) =>
                    updateSettings({
                      check_interval:
                        Number(
                          event.target.value
                        ),
                    })
                  }
                >

                  <option value="0.5">
                    0.5 sec
                  </option>

                  <option value="1">
                    1 sec
                  </option>

                  <option value="2">
                    2 sec
                  </option>

                  <option value="3">
                    3 sec
                  </option>

                  <option value="5">
                    5 sec
                  </option>

                  <option value="10">
                    10 sec
                  </option>

                  <option value="30">
                    30 sec
                  </option>

                  <option value="60">
                    60 sec
                  </option>

                </select>

              </div>


              {/* MONITOR */}

              <div className="setting-card">

                <div>

                  <div className="setting-title">
                    Safety monitor
                  </div>

                  <div className="setting-description">

                    Background Internet
                    monitoring while Ollama
                    is running.

                  </div>

                </div>


                <div
                  className={
                    status?.safety.monitoring
                      ? "monitor-status active"
                      : "monitor-status"
                  }
                >

                  {status?.safety.monitoring
                    ? "Active"
                    : "Inactive"}

                </div>

              </div>


              {/* CURRENT MODE */}

              <div className="setting-card">

                <div>

                  <div className="setting-title">
                    Current safety mode
                  </div>

                  <div className="setting-description">

                    Current protection state.

                  </div>

                </div>


                <div className="monitor-status active">

                  {status?.safety.offline_only
                    ? "Offline-only"
                    : "Normal"}

                </div>

              </div>


              {/* EVENT */}

              <div className="event-card">

                <div className="event-title">

                  <ShieldCheck size={15} />

                  Last safety event

                </div>


                <div className="event-value">

                  {status?.last_event ??
                    "No events yet"}

                </div>

              </div>


              {/* REFRESH */}

              <button
                type="button"
                className="refresh-settings"

                onClick={() =>
                  loadStatus(true)
                }

                disabled={
                  settingsLoading
                }
              >

                <RefreshCw size={15} />

                Refresh Status

              </button>

            </div>

          </section>

        )}

      </main>


      {/* ==================================================
          BOTTOM NAV
      ================================================== */}

      <nav className="bottom-nav">

        <button
          type="button"

          className={
            activeTab === "chat"
              ? "nav-item active"
              : "nav-item"
          }

          onClick={() =>
            setActiveTab("chat")
          }
        >

          <MessageSquare size={17} />

          <span>Chat</span>

        </button>


        <button
          type="button"

          className={
            activeTab === "history"
              ? "nav-item active"
              : "nav-item"
          }

          onClick={() =>
            setActiveTab("history")
          }
        >

          <History size={17} />

          <span>History</span>

        </button>


        <button
          type="button"

          className={
            activeTab === "settings"
              ? "nav-item active"
              : "nav-item"
          }

          onClick={() =>
            setActiveTab("settings")
          }
        >

          <Settings size={17} />

          <span>Settings</span>

        </button>

      </nav>

    </div>
  );
}

export default App;