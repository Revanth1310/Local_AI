import os
import subprocess
import time
import requests


OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_API = f"{OLLAMA_URL}/api/tags"


class OllamaManager:

    def __init__(self):

        self.process = None
        self.pid = None

    # =====================================================
    # CHECK API
    # =====================================================

    def is_running(self):

        try:

            response = requests.get(
                OLLAMA_API,
                timeout=2
            )

            return response.status_code == 200

        except requests.RequestException:

            return False

    # =====================================================
    # FIND EXISTING OLLAMA SERVE PROCESS
    # =====================================================

    def find_server_pid(self):

        try:

            # Ollama API listens on port 11434.
            # Find the Windows process that owns that port.
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        "Get-NetTCPConnection "
                        "-LocalPort 11434 "
                        "-State Listen "
                        "| Select-Object -ExpandProperty OwningProcess"
                    )
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout.strip()

            if not output:
                print(
                    "[OllamaManager] "
                    "No process found listening on port 11434."
                )
                return None

            # Get the first valid PID.
            pid = None

            for line in output.splitlines():

                line = line.strip()

                if line.isdigit():

                    pid = int(line)

                    break

            if pid is None:

                print(
                    "[OllamaManager] "
                    "Could not parse Ollama PID."
                )

                return None

            # Verify that this PID belongs to ollama.exe.
            verify = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        f"(Get-Process -Id {pid}).ProcessName"
                    )
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            process_name = verify.stdout.strip().lower()

            print(
                f"[OllamaManager] "
                f"Port 11434 owner: "
                f"PID={pid}, "
                f"Process={process_name}"
            )

            if process_name == "ollama":

                return pid

            print(
                "[OllamaManager] "
                "Port 11434 is owned by a process "
                "other than Ollama."
            )

            return None

        except Exception as error:

            print(
                "[OllamaManager] "
                f"Could not find Ollama server PID: "
                f"{error}"
            )

            return None

    # =====================================================
    # ADOPT EXISTING SERVER
    # =====================================================

    def adopt_existing(self):

        if not self.is_running():

            return False

        pid = self.find_server_pid()

        if pid is None:

            return False

        self.pid = pid

        self.process = "EXTERNAL"

        print(
            f"[OllamaManager] "
            f"Adopted existing Ollama server. "
            f"PID={pid}"
        )

        return True

    # =====================================================
    # START
    # =====================================================

    def start(self):

        # Already known process
        if self.is_running():

            if self.pid is None:

                self.adopt_existing()

            return {
                "success": False,
                "message": "Ollama is already running.",
                "running": True,
                "pid": self.pid
            }

        try:

            self.process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )

            self.pid = self.process.pid

        except Exception as error:

            return {
                "success": False,
                "message":
                    f"Failed to start Ollama: {error}",
                "running": False
            }

        # Wait for API
        for _ in range(20):

            if self.is_running():

                return {
                    "success": True,
                    "message":
                        "Ollama started successfully.",
                    "running": True,
                    "pid": self.pid
                }

            time.sleep(0.5)

        return {
            "success": False,
            "message":
                "Ollama process started but API "
                "did not become available.",
            "running": False,
            "pid": self.pid
        }

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        # If we don't know the PID, try to adopt it.
        if self.pid is None:

            self.adopt_existing()

        if self.pid is None:

            return {
                "success": False,
                "message":
                    "Ollama is running, but the "
                    "Ollama server process could "
                    "not be identified.",
                "running": self.is_running()
            }

        old_pid = self.pid

        try:

            result = subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(old_pid),
                    "/F"
                ],
                capture_output=True,
                text=True
            )

            print(
                "[OllamaManager] taskkill:",
                result.stdout.strip(),
                result.stderr.strip()
            )

        except Exception as error:

            return {
                "success": False,
                "message":
                    f"Failed to stop Ollama: {error}",
                "running": self.is_running(),
                "pid": old_pid
            }

        # Wait for API to disappear
        for _ in range(10):

            if not self.is_running():

                self.process = None
                self.pid = None

                return {
                    "success": True,
                    "message":
                        "Ollama stopped successfully.",
                    "running": False,
                    "pid": old_pid
                }

            time.sleep(0.5)

        return {
            "success": False,
            "message":
                "Ollama process was terminated "
                "but the API is still responding.",
            "running": True,
            "pid": old_pid
        }

    # =====================================================
    # STATUS
    # =====================================================

    def status(self):

        running = self.is_running()

        if running and self.pid is None:

            self.adopt_existing()

        return {
            "running": running,
            "pid": self.pid,
            "owned_by_controller":
                self.process is not None
        }


if __name__ == "__main__":

    manager = OllamaManager()

    print("Checking Ollama...")

    print(
        manager.status()
    )

    input(
        "\nPress ENTER to stop Ollama..."
    )

    print(
        manager.stop()
    )