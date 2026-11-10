
import asyncio
import contextlib

import decky

from backend.monitor import BatteryMonitor
from backend.service import BatteryService
from backend.settings import BatterySettings


class Plugin:

    def _create_service(self):
        monitor = BatteryMonitor(
            charging_threshold=self.config["charging_threshold"],
            low_threshold=self.config["low_threshold"],
            hysteresis=self.config["hysteresis"],
        )
        return BatteryService(monitor=monitor)

    async def get_settings(self):
        return self.config.copy()

    async def save_settings(self, settings: dict):
        saved = self.settings.save(settings)

        self.config = saved
        self.service = self._create_service()

        # Despertar el monitor para aplicar cambios.
        self.settings_changed.set()

        decky.logger.info("Battery settings updated")
        return saved.copy()

    async def _battery_loop(self):
        decky.logger.info("Battery monitoring started")

        while True:
            try:
                if self.config["enabled"]:
                    result = self.service.check()
                    battery = result["battery"]
                    event = result["event"]

                    if event is not None and battery is not None:
                        capacity = battery["capacity"]

                        decky.logger.info(
                            f"Battery alert: {event} at {capacity}%"
                        )

                        await decky.emit(
                            "battery_alert",
                            event,
                            capacity,
                        )

            except asyncio.CancelledError:
                raise

            except Exception:
                decky.logger.exception(
                    "Error while monitoring battery"
                )

            # Esperar al intervalo o a un cambio de ajustes.
            try:
                await asyncio.wait_for(
                    self.settings_changed.wait(),
                    timeout=self.config["check_interval"],
                )
            except asyncio.TimeoutError:
                pass
            finally:
                self.settings_changed.clear()

    async def _main(self):
        self.settings = BatterySettings(
            decky.DECKY_PLUGIN_SETTINGS_DIR
        )

        self.config = self.settings.load()
        self.service = self._create_service()
        self.settings_changed = asyncio.Event()

        self.monitor_task = asyncio.create_task(
            self._battery_loop()
        )

        decky.logger.info("Decky Battery Alert loaded")

    async def _unload(self):
        task = getattr(self, "monitor_task", None)

        if task is not None:
            task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await task

            self.monitor_task = None

        decky.logger.info("Decky Battery Alert unloaded")

    async def _uninstall(self):
        decky.logger.info("Decky Battery Alert uninstalled")
