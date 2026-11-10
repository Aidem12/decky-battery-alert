
import asyncio
import importlib.util
import sys
import tempfile
import unittest

from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestPluginLifecycle(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Simular Decky Loader dentro de WSL.
        fake_decky = ModuleType("decky")

        # Directorio temporal para las preferencias.
        self.settings_dir = tempfile.TemporaryDirectory()

        fake_decky.DECKY_PLUGIN_SETTINGS_DIR = (
            self.settings_dir.name
        )

        fake_decky.logger = Mock()
        fake_decky.emit = AsyncMock()

        # Cargar main.py utilizando el módulo Decky simulado.
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

        # Simular el servicio de lectura de batería.
        self.service = Mock()

        self.service_patch = patch.object(
            module,
            "BatteryService",
            return_value=self.service,
        )

        self.service_patch.start()

    async def asyncTearDown(self):
        # Detener cualquier tarea activa.
        await self.plugin._unload()

        # Restaurar las dependencias simuladas.
        self.service_patch.stop()

        # Eliminar los archivos temporales.
        self.settings_dir.cleanup()

    async def test_monitor_starts_and_stops(self):
        """Verify that monitoring starts and stops correctly."""

        self.service.check.return_value = {
            "battery": {
                "capacity": 50,
                "status": "Discharging",
            },
            "event": None,
        }

        await self.plugin._main()

        # Acelerar el monitoreo solo durante la prueba.
        self.plugin.config["check_interval"] = 0.01

        await asyncio.sleep(0.05)

        self.assertGreaterEqual(
            self.service.check.call_count,
            2,
        )

        await self.plugin._unload()

        # Comprobar que no continúa ejecutándose.
        count = self.service.check.call_count

        await asyncio.sleep(0.03)

        self.assertEqual(
            self.service.check.call_count,
            count,
        )

        self.decky.emit.assert_not_awaited()

    async def test_battery_alert_event(self):
        """Verify that battery alerts reach Decky."""

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
            return next(
                readings,
                {
                    "battery": {
                        "capacity": 80,
                        "status": "Charging",
                    },
                    "event": None,
                },
            )

        self.service.check.side_effect = next_reading

        await self.plugin._main()

        self.plugin.config["check_interval"] = 0.01

        # Esperar hasta recibir la notificación simulada.
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
        """Verify recovery from a temporary battery read error."""

        readings = iter([
            OSError("Temporary read error"),
            {
                "battery": {
                    "capacity": 60,
                    "status": "Discharging",
                },
                "event": None,
            },
        ])

        def next_reading():
            result = next(
                readings,
                {
                    "battery": {
                        "capacity": 60,
                        "status": "Discharging",
                    },
                    "event": None,
                },
            )

            if isinstance(result, Exception):
                raise result

            return result

        self.service.check.side_effect = next_reading

        await self.plugin._main()

        self.plugin.config["check_interval"] = 0.01

        # Permitir varias comprobaciones.
        await asyncio.sleep(0.05)

        await self.plugin._unload()

        # El monitor debe continuar después del error.
        self.assertGreaterEqual(
            self.service.check.call_count,
            2,
        )

        # Verificar que el error fue registrado.
        self.decky.logger.exception.assert_called()


if __name__ == "__main__":
    unittest.main()
