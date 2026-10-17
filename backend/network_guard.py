import requests
from datetime import datetime


class NetworkGuard:

    def __init__(self, timeout=2):
        self.timeout = timeout

        self.test_urls = [
            "https://www.google.com/generate_204",
            "https://1.1.1.1/",
        ]

    def is_internet_available(self):
        """
        Read-only Internet connectivity check.

        Returns True if at least one external endpoint responds.
        """

        for url in self.test_urls:

            try:
                response = requests.get(
                    url,
                    timeout=self.timeout
                )

                if response.status_code < 500:
                    return True

            except requests.RequestException:
                continue

        return False

    def status(self):
        available = self.is_internet_available()

        return {
            "internet_available": available,
            "checked_at": datetime.now().isoformat()
        }


if __name__ == "__main__":

    guard = NetworkGuard()

    print("Checking Internet connectivity...")

    result = guard.status()

    print(result)