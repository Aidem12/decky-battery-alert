
import asyncio
import importlib.util
import sys
import tempfile
import unittest

from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, Mock, patch

from backend.settings import BatterySettings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestSettingsIntegration(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()

        fake_decky = ModuleType("decky")
        fake_decky.DECKY_PLUGIN_SETTINGS_DIR = self.temp.name
        fake_decky.logger = Mock()
        fake_decky.emit = AsyncMock()

        spec = importlib.util.spec_from_file_location(
            "battery_settings_plugin_test",
            PROJECT_ROOT / "main.py",
        )

        with patch.dict(sys.modules, {"decky": fake_decky}):
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        self.module = module
        self.decky = fake_decky

        self.mock_service = Mock()
        self.mock_service.check.return_value = {
            "battery": {
                "capacity": 50,
                "status": "Discharging",
            },
            "event": None,
        }

        self.service_patch = patch.object(
            module,
            "BatteryService",
            return_value=self.mock_service,
        )
        self.service_patch.start()

        self.plugin = module.Plugin()
        await self.plugin._main()

    async def asyncTearDown(self):
        await self.plugin._unload()
        self.service_patch.stop()
        self.temp.cleanup()

    async def test_default_settings_loaded(self):
        settings = await self.plugin.get_settings()

        self.assertEqual(settings["charging_threshold"], 80)
        self.assertEqual(settings["low_threshold"], 20)
        self.assertTrue(settings["enabled"])

    async def test_settings_update_monitor(self):
        settings = await self.plugin.get_settings()

        settings["charging_threshold"] = 85
        settings["low_threshold"] = 15

        saved = await self.plugin.save_settings(settings)

        self.assertEqual(saved["charging_threshold"], 85)
        self.assertEqual(saved["low_threshold"], 15)

        # Comprobar que se reconstruyo el monitor.
        monitor = self.module.BatteryService.call_args.kwargs[
            "monitor"
        ]

        self.assertEqual(monitor.charging_threshold, 85)
        self.assertEqual(monitor.low_threshold, 15)

        # Comprobar persistencia en disco.
        stored = BatterySettings(self.temp.name).load()
        self.assertEqual(stored, saved)

    async def test_invalid_settings_preserve_configuration(self):
        original = await self.plugin.get_settings()
        invalid = original.copy()

        invalid["charging_threshold"] = 150

        with self.assertRaises(ValueError):
            await self.plugin.save_settings(invalid)

        self.assertEqual(
            await self.plugin.get_settings(),
            original,
        )

        self.assertEqual(
            BatterySettings(self.temp.name).load(),
            original,
        )

    async def test_disabled_monitor_skips_reading(self):
        settings = await self.plugin.get_settings()
        settings["enabled"] = False

        await self.plugin.save_settings(settings)

        # Registrar las lecturas realizadas antes de desactivar.
        previous_calls = self.mock_service.check.call_count

        # Forzar un intervalo corto para comprobar nuevos ciclos.
        self.plugin.config["check_interval"] = 0.01

        # El monitor debe permanecer desactivado.
        await asyncio.sleep(0.04)

        self.assertEqual(
            self.mock_service.check.call_count,
            previous_calls,
        )

        self.decky.emit.assert_not_awaited()

if __name__ == "__main__":
    unittest.main()
