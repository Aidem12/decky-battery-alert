
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "out"
PLUGIN_FOLDER = "decky-battery-alert"


def build_package():
    package = json.loads(
        (ROOT / "package.json").read_text()
    )

    version = package["version"]

    required_files = [
        "plugin.json",
        "package.json",
        "main.py",
        "LICENSE",
        "README.md",
        "dist/index.js",
        "backend/battery.py",
	"backend/monitor.py",
	"backend/service.py",
	"backend/settings.py",
    ]

    for relative_path in required_files:
        path = ROOT / relative_path

        if not path.is_file():
            raise FileNotFoundError(
                f"Missing required file: {relative_path}"
            )

    OUTPUT.mkdir(exist_ok=True)

    archive_path = (
        OUTPUT / f"{PLUGIN_FOLDER}-v{version}.zip"
    )

    with ZipFile(
        archive_path,
        "w",
        compression=ZIP_DEFLATED,
    ) as archive:

        for relative_path in required_files:
            source = ROOT / relative_path
            destination = (
                f"{PLUGIN_FOLDER}/{relative_path}"
            )

            archive.write(source, destination)

    print(f"Package created: {archive_path}")


if __name__ == "__main__":
    build_package()
