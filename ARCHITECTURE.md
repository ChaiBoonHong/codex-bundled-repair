# Architecture

| File | Responsibility |
|---|---|
| `repair.py` | Reads Codex JSON status, verifies the bundled source and plugin cache, creates a backup, performs confirmed repairs, offers rollback, and hosts temporary live-test targets. |
| `tests/test_repair.py` | Checks healthy and invalid sources, cache detection, full backup, path safety, and rollback behavior with temporary data. |
| `build_release.py` | Packages `repair.py` as a standalone executable and ZIP on the current platform. |
| `.github/workflows/release.yml` | Runs tests and builds on Windows and macOS, then publishes tagged ZIPs and SHA-256 checksums. |
| `README.md` | Explains product purpose, use, setup, tests, deployment, limits, and source research. |
| `RELEASE_NOTES.md` | Supplies release safety and macOS preview text. |
| `LICENSE` | Grants MIT reuse rights. |
| `CONTEXT.md` | Records the current work phase and decisions. |
| `lessons.md` | Records lasting user guidance for this project. |
| `.gitignore` | Excludes build products, environments, and temporary mock data. |
| `.gitattributes` | Keeps Python, workflow, and documentation line endings consistent across operating systems. |

`repair.py` calls the installed Codex CLI for marketplace and plugin status. On repair, it asks to close Codex Desktop, backs up local state, calls `codex plugin add` for each approved target, then reads Codex status again. The live test starts local disposable targets and waits for results from a user-approved task in Codex Desktop. The tests import `repair.py` and replace CLI calls with local fixtures. The build script and GitHub workflow package that same file without changing its runtime behavior.
