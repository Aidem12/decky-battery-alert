
import asyncio
import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestPluginLifecycle(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Simular el módulo Decky que no existe en WSL.
        fake_decky = ModuleType("decky")
        fake_decky.logger = Mock()
        fake_decky.emit = AsyncMock()

        spec = importlib.util.spec_from_file_location(
            "battery_plugin_under_test",
            PROJECT_ROOT / "main.py",
        )

        with patch.dict(sys.modules, {"decky": fake_decky}):
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        self.module = module
        self.decky = fake_decky
        self.plugin = module.Plugin()
        self.service = Mock()

        # Acelerar las pruebas sin cambiar el intervalo real.
        self.interval_patch = patch.object(
            module, "CHECK_INTERVAL", 0.01
        )
        self.interval_patch.start()

        self.service_patch = patch.object(
            module,
            "BatteryService",
            return_value=self.service,
        )
        self.service_patch.start()

    async def asyncTearDown(self):
        await self.plugin._unload()
        self.service_patch.stop()
        self.interval_patch.stop()

    async def test_monitor_starts_and_stops(self):
        self.service.check.return_value = {
            "battery": {
                "capacity": 50,
                "status": "Discharging",
            },
            "event": None,
        }

        await self.plugin._main()
        await asyncio.sleep(0.05)

        self.assertGreaterEqual(
            self.service.check.call_count, 2
        )

        await self.plugin._unload()

        count = self.service.check.call_count
        await asyncio.sleep(0.03)

        self.assertEqual(
            self.service.check.call_count,
            count,
        )

        self.decky.emit.assert_not_awaited()

    async def test_battery_alert_event(self):
        event_received = asyncio.Event()

        async def capture_event(*args):
            event_received.set()

        self.decky.emit.side_effect = capture_event

        readings = iter([
            {
                "battery": {
                    "capacity": 79,
                    "status": "Charging",
                },
                "event": None,
            },
            {
                "battery": {
                    "capacity": 80,
                    "status": "Charging",
                },
                "event": "charging",
            },
        ])

        def next_reading():
            return next(readings, {
                "battery": {
                    "capacity": 80,
                    "status": "Charging",
                },
                "event": None,
            })

        self.service.check.side_effect = next_reading

        await self.plugin._main()

        await asyncio.wait_for(
            event_received.wait(),
            timeout=1,
        )

        await self.plugin._unload()

        self.decky.emit.assert_awaited_once_with(
            "battery_alert",
            "charging",
            80,
        )

    async def test_recovers_from_read_error(self):
        self.service.check.side_effect = [
            OSError("Temporary read error"),
            {
                "battery": {
                    "capacity": 60,
                    "status": "Discharging",
                },
                "event": None,
            },
        ]

        await self.plugin._main()
        await asyncio.sleep(0.015)
        await self.plugin._unload()

        self.assertGreaterEqual(
            self.service.check.call_count, 2
        )


if __name__ == "__main__":
    unittest.main()
