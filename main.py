
import asyncio
import contextlib

import decky

from backend.service import BatteryService


CHECK_INTERVAL = 15


class Plugin:

    async def _battery_loop(self):
        """Continuously monitor battery state."""
        decky.logger.info("Battery monitoring started")

        while True:
            try:
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

            await asyncio.sleep(CHECK_INTERVAL)

    async def _main(self):
        """Start battery monitoring."""
        self.service = BatteryService()

        self.monitor_task = asyncio.create_task(
            self._battery_loop()
        )

        decky.logger.info("Decky Battery Alert loaded")

    async def _unload(self):
        """Stop battery monitoring."""
        task = getattr(self, "monitor_task", None)

        if task is not None:
            task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await task

            self.monitor_task = None

        decky.logger.info("Decky Battery Alert unloaded")

    async def _uninstall(self):
        decky.logger.info(
            "Decky Battery Alert uninstalled"
        )
