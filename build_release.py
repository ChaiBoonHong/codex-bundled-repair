"""Build a single-file executable and a portable release archive."""

import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile


if sys.platform == "win32":
    label = "windows"
elif sys.platform == "darwin":
    label = "macos-preview"
else:
    raise SystemExit("Release builds support Windows and macOS only")

name = f"codex-bundled-repair-{label}"
subprocess.run([sys.executable, "-m", "PyInstaller", "--clean", "--onefile", "--name", name, "repair.py"], check=True)
binary = Path("dist") / (name + (".exe" if sys.platform == "win32" else ""))
archive = Path("dist") / f"{name}.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
    info = zipfile.ZipInfo(binary.name)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o755 if sys.platform == "darwin" else 0o644) << 16
    output.writestr(info, binary.read_bytes())
    output.write("README.md")
    output.write("LICENSE")
    output.write("RELEASE_NOTES.md")
print(f"{archive}: {hashlib.sha256(archive.read_bytes()).hexdigest()}")
