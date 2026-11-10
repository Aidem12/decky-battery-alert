
from backend.battery import BatteryReader
from backend.monitor import BatteryMonitor


class BatteryService:
    def __init__(self, reader=None, monitor=None):
        self.reader = reader if reader is not None else BatteryReader()
        self.monitor = monitor if monitor is not None else BatteryMonitor()

    def check(self):
        battery = self.reader.read()
        event = self.monitor.update(battery)

        return {
            "battery": battery,
            "event": event,
        }
