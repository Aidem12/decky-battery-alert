
import unittest

from backend.monitor import BatteryMonitor
from backend.service import BatteryService


class FakeBatteryReader:
    def __init__(self, readings):
        self.readings = iter(readings)

    def read(self):
        return next(self.readings)


class TestBatteryService(unittest.TestCase):

    def test_charging_notification(self):
        reader = FakeBatteryReader([
            {"capacity": 79, "status": "Charging"},
            {"capacity": 80, "status": "Charging"},
            {"capacity": 81, "status": "Charging"},
        ])

        service = BatteryService(
            reader=reader,
            monitor=BatteryMonitor(
                charging_threshold=80,
                low_threshold=20,
            ),
        )

        self.assertIsNone(service.check()["event"])

        result = service.check()

        self.assertEqual(result["event"], "charging")
        self.assertEqual(result["battery"]["capacity"], 80)

        self.assertIsNone(service.check()["event"])

    def test_low_battery_notification(self):
        reader = FakeBatteryReader([
            {"capacity": 21, "status": "Discharging"},
            {"capacity": 20, "status": "Discharging"},
        ])

        service = BatteryService(reader=reader)

        self.assertIsNone(service.check()["event"])
        self.assertEqual(
            service.check()["event"],
            "low_battery",
        )


if __name__ == "__main__":
    unittest.main()
