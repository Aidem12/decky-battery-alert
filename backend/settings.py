
import json
import os
import tempfile
from pathlib import Path


DEFAULT_SETTINGS = {
    "enabled": True,
    "charging_threshold": 80,
    "low_threshold": 20,
    "hysteresis": 3,
    "check_interval": 15,
}


class BatterySettings:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "settings.json"

    def validate(self, settings):
        if not isinstance(settings, dict):
            raise ValueError("Settings must be an object")

        if set(settings) != set(DEFAULT_SETTINGS):
            raise ValueError("Invalid settings fields")

        if type(settings["enabled"]) is not bool:
            raise ValueError("Invalid enabled value")

        ranges = {
            "charging_threshold": (0, 100),
            "low_threshold": (0, 100),
            "hysteresis": (0, 100),
            "check_interval": (5, 300),
        }

        for key, (minimum, maximum) in ranges.items():
            value = settings[key]

            if type(value) is not int:
                raise ValueError(f"Invalid type: {key}")

            if not minimum <= value <= maximum:
                raise ValueError(f"Invalid value: {key}")

        return settings.copy()

    def load(self):
        if not self.path.exists():
            return DEFAULT_SETTINGS.copy()

        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            return self.validate(data)

        except (OSError, ValueError, TypeError):
            return DEFAULT_SETTINGS.copy()

    def save(self, settings):
        settings = self.validate(settings)

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.directory,
                prefix=".settings-",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                json.dump(settings, file, indent=2)
                file.write("\n")

            os.replace(temporary_path, self.path)

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        return settings.copy()
