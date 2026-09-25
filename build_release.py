"""Build separate desktop GUI and command-line release assets."""

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys


if sys.platform == "win32":
    label = "windows"
    data_separator = ";"
elif sys.platform == "darwin":
    label = "macos"
    data_separator = ":"
else:
    raise SystemExit("Release builds support Windows and macOS only")

if not Path("ui/styles.css").is_file():
    raise SystemExit("Missing ui/styles.css. Run `npm run build:css` before packaging.")

cli_name = f"codex-bundled-repair-{label}-cli"
gui_name = f"codex-bundled-repair-{label}-gui"


def build(name, script, windowed=False):
    command = [sys.executable, "-m", "PyInstaller", "--clean", "--onefile", "--name", name]
    if windowed:
        command.extend(("--windowed", "--add-data", f"ui{data_separator}ui"))
    command.append(script)
    subprocess.run(command, check=True)


build(cli_name, "repair.py")
build(gui_name, "gui.py", windowed=True)

dist = Path("dist")
cli = dist / (cli_name + (".exe" if sys.platform == "win32" else ""))
gui = dist / (gui_name + (".exe" if sys.platform == "win32" else ".app"))
if not cli.is_file() or not gui.exists():
    raise SystemExit(f"Expected launchers were not built: {cli.name}, {gui.name}")

release_dir = dist / "release"
release_dir.mkdir(parents=True, exist_ok=True)
cli_asset = release_dir / cli.name
shutil.copy2(cli, cli_asset)

if sys.platform == "win32":
    gui_asset = release_dir / gui.name
    shutil.copy2(gui, gui_asset)
else:
    gui_asset = release_dir / f"{gui_name}.dmg"
    subprocess.run(
        ["hdiutil", "create", "-volname", "Codex Bundled Repair", "-srcfolder", str(gui), "-ov", "-format", "UDZO", str(gui_asset)],
        check=True,
    )

for asset in (gui_asset, cli_asset):
    print(f"{asset}: {hashlib.sha256(asset.read_bytes()).hexdigest()}")
