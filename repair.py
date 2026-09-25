#!/usr/bin/env python3
"""Diagnose and repair the desktop Codex bundled Chrome and Computer Use plugins."""

import argparse
import hashlib
import http.server
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time


TARGETS = ("chrome", "computer-use")
MARKETPLACE = "openai-bundled"


class RepairError(Exception):
    pass


def confirm(message):
    return input(f"{message} [y/N] ").strip().lower() in ("y", "yes")


def command(codex, home, *args):
    env = os.environ.copy()
    env["CODEX_HOME"] = str(home)
    result = subprocess.run(
        [str(codex), *args], cwd=Path.home(), env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode:
        raise RepairError(f"codex {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def command_json(codex, home, *args):
    try:
        return json.loads(command(codex, home, *args))
    except json.JSONDecodeError as exc:
        raise RepairError(f"Codex returned invalid JSON for {' '.join(args)}") from exc


def manifest(plugin_dir):
    for relative in ("plugin.json", ".codex-plugin/plugin.json"):
        candidate = plugin_dir / relative
        if candidate.is_file():
            return candidate
    return None


def package_source():
    candidates = []
    if sys.platform == "win32":
        script = r"$p=Get-Process ChatGPT -ErrorAction SilentlyContinue | Where-Object Path | Select-Object -First 1 -ExpandProperty Path; if($p){Join-Path (Split-Path $p -Parent) 'resources\plugins\openai-bundled'}; Get-AppxPackage -Name OpenAI.Codex -ErrorAction SilentlyContinue | ForEach-Object {Join-Path $_.InstallLocation 'app\resources\plugins\openai-bundled'}"
        result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, errors="replace")
        candidates = [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]
    elif sys.platform == "darwin":
        for app in ("ChatGPT.app", "Codex.app"):
            candidates.extend((Path("/Applications") / app / "Contents/Resources/plugins/openai-bundled", Path.home() / "Applications" / app / "Contents/Resources/plugins/openai-bundled"))
    return next((path for path in candidates if (path / ".agents/plugins/marketplace.json").is_file()), None)


def verify_package_copy(root, packaged):
    catalog = ".agents/plugins/marketplace.json"
    if sha256(packaged / catalog) != sha256(root / catalog):
        raise RepairError("Bundled marketplace catalog differs from the installed desktop package. Stop and repair the official app.")
    for name in TARGETS:
        original, copy = packaged / "plugins" / name, root / "plugins" / name
        source_files = {str(path.relative_to(original)): sha256(path) for path in regular_files(original)}
        copied_files = {str(path.relative_to(copy)): sha256(path) for path in regular_files(copy)}
        if not source_files or source_files != copied_files:
            raise RepairError(f"Bundled source differs from the installed desktop package for {name}. Stop and repair the official app.")


def inside(path, root):
    try:
        return path.resolve().is_relative_to(root.resolve())
    except (OSError, RuntimeError):
        return False


def inspect(codex, home):
    markets = command_json(codex, home, "plugin", "marketplace", "list", "--json")
    entry = next((m for m in markets.get("marketplaces", []) if m.get("name") == MARKETPLACE), None)
    if not entry:
        raise RepairError("Codex does not resolve openai-bundled. This reserved source cannot be re-registered by this tool; repair or reinstall the official desktop app.")
    root = Path(entry["root"])
    catalog = root / ".agents" / "plugins" / "marketplace.json"
    try:
        data = json.loads(catalog.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RepairError(f"Bundled source is unreadable or invalid: {catalog}. Repair or reinstall the official desktop app.") from exc
    names = {p.get("name") for p in data.get("plugins", [])}
    if data.get("name") != MARKETPLACE or not set(TARGETS) <= names:
        raise RepairError("Bundled source does not contain both target plugins. Repair or reinstall the official desktop app.")
    listing = command_json(codex, home, "plugin", "list", "--marketplace", MARKETPLACE, "--available", "--json")
    entries = {p.get("pluginId"): p for p in listing.get("installed", []) + listing.get("available", [])}
    statuses = {}
    for name in TARGETS:
        plugin = entries.get(f"{name}@{MARKETPLACE}")
        if not plugin:
            raise RepairError(f"{name} is absent from the resolved bundled marketplace.")
        source_value = plugin.get("source", {}).get("path")
        source = Path(source_value) if source_value else root / "plugins" / name
        if not inside(source, root) or not manifest(source):
            raise RepairError(f"{name} has an invalid source path. No repair was attempted.")
        version = plugin.get("version", "")
        if not version or Path(version).name != version:
            raise RepairError(f"{name} has an invalid version value.")
        installed = bool(plugin.get("installed"))
        enabled = bool(plugin.get("enabled"))
        cache = home / "plugins" / "cache" / MARKETPLACE / name / version
        source_manifest = manifest(source)
        cached_manifest = manifest(cache) if installed else None
        cache_ok = bool(cached_manifest and source_manifest.read_bytes() == cached_manifest.read_bytes())
        statuses[name] = {
            "installed": installed, "enabled": enabled, "cache_ok": cache_ok,
            "version": version, "cache_parent": cache.parent,
        }
    return root, statuses


def diagnose(codex, home):
    root, statuses = inspect(codex, home)
    packaged = package_source()
    if packaged:
        verify_package_copy(root, packaged)
    return root, statuses, packaged


def regular_files(root):
    if not root.exists():
        return []
    found = []
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not os.path.isjunction(os.path.join(base, d))]
        found.extend(Path(base) / name for name in files)
    return found


def junctions(root):
    found = {}
    if not root.exists() or sys.platform != "win32":
        return found
    for base, dirs, _ in os.walk(root, followlinks=False):
        for name in dirs[:]:
            path = Path(base) / name
            if os.path.isjunction(path):
                found[str(path.relative_to(root))] = os.readlink(path)
                dirs.remove(name)
    return found


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup(home, base=None):
    if not (home / "config.toml").is_file():
        raise RepairError("config.toml is missing; a safe configuration backup cannot be made.")
    base = base or Path.home() / "CodexPluginRepairBackups"
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    folder = base / time.strftime("%Y%m%d-%H%M%S")
    if folder.exists():
        folder = base / f"{folder.name}-{secrets.token_hex(3)}"
    folder.mkdir(mode=0o700)
    plugins = home / "plugins"
    destination = folder / "plugins"
    if plugins.is_dir():
        if sys.platform == "win32":
            result = subprocess.run(
                ["robocopy", str(plugins), str(destination), "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:0", "/W:0", "/XJ", "/NFL", "/NDL", "/NP", "/NJH"],
                capture_output=True, text=True, errors="replace",
            )
            if result.returncode >= 8:
                raise RepairError(f"Plugin backup failed: {result.stdout[-800:]} {result.stderr[-400:]}")
        else:
            shutil.copytree(plugins, destination, symlinks=True)
        source_files, copied_files = regular_files(plugins), regular_files(destination)
        source_sizes = sorted((str(p.relative_to(plugins)), p.stat().st_size) for p in source_files)
        copied_sizes = sorted((str(p.relative_to(destination)), p.stat().st_size) for p in copied_files)
        if source_sizes != copied_sizes:
            raise RepairError(f"Plugin backup verification failed. Partial backup: {folder}")
    else:
        destination.mkdir()
    file_hashes = {}
    for name in ("config.toml", "codex-global-state.json", ".codex-global-state.json"):
        source = home / name
        if source.is_file():
            shutil.copy2(source, folder / name)
            if sha256(source) != sha256(folder / name):
                raise RepairError(f"Backup hash mismatch for {name}. Partial backup: {folder}")
            file_hashes[name] = sha256(source)
        else:
            file_hashes[name] = None
    (folder / "backup.json").write_text(json.dumps({"files": file_hashes, "junctions": junctions(plugins)}, indent=2), encoding="utf-8")
    return folder


def close_codex():
    if sys.platform == "win32":
        script = "$p=Get-Process ChatGPT -ErrorAction SilentlyContinue | Where-Object MainWindowHandle -ne 0; $p | ForEach-Object { $_.CloseMainWindow() | Out-Null }; for($i=0;$i -lt 15;$i++){if(-not (Get-Process ChatGPT -ErrorAction SilentlyContinue)){exit 0}; Start-Sleep -Seconds 1}; exit 2"
        result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
    else:
        result = subprocess.run(["osascript", "-e", 'tell application "ChatGPT" to quit'], capture_output=True, text=True)
        for _ in range(10):
            if subprocess.run(["pgrep", "-x", "ChatGPT"], capture_output=True).returncode:
                break
            time.sleep(1)
        else:
            raise RepairError("Codex is still running. Close it manually before repair.")
    if result.returncode:
        raise RepairError("Codex did not close cleanly. Save your work and close it manually before retrying.")


def repair(codex, home, statuses, backup_folder, confirm_fn=None, emit=None):
    confirm_fn = confirm_fn or confirm
    emit = emit or print
    changed = []
    quarantine = home / "plugin-repair-quarantine" / backup_folder.name
    config = home / "config.toml"
    for name, status in statuses.items():
        if status["installed"] and status["enabled"] and status["cache_ok"]:
            continue
        emit(f"\n{name}: installed={status['installed']}, enabled={status['enabled']}, cache valid={status['cache_ok']}")
        if not confirm_fn(f"Repair {name} using the verified bundled source?"):
            continue
        current = status["cache_parent"]
        old = quarantine / name
        moved = False
        if status["installed"] and current.exists():
            quarantine.mkdir(parents=True, exist_ok=True)
            if old.exists() or not inside(current, home / "plugins" / "cache" / MARKETPLACE):
                raise RepairError("Unsafe cache quarantine path; stopped without moving files.")
            current.rename(old)
            moved = True
        try:
            command(codex, home, "plugin", "add", f"{name}@{MARKETPLACE}", "--json")
            changed.append((name, current, old if moved else None))
        except RepairError:
            if current.exists():
                quarantine.mkdir(parents=True, exist_ok=True)
                failed = quarantine / f"failed-new-{name}"
                if failed.exists():
                    raise RepairError(f"Cannot protect partial cache; destination exists: {failed}")
                current.rename(failed)
            if moved:
                old.rename(current)
            rollback(home, backup_folder, changed, sha256(config) if config.is_file() else None)
            raise
    return changed, sha256(config) if config.is_file() else None


def rollback(home, backup_folder, changed, expected_config_hash):
    config = home / "config.toml"
    if expected_config_hash and (not config.is_file() or sha256(config) != expected_config_hash):
        raise RepairError(f"Codex changed config.toml since repair. Automatic rollback stopped to protect new settings. Backup: {backup_folder}")
    for name, current, old in reversed(changed):
        if current.exists():
            failed = home / "plugin-repair-quarantine" / backup_folder.name / f"failed-new-{name}"
            if failed.exists():
                raise RepairError(f"Rollback destination already exists: {failed}")
            failed.parent.mkdir(parents=True, exist_ok=True)
            current.rename(failed)
        if old and old.exists():
            old.rename(current)
    saved = backup_folder / "config.toml"
    if saved.is_file():
        shutil.copy2(saved, config)


def live_test(test_dir=None, on_ready=None, emit=None):
    emit = emit or print
    token = secrets.token_hex(8)
    clicked = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/mock":
                self.send_error(404)
                return
            page = f'<html><body><button onclick="fetch(\'/mock/click/{token}\',{{method:\'POST\'}}).then(()=>document.body.innerText=\'PASS\')">Click to test Chrome</button></body></html>'.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def do_POST(self):
            if self.path != f"/mock/click/{token}":
                self.send_error(404)
                return
            clicked.set()
            self.send_response(204)
            self.end_headers()

        def log_message(self, *_):
            pass

    if test_dir is not None:
        test_dir = test_dir.expanduser().resolve()
        test_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="codex-plugin-repair-", dir=test_dir, ignore_cleanup_errors=True) as temporary:
        target = Path(temporary) / "desktop-check.txt"
        target.write_text("READY\n", encoding="utf-8")
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/mock"
        try:
            try:
                if sys.platform == "win32":
                    subprocess.Popen(["notepad.exe", str(target)])
                else:
                    subprocess.Popen(["open", "-a", "TextEdit", str(target)])
            except OSError as exc:
                raise RepairError(f"Could not open the temporary test window: {exc}") from exc
            emit("\nOpen Codex Desktop and send these two prompts in a new task:")
            emit(f"1. Use Computer Use to open {target} in Notepad or TextEdit, append {token}, then save it.")
            emit(f"2. Use the Chrome plugin to open {url} and click 'Click to test Chrome'.")
            emit("Approve only access to these temporary targets. Waiting up to five minutes...")
            if on_ready:
                on_ready(url, target, token)
            deadline = time.monotonic() + 300
            while time.monotonic() < deadline:
                desktop_ok = token in target.read_text(encoding="utf-8", errors="replace")
                if desktop_ok and clicked.is_set():
                    emit("Live test passed: Computer Use and Chrome both acted on temporary targets.")
                    return True
                time.sleep(2)
            emit(f"Live test incomplete: Computer Use={desktop_ok}, Chrome={clicked.is_set()}.")
            return False
        finally:
            server.shutdown()
            server.server_close()


def main(argv=None, *, confirm_fn=None, emit=None, on_status=None):
    confirm_fn = confirm_fn or confirm
    emit = emit or print
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair", action="store_true", help="Back up and offer confirmed repairs")
    parser.add_argument("--test", action="store_true", help="Run a guided live test in Codex Desktop")
    parser.add_argument("--test-dir", type=Path, help="Use this writable, desktop-accessible parent folder for temporary test files")
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--codex", default=shutil.which("codex"))
    args = parser.parse_args(argv)
    if sys.platform not in ("win32", "darwin"):
        raise RepairError("This release supports Windows and macOS Codex Desktop only.")
    if not args.codex:
        raise RepairError("Codex CLI was not found. Install or repair the official Codex Desktop app.")
    home = args.codex_home.expanduser().resolve()
    root, statuses, packaged = diagnose(args.codex, home)
    if on_status:
        on_status(root, statuses, packaged)
    emit(f"Codex bundled source: {root}")
    if packaged:
        emit(f"Desktop package source matches: {packaged}")
    else:
        emit("Desktop package source could not be located; version match is unverified.")
    for name, status in statuses.items():
        emit(f"{name}: installed={status['installed']}, enabled={status['enabled']}, cache valid={status['cache_ok']}")
    needs_repair = any(not (s["installed"] and s["enabled"] and s["cache_ok"]) for s in statuses.values())
    if not args.repair and not args.test:
        emit("Run with --repair for confirmed repairs or --test for a guided desktop test.")
        return 2 if needs_repair else 0
    changed, backup_folder, config_hash = [], None, None
    if args.repair and needs_repair:
        if not packaged:
            raise RepairError("Cannot verify the bundled source against the installed desktop package; no repair was attempted.")
        emit("The tool will never change WindowsApps permissions or re-register the reserved marketplace.")
        if not confirm_fn("Save your Codex work. May the tool ask Codex Desktop to close for repair?"):
            return 2
        close_codex()
        backup_folder = backup(home)
        emit(f"Verified backup: {backup_folder}")
        changed, config_hash = repair(args.codex, home, statuses, backup_folder, confirm_fn, emit)
        try:
            refreshed_root, refreshed = inspect(args.codex, home)
        except RepairError:
            rollback(home, backup_folder, changed, config_hash)
            raise
        if on_status:
            on_status(refreshed_root, refreshed, packaged)
        if any(not (s["installed"] and s["enabled"] and s["cache_ok"]) for s in refreshed.values()):
            rollback(home, backup_folder, changed, config_hash)
            emit("Plugin verification did not pass; the tool's changes were rolled back.")
            return 2
        emit("Plugin list and cache verification passed. Reopen Codex Desktop before the live test.")
    if args.test or (changed and confirm_fn("Run the guided live desktop test now?")):
        if not live_test(args.test_dir, emit=emit):
            if changed and confirm_fn("Live test failed. Restore the tool's changes?"):
                if not confirm_fn("Save your Codex work. May the tool close Codex Desktop for rollback?"):
                    return 2
                close_codex()
                rollback(home, backup_folder, changed, config_hash)
                emit("The tool's changes were rolled back; the backup remains available.")
            return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RepairError, OSError) as error:
        print(f"Stopped safely: {error}", file=sys.stderr)
        sys.exit(1)
