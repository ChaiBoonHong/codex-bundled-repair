import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

import repair


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.home = self.base / ".codex"
        self.home.mkdir()
        (self.home / "config.toml").write_text("original\n", encoding="utf-8")
        self.root = self.base / "bundled"
        catalog = self.root / ".agents" / "plugins" / "marketplace.json"
        catalog.parent.mkdir(parents=True)
        catalog.write_text(json.dumps({"name": repair.MARKETPLACE, "plugins": [{"name": name} for name in repair.TARGETS]}), encoding="utf-8")
        for name in repair.TARGETS:
            source = self.root / "plugins" / name / ".codex-plugin" / "plugin.json"
            source.parent.mkdir(parents=True)
            source.write_text(f'{{"name":"{name}","version":"1"}}', encoding="utf-8")
            cache = self.home / "plugins" / "cache" / repair.MARKETPLACE / name / "1" / ".codex-plugin" / "plugin.json"
            cache.parent.mkdir(parents=True)
            cache.write_bytes(source.read_bytes())

    def listing(self):
        return {"installed": [{
            "pluginId": f"{name}@{repair.MARKETPLACE}", "source": {"path": str(self.root / "plugins" / name)},
            "version": "1", "installed": True, "enabled": True,
        } for name in repair.TARGETS], "available": []}

    def mock_json(self, codex, home, *args):
        if args[:2] == ("plugin", "marketplace"):
            return {"marketplaces": [{"name": repair.MARKETPLACE, "root": str(self.root)}]}
        return self.listing()

    def test_healthy_source_and_cache(self):
        with patch.object(repair, "command_json", side_effect=self.mock_json):
            root, statuses = repair.inspect("codex", self.home)
        self.assertEqual(root, self.root)
        self.assertTrue(all(status["installed"] and status["enabled"] and status["cache_ok"] for status in statuses.values()))

    def test_missing_reserved_source_stops(self):
        with patch.object(repair, "command_json", return_value={"marketplaces": []}):
            with self.assertRaisesRegex(repair.RepairError, "reserved source"):
                repair.inspect("codex", self.home)

    def test_corrupt_cache_is_detected(self):
        cache = self.home / "plugins" / "cache" / repair.MARKETPLACE / "chrome" / "1" / ".codex-plugin" / "plugin.json"
        cache.write_text("corrupt", encoding="utf-8")
        with patch.object(repair, "command_json", side_effect=self.mock_json):
            _, statuses = repair.inspect("codex", self.home)
        self.assertFalse(statuses["chrome"]["cache_ok"])
        self.assertTrue(statuses["computer-use"]["cache_ok"])

    def test_source_path_cannot_escape_marketplace(self):
        listing = self.listing()
        listing["installed"][0]["source"]["path"] = str(self.base)
        def answers(codex, home, *args):
            if args[:2] == ("plugin", "marketplace"):
                return {"marketplaces": [{"name": repair.MARKETPLACE, "root": str(self.root)}]}
            return listing
        with patch.object(repair, "command_json", side_effect=answers):
            with self.assertRaisesRegex(repair.RepairError, "invalid source path"):
                repair.inspect("codex", self.home)

    def test_package_copy_mismatch_stops(self):
        packaged = self.base / "package"
        source = packaged / ".agents" / "plugins" / "marketplace.json"
        source.parent.mkdir(parents=True)
        source.write_text("different", encoding="utf-8")
        with self.assertRaisesRegex(repair.RepairError, "differs"):
            repair.verify_package_copy(self.root, packaged)

    def test_backup_copies_required_files(self):
        (self.home / ".codex-global-state.json").write_text("state", encoding="utf-8")
        folder = repair.backup(self.home, self.base / "backups")
        self.assertEqual((folder / "config.toml").read_text(encoding="utf-8"), "original\n")
        self.assertEqual((folder / ".codex-global-state.json").read_text(encoding="utf-8"), "state")
        self.assertTrue((folder / "plugins" / "cache" / repair.MARKETPLACE / "chrome" / "1" / ".codex-plugin" / "plugin.json").is_file())
        self.assertIsNone(json.loads((folder / "backup.json").read_text(encoding="utf-8"))["files"]["codex-global-state.json"])

    def test_rollback_restores_original_cache_and_config(self):
        folder = repair.backup(self.home, self.base / "backups")
        current = self.home / "plugins" / "cache" / repair.MARKETPLACE / "chrome"
        old = self.home / "plugin-repair-quarantine" / folder.name / "chrome"
        old.parent.mkdir(parents=True)
        current.rename(old)
        (current / "new").mkdir(parents=True)
        (self.home / "config.toml").write_text("modified\n", encoding="utf-8")
        repair.rollback(self.home, folder, [("chrome", current, old)], repair.sha256(self.home / "config.toml"))
        self.assertTrue((current / "1" / ".codex-plugin" / "plugin.json").is_file())
        self.assertEqual((self.home / "config.toml").read_text(encoding="utf-8"), "original\n")

    def test_rollback_refuses_concurrent_config_change(self):
        folder = repair.backup(self.home, self.base / "backups")
        expected = repair.sha256(self.home / "config.toml")
        (self.home / "config.toml").write_text("changed by app\n", encoding="utf-8")
        with self.assertRaisesRegex(repair.RepairError, "changed config"):
            repair.rollback(self.home, folder, [], expected)

    def test_second_repair_failure_restores_first_plugin(self):
        folder = repair.backup(self.home, self.base / "backups")
        statuses = {}
        for name in repair.TARGETS:
            statuses[name] = {
                "installed": True, "enabled": False, "cache_ok": True,
                "cache_parent": self.home / "plugins" / "cache" / repair.MARKETPLACE / name,
            }
        def add_plugin(codex, home, *args):
            if args[2].startswith("computer-use@"):
                raise repair.RepairError("simulated install failure")
            current = statuses["chrome"]["cache_parent"]
            current.mkdir()
            (current / "new").write_text("new", encoding="utf-8")
            (self.home / "config.toml").write_text("modified\n", encoding="utf-8")
            return "{}"
        with patch.object(repair, "confirm", return_value=True), patch.object(repair, "command", side_effect=add_plugin):
            with self.assertRaisesRegex(repair.RepairError, "simulated install failure"):
                repair.repair("codex", self.home, statuses, folder)
        for name in repair.TARGETS:
            original = statuses[name]["cache_parent"] / "1" / ".codex-plugin" / "plugin.json"
            self.assertTrue(original.is_file())
        self.assertEqual((self.home / "config.toml").read_text(encoding="utf-8"), "original\n")

    def test_live_test_accepts_both_temporary_actions(self):
        def complete(url, target, token):
            target.write_text(f"READY\n{token}\n", encoding="utf-8")
            request = urllib.request.Request(f"{url}/click/{token}", method="POST")
            with urllib.request.urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 204)
        with patch.object(repair.subprocess, "Popen"):
            self.assertTrue(repair.live_test(self.base, on_ready=complete))


if __name__ == "__main__":
    unittest.main()
