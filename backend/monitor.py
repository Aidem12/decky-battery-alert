
class BatteryMonitor:
    def __init__(self, charging_threshold=80, low_threshold=20):
        if not 0 <= charging_threshold <= 100:
            raise ValueError("Invalid charging threshold")
        if not 0 <= low_threshold <= 100:
            raise ValueError("Invalid low battery threshold")

        self.charging_threshold = charging_threshold
        self.low_threshold = low_threshold
        self.previous = None

    def update(self, battery):
        if battery is None:
            self.previous = None
            return None

        capacity = battery.get("capacity")
        status = battery.get("status")

        if (
            type(capacity) is not int
            or not 0 <= capacity <= 100
            or status not in ("Charging", "Discharging", "Full")
        ):
            self.previous = None
            return None

        current = {
            "capacity": capacity,
            "status": status,
        }

        previous = self.previous
        self.previous = current

        # Primera lectura: establecer referencia.
        if previous is None:
            return None

        # No generar alertas al cambiar el estado.
        if previous["status"] != status:
            return None

        old = previous["capacity"]

        if status == "Charging":
            if old < self.charging_threshold <= capacity:
                return "charging"

        if status == "Discharging":
            if old > self.low_threshold >= capacity:
                return "low_battery"

        return None
