import threading
import time

from backend.network_guard import NetworkGuard
from backend.ollama_manager import OllamaManager


class SafetyController:

    def __init__(
        self,
        check_interval=1,
        offline_only=True,
        pre_start_check=True,
        auto_stop_on_internet=True
    ):
        self.network = NetworkGuard()
        self.ollama = OllamaManager()

        # Safety settings
        self.check_interval = check_interval
        self.offline_only = offline_only
        self.pre_start_check = pre_start_check
        self.auto_stop_on_internet = auto_stop_on_internet

        # Monitoring state
        self.monitor_thread = None
        self.monitoring = False

        # Status information
        self.last_internet_status = None
        self.last_event = None

        # Thread safety
        self.lock = threading.Lock()

    # =========================================================
    # START OLLAMA
    # =========================================================

    def start_ollama(self):

        with self.lock:

            # -------------------------------------------------
            # Pre-start Internet check
            # -------------------------------------------------
            if self.offline_only and self.pre_start_check:

                internet = self.network.is_internet_available()

                self.last_internet_status = internet

                if internet:

                    self.last_event = "START_BLOCKED_INTERNET"

                    return {
                        "success": False,
                        "blocked": True,
                        "message": (
                            "Internet connection detected. "
                            "Disconnect Internet manually and try again."
                        )
                    }

            # -------------------------------------------------
            # Start Ollama
            # -------------------------------------------------

            result = self.ollama.start()

            if result.get("success"):

                self.last_event = "OLLAMA_STARTED"

                # Start safety monitoring if required
                if (
                    self.offline_only
                    and self.auto_stop_on_internet
                ):
                    self.start_monitor()

            return result

    # =========================================================
    # STOP OLLAMA
    # =========================================================

    def stop_ollama(self):

        self.stop_monitor()

        with self.lock:

            result = self.ollama.stop()

            if result.get("success"):

                self.last_event = "OLLAMA_STOPPED"

            return result

    # =========================================================
    # START MONITOR
    # =========================================================

    def start_monitor(self):

        if self.monitoring:
            return

        self.monitoring = True

        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )

        self.monitor_thread.start()

    # =========================================================
    # STOP MONITOR
    # =========================================================

    def stop_monitor(self):

        self.monitoring = False

    # =========================================================
    # MONITOR LOOP
    # =========================================================

    def _monitor_loop(self):

        while self.monitoring:

            time.sleep(self.check_interval)

            # Ollama already stopped
            if not self.ollama.is_running():

                self.monitoring = False
                break

            # Check Internet
            internet = self.network.is_internet_available()

            self.last_internet_status = internet

            # -------------------------------------------------
            # Internet detected
            # -------------------------------------------------

            if (
                internet
                and self.offline_only
                and self.auto_stop_on_internet
            ):

                self.last_event = "INTERNET_DETECTED_STOPPING"

                print(
                    "Internet detected. "
                    "Stopping Ollama..."
                )

                result = self.ollama.stop()

                if result.get("success"):

                    self.last_event = "OLLAMA_AUTO_STOPPED"

                self.monitoring = False

                break

    # =========================================================
    # UPDATE SETTINGS
    # =========================================================

    def update_settings(
        self,
        offline_only=None,
        pre_start_check=None,
        auto_stop_on_internet=None,
        check_interval=None
    ):

        with self.lock:

            if offline_only is not None:
                self.offline_only = offline_only

            if pre_start_check is not None:
                self.pre_start_check = pre_start_check

            if auto_stop_on_internet is not None:
                self.auto_stop_on_internet = auto_stop_on_internet

            if check_interval is not None:

                # Keep the interval within a safe range
                self.check_interval = max(
                    0.5,
                    min(float(check_interval), 60)
                )

            # -------------------------------------------------
            # Adjust monitoring according to new settings
            # -------------------------------------------------

            if self.ollama.is_running():

                if (
                    self.offline_only
                    and self.auto_stop_on_internet
                ):

                    self.start_monitor()

                else:

                    self.stop_monitor()

            self.last_event = "SETTINGS_UPDATED"

            return self.settings()

    # =========================================================
    # GET SETTINGS
    # =========================================================

    def settings(self):

        return {
            "offline_only": self.offline_only,
            "pre_start_check": self.pre_start_check,
            "auto_stop_on_internet": self.auto_stop_on_internet,
            "check_interval": self.check_interval
        }

    # =========================================================
    # COMPLETE STATUS
    # =========================================================

    def status(self):

        internet = self.network.is_internet_available()

        return {
            "internet": {
                "available": internet
            },

            "ollama": {
                "running": self.ollama.is_running(),
                "pid": self.ollama.pid,
                "owned_by_controller":
                    self.ollama.process is not None
            },

            "safety": {
                "offline_only":
                    self.offline_only,

                "pre_start_check":
                    self.pre_start_check,

                "auto_stop_on_internet":
                    self.auto_stop_on_internet,

                "check_interval":
                    self.check_interval,

                "monitoring":
                    self.monitoring
            },

            "last_event":
                self.last_event
        }