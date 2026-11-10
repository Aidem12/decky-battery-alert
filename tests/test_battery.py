
import tempfile
import unittest
from pathlib import Path

from backend.battery import BatteryReader


class TestBatteryReader(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def create_battery(self, name, capacity, status):
        device = self.root / name
        device.mkdir()
        (device / "type").write_text("Battery\n")
        (device / "capacity").write_text(f"{capacity}\n")
        (device / "status").write_text(f"{status}\n")

    def test_charging(self):
        self.create_battery("BAT1", 80, "Charging")

        result = BatteryReader(self.root).read()

        self.assertEqual(result["capacity"], 80)
        self.assertEqual(result["status"], "Charging")

    def test_discharging(self):
        self.create_battery("BAT1", 20, "Discharging")

        result = BatteryReader(self.root).read()

        self.assertEqual(result["capacity"], 20)
        self.assertEqual(result["status"], "Discharging")

    def test_full(self):
        self.create_battery("BAT1", 100, "Full")

        result = BatteryReader(self.root).read()

        self.assertEqual(result["status"], "Full")

    def test_no_battery(self):
        result = BatteryReader(self.root).read()

        self.assertIsNone(result)

    def test_invalid_capacity(self):
        self.create_battery("BAT1", 150, "Charging")

        result = BatteryReader(self.root).read()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
