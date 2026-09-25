import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

import gui


class FakeRegistry:
    HKEY_LOCAL_MACHINE = "machine"
    HKEY_CURRENT_USER = "user"

    def __init__(self, versions):
        self.versions = iter(versions)

    def OpenKey(self, hive, path):
        value = next(self.versions)
        if value is None:
            raise FileNotFoundError(path)
        return FakeKey(value)

    @staticmethod
    def QueryValueEx(key, name):
        return key.version, 1


class FakeKey:
    def __init__(self, version):
        self.version = version

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class GuiTests(unittest.TestCase):
    def wait_for_completion(self, api):
        events = []
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            result = api.poll()
            events.extend(result["events"])
            if not result["running"]:
                return events
            time.sleep(0.01)
        self.fail("GUI action did not finish")

    def test_runtime_detection_accepts_a_registered_version(self):
        registry = FakeRegistry(["126.0.0.0"])
        with patch.object(gui.sys, "platform", "win32"):
            self.assertTrue(gui.webview2_runtime_present(registry))

    def test_runtime_detection_rejects_missing_runtime(self):
        registry = FakeRegistry([None, None, None])
        with patch.object(gui.sys, "platform", "win32"):
            self.assertFalse(gui.webview2_runtime_present(registry))

    def test_main_serves_the_bundled_page_by_absolute_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            ui_directory = Path(temporary) / "_MEI123" / "ui"
            ui_directory.mkdir(parents=True)
            (ui_directory / "index.html").write_text("<html></html>", encoding="utf-8")
            (ui_directory / "styles.css").write_text("", encoding="utf-8")

            for platform, start_args in (
                ("win32", {"gui": "edgechromium", "http_server": True}),
                ("darwin", {"http_server": True}),
            ):
                with self.subTest(platform=platform):
                    with (
                        patch.object(gui.sys, "platform", platform),
                        patch.object(gui, "webview2_runtime_present", return_value=True),
                        patch.object(gui, "_ui_directory", return_value=ui_directory),
                        patch.object(gui.webview, "create_window") as create_window,
                        patch.object(gui.webview, "start") as start,
                    ):
                        self.assertEqual(gui.main(), 0)

                    self.assertEqual(create_window.call_args.kwargs["url"], str((ui_directory / "index.html").resolve()))
                    start.assert_called_once_with(**start_args)

    def test_action_uses_shared_cli_flow_and_emits_status(self):
        api = gui.RepairWindowAPI()
        api.window = Mock()
        called = threading.Event()

        def run(args, *, confirm_fn, emit, on_status):
            self.assertEqual(args, ["--repair"])
            self.assertIs(confirm_fn.__self__, api)
            self.assertIs(confirm_fn.__func__, api._confirm.__func__)
            emit("Repair started")
            on_status(None, {"chrome": {"installed": True, "enabled": True, "cache_ok": True, "version": "1", "cache_parent": "private"}}, None)
            called.set()
            return 0

        with patch.object(gui.repair, "main", side_effect=run):
            self.assertTrue(api.start("repair")["started"])
            events = self.wait_for_completion(api)

        self.assertTrue(called.is_set())
        self.assertIn({"type": "log", "message": "Repair started"}, events)
        self.assertIn({"type": "status", "statuses": {"chrome": {"installed": True, "enabled": True, "cache_ok": True, "version": "1"}}}, events)
        self.assertIn({"type": "complete", "action": "repair", "code": 0}, events)

    def test_unknown_action_is_rejected(self):
        api = gui.RepairWindowAPI()
        with self.assertRaisesRegex(gui.repair.RepairError, "Unknown GUI action"):
            api.start("shell")

    def test_confirmation_uses_the_window_dialog(self):
        api = gui.RepairWindowAPI()
        api.window = Mock()
        api.window.create_confirmation_dialog.return_value = True
        self.assertTrue(api._confirm("Confirm the repair"))
        api.window.create_confirmation_dialog.assert_called_once_with(gui.TITLE, "Confirm the repair")

    def test_only_one_action_runs_at_a_time(self):
        api = gui.RepairWindowAPI()
        started = threading.Event()
        finish = threading.Event()

        def run(*args, **kwargs):
            started.set()
            finish.wait(2)
            return 0

        with patch.object(gui.repair, "main", side_effect=run):
            self.assertTrue(api.start("inspect")["started"])
            self.assertTrue(started.wait(1))
            self.assertFalse(api.start("test")["started"])
            finish.set()
            self.wait_for_completion(api)

    def test_gui_repair_uses_a_disposable_profile_and_keeps_confirmations(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            home = base / ".codex"
            home.mkdir()
            (home / "config.toml").write_text("original\n", encoding="utf-8")
            root = base / "bundled"
            catalog = root / ".agents" / "plugins" / "marketplace.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(
                json.dumps({"name": gui.repair.MARKETPLACE, "plugins": [{"name": name} for name in gui.repair.TARGETS]}),
                encoding="utf-8",
            )
            for name in gui.repair.TARGETS:
                source = root / "plugins" / name / ".codex-plugin" / "plugin.json"
                source.parent.mkdir(parents=True)
                source.write_text(json.dumps({"name": name, "version": "1"}), encoding="utf-8")

            installed = {name: False for name in gui.repair.TARGETS}

            def command_json(codex, codex_home, *args):
                if args[:2] == ("plugin", "marketplace"):
                    return {"marketplaces": [{"name": gui.repair.MARKETPLACE, "root": str(root)}]}
                plugins = [
                    {
                        "pluginId": f"{name}@{gui.repair.MARKETPLACE}",
                        "source": {"path": str(root / "plugins" / name)},
                        "version": "1",
                        "installed": installed[name],
                        "enabled": installed[name],
                    }
                    for name in gui.repair.TARGETS
                ]
                return {"installed": plugins, "available": []}

            def add_plugin(codex, codex_home, *args):
                name = args[2].split("@", 1)[0]
                source = root / "plugins" / name / ".codex-plugin" / "plugin.json"
                cached = home / "plugins" / "cache" / gui.repair.MARKETPLACE / name / "1" / ".codex-plugin" / "plugin.json"
                cached.parent.mkdir(parents=True)
                cached.write_bytes(source.read_bytes())
                installed[name] = True
                return "{}"

            api = gui.RepairWindowAPI()
            api.window = Mock()
            api.window.create_confirmation_dialog.side_effect = [True, True, True, False]
            with (
                patch.dict(os.environ, {"CODEX_HOME": str(home)}),
                patch.object(gui.shutil, "which", return_value="codex"),
                patch.object(gui.repair, "package_source", return_value=root),
                patch.object(gui.repair, "command_json", side_effect=command_json),
                patch.object(gui.repair, "command", side_effect=add_plugin) as add,
                patch.object(gui.repair, "close_codex") as close_codex,
                patch.object(Path, "home", return_value=base / "user"),
            ):
                self.assertTrue(api.start("repair")["started"])
                events = self.wait_for_completion(api)

            self.assertEqual(add.call_count, len(gui.repair.TARGETS))
            close_codex.assert_called_once()
            self.assertEqual(api.window.create_confirmation_dialog.call_count, 4)
            self.assertTrue((base / "user" / "CodexPluginRepairBackups").is_dir())
            status_events = [event for event in events if event["type"] == "status"]
            status_event = status_events[-1]
            self.assertTrue(all(status["installed"] and status["enabled"] and status["cache_ok"] for status in status_event["statuses"].values()))
            self.assertIn({"type": "complete", "action": "repair", "code": 0}, events)


if __name__ == "__main__":
    unittest.main()
