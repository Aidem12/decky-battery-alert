from pathlib import Path


class BatteryReader:
    def __init__(self, power_supply="/sys/class/power_supply"):
        self.power_supply = Path(power_supply)

    def find_battery(self):
        if not self.power_supply.is_dir():
            return None

        for device in sorted(self.power_supply.iterdir()):
            try:
                if (device / "type").read_text().strip() == "Battery":
                    return device
            except (OSError, UnicodeError):
                continue

        return None

    def read(self):
        battery = self.find_battery()

        if battery is None:
            return None

        try:
            capacity = int((battery / "capacity").read_text().strip())
            status = (battery / "status").read_text().strip()

            if not 0 <= capacity <= 100:
                return None

            return {
                "device": battery.name,
                "capacity": capacity,
                "status": status,
            }
        except (OSError, ValueError, UnicodeError):
            return None


if __name__ == "__main__":
    reader = BatteryReader()
    result = reader.read()

    if result is None:
        print("No se pudo detectar una batería.")
    else:
        print(result)

