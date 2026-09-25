# Architecture

| File | Responsibility |
|---|---|
| `repair.py` | Shared CLI and GUI repair engine: diagnosis, source/cache validation, verified backup, confirmed changes, rollback, and temporary live-test targets. |
| `gui.py` | Launches the pywebview window and exposes a constrained action dispatcher plus event polling to the local page. |
| `ui/index.html`, `ui/app.js`, `ui/input.css` | Accessible dashboard, status cards, action controls, and Tailwind source styles. `ui/styles.css` is generated during the build and ignored by Git. |
| `requirements-gui.txt`, `package.json`, `package-lock.json` | Pin pywebview and the build-only Tailwind CLI. |
| `tests/test_repair.py`, `tests/test_gui.py` | Exercise repair safety and the GUI-to-engine flow with temporary data and mocked dialogs. |
| `build_release.py` | Builds separate console CLI and windowed GUI launchers, then archives both with the user guide and license. |
| `.github/workflows/release.yml` | Builds the stylesheet, runs tests, and packages Windows and macOS archives; version tags publish ZIPs and SHA-256 checksums. |
| `README.md` | Explains product purpose, use, setup, tests, deployment, limits, and source research. |
| `RELEASE_NOTES.md` | Supplies the stable v1.0.0 release summary and safety conditions. |
| `CONTEXT.md`, `lessons.md` | Record the active project phase and lasting user preferences. |
| `.gitignore`, `.gitattributes` | Exclude local build artifacts and preserve the repository's text line endings. |
| `LICENSE` | Grants MIT reuse rights. |

The CLI and GUI call the same `repair.py` workflows. The GUI serves its bundled files from pywebview's local server, then uses a narrow JavaScript-to-Python bridge for action requests and queued progress events. Repair confirmations use the native webview dialog. No generic shell command is exposed to the page. On Windows the launcher checks the WebView2 Runtime and forces pywebview's Edge renderer; macOS uses the system WebKit renderer.

On repair, `repair.py` still asks to close Codex Desktop, verifies a backup, confirms each plugin change, and verifies or rolls back the result. The guided test still uses a temporary file and a localhost page. Tests use temporary profiles and mocked Codex CLI responses. The release builder packages the GUI and CLI separately so the default CLI diagnosis behavior remains unchanged.
