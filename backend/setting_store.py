import json
from pathlib import Path


SETTINGS_FILE = (
    Path(__file__).resolve().parent
    / "settings.json"
)


DEFAULT_SETTINGS = {
    "offline_only": True,
    "pre_start_check": True,
    "auto_stop_on_internet": True,
    "check_interval": 1
}


def load_settings():

    if not SETTINGS_FILE.exists():

        return DEFAULT_SETTINGS.copy()

    try:

        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        settings = DEFAULT_SETTINGS.copy()

        settings.update(data)

        return settings

    except Exception as error:

        print(
            f"Could not load settings: {error}"
        )

        return DEFAULT_SETTINGS.copy()


def save_settings(settings):

    try:

        with open(
            SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                settings,
                file,
                indent=4
            )

        return True

    except Exception as error:

        print(
            f"Could not save settings: {error}"
        )

        return False