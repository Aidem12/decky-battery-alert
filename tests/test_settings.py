
import json
import tempfile
import unittest
from pathlib import Path

from backend.settings import (
    BatterySettings,
    DEFAULT_SETTINGS,
)


class TestBatterySettings(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = BatterySettings(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_default_settings(self):
        result = self.settings.load()

        self.assertEqual(result, DEFAULT_SETTINGS)

    def test_save_and_load(self):
        config = DEFAULT_SETTINGS.copy()
        config["charging_threshold"] = 85
        config["low_threshold"] = 15

        self.settings.save(config)

        self.assertEqual(
            self.settings.load(),
            config,
        )

    def test_invalid_threshold(self):
        config = DEFAULT_SETTINGS.copy()
        config["charging_threshold"] = 150

        with self.assertRaises(ValueError):
            self.settings.save(config)

    def test_corrupted_file(self):
        path = Path(self.temp.name) / "settings.json"
        path.write_text("{invalid json")

        self.assertEqual(
            self.settings.load(),
            DEFAULT_SETTINGS,
        )


if __name__ == "__main__":
    unittest.main()
