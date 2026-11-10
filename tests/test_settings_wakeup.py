
import asyncio
import importlib.util
import sys
import tempfile
import unittest

from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestSettingsWakeup(unittest.IsolatedAsyncioTestCase):

    async def test_reenable_wakes_monitor_immediately(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_decky = ModuleType("decky")
            fake_decky.DECKY_PLUGIN_SETTINGS_DIR = directory
            fake_decky.logger = Mock()
            fake_decky.emit = AsyncMock()

            spec = importlib.util.spec_from_file_location(
                "battery_wakeup_test",
                PROJECT_ROOT / "main.py",
            )

            with patch.dict(sys.modules, {"decky": fake_decky}):
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            service = Mock()
            service.check.return_value = {
                "battery": {
                    "capacity": 50,
                    "status": "Discharging",
                },
                "event": None,
            }

            with patch.object(
                module,
                "BatteryService",
                return_value=service,
            ):
                plugin = module.Plugin()

                try:
                    await plugin._main()

                    # Permitir la primera lectura.
                    await asyncio.sleep(0.02)

                    settings = await plugin.get_settings()
                    settings["enabled"] = False

                    await plugin.save_settings(settings)
                    await asyncio.sleep(0.02)

                    # Ignorar lecturas anteriores.
                    service.check.reset_mock()

                    # Confirmar que no consulta estando apagado.
                    await asyncio.sleep(0.03)
                    service.check.assert_not_called()

                    reading_detected = asyncio.Event()

                    def on_read():
                        reading_detected.set()
                        return {
                            "battery": {
                                "capacity": 50,
                                "status": "Discharging",
                            },
                            "event": None,
                        }

                    service.check.side_effect = on_read

                    settings["enabled"] = True
                    await plugin.save_settings(settings)

                    # Debe despertar sin esperar 15 segundos.
                    await asyncio.wait_for(
                        reading_detected.wait(),
                        timeout=0.5,
                    )

                    self.assertGreaterEqual(
                        service.check.call_count,
                        1,
                    )

                finally:
                    await plugin._unload()


if __name__ == "__main__":
    unittest.main()
