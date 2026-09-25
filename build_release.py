"""Build the CLI and desktop GUI archives for the current platform."""

import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile


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


archive = dist / f"codex-bundled-repair-{label}.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
    output.write(cli, cli.name)
    if gui.is_dir():
        for path in sorted(gui.rglob("*")):
            if path.is_file():
                output.write(path, path.relative_to(dist).as_posix())
    else:
        output.write(gui, gui.name)
    for filename in ("README.md", "LICENSE", "RELEASE_NOTES.md"):
        output.write(filename)

print(f"{archive}: {hashlib.sha256(archive.read_bytes()).hexdigest()}")
