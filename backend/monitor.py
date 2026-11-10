
class BatteryMonitor:
    def __init__(
        self,
        charging_threshold=80,
        low_threshold=20,
        hysteresis=3,
    ):
        if type(charging_threshold) is not int or not 0 <= charging_threshold <= 100:
            raise ValueError("Invalid charging threshold")
        if type(low_threshold) is not int or not 0 <= low_threshold <= 100:
            raise ValueError("Invalid low battery threshold")
        if type(hysteresis) is not int or not 0 <= hysteresis <= 100:
            raise ValueError("Invalid hysteresis")

        self.charging_threshold = charging_threshold
        self.low_threshold = low_threshold
        self.hysteresis = hysteresis

        self.previous = None
        self.charging_armed = True
        self.low_armed = True

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

        # Rearmar alertas cuando se alcanza el margen.
        if capacity <= self.charging_threshold - self.hysteresis:
            self.charging_armed = True

        if capacity >= self.low_threshold + self.hysteresis:
            self.low_armed = True

        # No alertar en la primera lectura.
        if previous is None:
            return None

        # Evitar alertas al cambiar de estado.
        if previous["status"] != status:
            return None

        old = previous["capacity"]

        if status == "Charging":
            if (
                self.charging_armed
                and old < self.charging_threshold <= capacity
            ):
                self.charging_armed = False
                return "charging"

        if status == "Discharging":
            if (
                self.low_armed
                and old > self.low_threshold >= capacity
            ):
                self.low_armed = False
                return "low_battery"

        return None
