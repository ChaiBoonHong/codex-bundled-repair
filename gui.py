"""Launch the local desktop interface for Codex Bundled Repair."""

import ctypes
from pathlib import Path
import queue
import shutil
import sys
import threading

import webview

import repair


TITLE = "Codex Bundled Repair"
WEBVIEW2_URL = "https://developer.microsoft.com/en-us/microsoft-edge/webview2/"


def webview2_runtime_present(registry=None):
    if sys.platform != "win32":
        return True
    if registry is None:
        import winreg as registry

    client_id = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    locations = (
        (registry.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{client_id}"),
        (registry.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{client_id}"),
        (registry.HKEY_CURRENT_USER, rf"Software\Microsoft\EdgeUpdate\Clients\{client_id}"),
    )
    for hive, path in locations:
        try:
            with registry.OpenKey(hive, path) as key:
                version = registry.QueryValueEx(key, "pv")[0]
        except OSError:
            continue
        try:
            if tuple(int(part) for part in version.split(".")) > (0, 0, 0, 0):
                return True
        except (AttributeError, TypeError, ValueError):
            continue
    return False


class RepairWindowAPI:
    def __init__(self):
        self.window = None
        self._events = queue.Queue()
        self._state_lock = threading.Lock()
        self._running = False

    def start(self, action):
        if action not in ("inspect", "repair", "test"):
            raise repair.RepairError("Unknown GUI action.")
        with self._state_lock:
            if self._running:
                return {"started": False, "message": "An action is already running."}
            self._running = True
        args = {"inspect": [], "repair": ["--repair"], "test": ["--test"]}[action]
        threading.Thread(target=self._run, args=(action, args), daemon=True).start()
        return {"started": True}

    def poll(self):
        events = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                break
        with self._state_lock:
            running = self._running
        return {"events": events, "running": running}

    def _emit(self, event_type, **data):
        self._events.put({"type": event_type, **data})

    def _confirm(self, message):
        return bool(self.window.create_confirmation_dialog(TITLE, message))

    def _status(self, root, statuses, packaged):
        safe_statuses = {
            name: {key: status[key] for key in ("installed", "enabled", "cache_ok", "version")}
            for name, status in statuses.items()
        }
        self._emit("status", statuses=safe_statuses)

    def _run(self, action, args):
        code = 1
        try:
            code = repair.main(
                args,
                confirm_fn=self._confirm,
                emit=lambda message: self._emit("log", message=str(message)),
                on_status=self._status,
            )
        except (repair.RepairError, OSError, RuntimeError) as error:
            self._emit("error", message=str(error))
        except Exception as error:
            self._emit("error", message=f"The action stopped unexpectedly: {error}")
        finally:
            self._emit("complete", action=action, code=code)
            with self._state_lock:
                self._running = False


def _ui_directory():
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / "ui"


def _show_windows_error(message):
    ctypes.windll.user32.MessageBoxW(None, message, TITLE, 0x10)


def main():
    if sys.platform not in ("win32", "darwin"):
        print("This desktop interface supports Windows and macOS only.", file=sys.stderr)
        return 1

    if sys.platform == "win32" and not webview2_runtime_present():
        _show_windows_error(
            "Microsoft Edge WebView2 Runtime is required to open this window.\n\n"
            f"Install it from {WEBVIEW2_URL}, then start Codex Bundled Repair again."
        )
        return 1

    ui_directory = _ui_directory()
    if not (ui_directory / "index.html").is_file() or not (ui_directory / "styles.css").is_file():
        message = "The desktop interface files are missing. Build the local Tailwind styles and try again."
        if sys.platform == "win32":
            _show_windows_error(message)
        else:
            print(message, file=sys.stderr)
        return 1

    api = RepairWindowAPI()
    window = webview.create_window(
        TITLE,
        url=str((ui_directory / "index.html").resolve()),
        js_api=api,
        width=1180,
        height=880,
        min_size=(760, 680),
        background_color="#f4f6fa",
        text_select=True,
    )
    api.window = window
    try:
        if sys.platform == "win32":
            webview.start(gui="edgechromium", http_server=True)
        else:
            webview.start(http_server=True)
    except Exception as error:
        message = f"The desktop window could not start.\n\n{error}"
        if sys.platform == "win32":
            _show_windows_error(message)
        else:
            print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
