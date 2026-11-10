
import unittest

from backend.monitor import BatteryMonitor


def battery(capacity, status):
    return {
        "capacity": capacity,
        "status": status,
    }


class TestBatteryMonitor(unittest.TestCase):

    def test_charging_threshold(self):
        monitor = BatteryMonitor(charging_threshold=80)

        self.assertIsNone(
            monitor.update(battery(79, "Charging"))
        )
        self.assertEqual(
            monitor.update(battery(80, "Charging")),
            "charging"
        )

    def test_low_battery_threshold(self):
        monitor = BatteryMonitor(low_threshold=20)

        self.assertIsNone(
            monitor.update(battery(21, "Discharging"))
        )
        self.assertEqual(
            monitor.update(battery(20, "Discharging")),
            "low_battery"
        )

    def test_no_duplicate_notifications(self):
        monitor = BatteryMonitor()

        monitor.update(battery(79, "Charging"))

        self.assertEqual(
            monitor.update(battery(80, "Charging")),
            "charging"
        )
        self.assertIsNone(
            monitor.update(battery(80, "Charging"))
        )
        self.assertIsNone(
            monitor.update(battery(81, "Charging"))
        )

    def test_initial_reading_no_notification(self):
        monitor = BatteryMonitor()

        self.assertIsNone(
            monitor.update(battery(80, "Charging"))
        )

    def test_percentage_jump(self):
        monitor = BatteryMonitor()

        monitor.update(battery(75, "Charging"))

        self.assertEqual(
            monitor.update(battery(85, "Charging")),
            "charging"
        )

    def test_status_change(self):
        monitor = BatteryMonitor()

        monitor.update(battery(79, "Discharging"))

        self.assertIsNone(
            monitor.update(battery(80, "Charging"))
        )

    def test_missing_battery(self):
        monitor = BatteryMonitor()

        self.assertIsNone(monitor.update(None))
        self.assertIsNone(
            monitor.update(battery(80, "Charging"))
        )

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            BatteryMonitor(charging_threshold=120)

    def test_rearm_after_dropping(self):
        monitor = BatteryMonitor()

        monitor.update(battery(79, "Charging"))

        self.assertEqual(
            monitor.update(battery(80, "Charging")),
            "charging"
        )

        # Histeresis de 3 puntos: bajar al 77%.
        monitor.update(battery(77, "Charging"))

        self.assertEqual(
            monitor.update(battery(82, "Charging")),
            "charging"
        )


class TestBatteryHysteresis(unittest.TestCase):

    def test_charging_fluctuation(self):
        monitor = BatteryMonitor(hysteresis=3)

        monitor.update(battery(79, "Charging"))

        self.assertEqual(
            monitor.update(battery(80, "Charging")),
            "charging"
        )

        # Oscilaciones que no deben generar mas alertas.
        for value in [79, 80, 79, 81, 78, 80]:
            self.assertIsNone(
                monitor.update(battery(value, "Charging"))
            )

    def test_charging_rearm(self):
        monitor = BatteryMonitor(hysteresis=3)

        monitor.update(battery(79, "Charging"))

        self.assertEqual(
            monitor.update(battery(80, "Charging")),
            "charging"
        )

        # El margen de rearme es 80 - 3 = 77.
        monitor.update(battery(77, "Charging"))

        self.assertEqual(
            monitor.update(battery(80, "Charging")),
            "charging"
        )

    def test_low_battery_rearm(self):
        monitor = BatteryMonitor(hysteresis=3)

        monitor.update(battery(21, "Discharging"))

        self.assertEqual(
            monitor.update(battery(20, "Discharging")),
            "low_battery"
        )

        # Una oscilacion pequena no debe repetir el aviso.
        monitor.update(battery(21, "Discharging"))

        self.assertIsNone(
            monitor.update(battery(20, "Discharging"))
        )

        # El margen de rearme es 20 + 3 = 23.
        monitor.update(battery(23, "Discharging"))

        self.assertEqual(
            monitor.update(battery(20, "Discharging")),
            "low_battery"
        )


if __name__ == "__main__":
    unittest.main()
