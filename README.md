<div align="center">

<h1>🧰 Codex Bundled Repair</h1>
<p><strong>A careful tune-up for Chrome and Computer Use in Codex Desktop.</strong></p>
<p>Inspect, repair, and verify bundled plugins with a desktop window or the command line.</p>
<p><a href="https://github.com/ChaiBoonHong/codex-bundled-repair/releases/tag/v0.1.0-preview.1">Download the preview</a> · <a href="#how-it-works">How it works</a> · <a href="https://github.com/ChaiBoonHong/codex-bundled-repair/issues">Report an issue</a></p>
<p>
  <a href="https://github.com/ChaiBoonHong/codex-bundled-repair/actions/workflows/release.yml"><img alt="Build and tests" src="https://github.com/ChaiBoonHong/codex-bundled-repair/actions/workflows/release.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/ChaiBoonHong/codex-bundled-repair/releases/tag/v0.1.0-preview.1"><img alt="Preview release" src="https://img.shields.io/github/v/release/ChaiBoonHong/codex-bundled-repair?include_prereleases&amp;label=preview"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-2ea44f"></a>
</p>

</div>

> [!IMPORTANT]
> The current `v0.1.0-preview.1` downloads are **unsigned CLI previews**. The Tailwind desktop GUI is being validated for `v1.0.0`; do not tag or describe it as stable until the GUI and repair flow pass on Windows and macOS.

## The four-step tune-up

| | What happens | Your control |
|---|---|---|
| 🔎 **Inspect** | Read the Codex marketplace, both plugin states, and the installed desktop bundle. | The default run makes no changes. |
| 📦 **Back up** | Copy the plugin directory, configuration, and available global state file. | Repair stops if the backup cannot be verified. |
| 🛠️ **Repair** | Install or enable a target plugin with Codex's own CLI; quarantine a bad cache if needed. | Confirm closing Codex and each plugin change. |
| 🧪 **Prove it** | Try a temporary text file and a local Chrome page. | Approve only those targets in Codex Desktop. |

## Get started

1. Download the ZIP for your platform and **SHA256SUMS** from the [preview release](https://github.com/ChaiBoonHong/codex-bundled-repair/releases/tag/v0.1.0-preview.1).
2. Check the ZIP's SHA-256 value, then extract it.
3. Start with the read-only check. Run repair only if it reports a problem.

**Windows PowerShell**

~~~powershell
.\codex-bundled-repair-windows.exe
.\codex-bundled-repair-windows.exe --repair
.\codex-bundled-repair-windows.exe --test
~~~

**macOS Terminal**

~~~bash
./codex-bundled-repair-macos-preview
./codex-bundled-repair-macos-preview --repair
./codex-bundled-repair-macos-preview --test
~~~

Each line is a separate command. Running the program without a flag only diagnoses. The <code>--repair</code> flag asks before it closes Codex or changes a plugin; <code>--test</code> starts the guided desktop test.

### Desktop window for v1.0.0

The upcoming desktop window includes the same read-only diagnosis, confirmed repair, and guided test. It uses a bundled Tailwind stylesheet and runs offline. The Windows window needs the [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/); macOS uses its built-in WebKit view.

The current release ZIP does not include the GUI yet. To run it from a source checkout:

~~~powershell
python -m pip install -r requirements-gui.txt
npm ci
npm run build:css
python gui.py
~~~

The v1 ZIP will include a separate GUI launcher and CLI launcher. On Windows, open <code>codex-bundled-repair-windows-gui.exe</code> or run <code>codex-bundled-repair-windows-cli.exe</code> in PowerShell. On macOS, open <code>codex-bundled-repair-macos-gui.app</code> or run <code>codex-bundled-repair-macos-cli</code> in Terminal. Opening the GUI starts a read-only inspection; repair still requires a verified backup and explicit confirmation before each change.

<details>
<summary><strong>How do I check the download?</strong></summary>

Place both ZIPs and <code>SHA256SUMS</code> in the same folder.

- On macOS, run <code>shasum -a 256 -c SHA256SUMS</code>.
- On Windows, run <code>(Get-FileHash .\codex-bundled-repair-windows.zip -Algorithm SHA256).Hash</code> in PowerShell and compare the result with the Windows line in <code>SHA256SUMS</code>.

The binaries are unsigned. Windows may show a SmartScreen warning. macOS may block an unsigned download; the tool does not ask you to turn off system security. If the executable bit was lost when extracting the macOS ZIP, run <code>chmod +x ./codex-bundled-repair-macos-preview</code>.

</details>

## How it works

~~~mermaid
flowchart LR
    A["🔎 Read-only check"] --> B{"Bundle valid?"}
    B -- No --> C["Stop with a clear diagnosis"]
    B -- Yes --> D{"Plugin needs repair?"}
    D -- No --> H["🧪 Guided live test"]
    D -- Yes --> E["📦 Back up and verify"]
    E --> F["Confirm each change"]
    F --> G["Recheck CLI and cache"]
    G --> H
    H --> I{"Live test passed?"}
    I -- No --> J["Choose: keep or safe rollback"]
~~~

The tool compares the resolved <code>openai-bundled</code> source with the desktop package when the package is accessible. It checks <code>chrome@openai-bundled</code> and <code>computer-use@openai-bundled</code> with Codex's JSON CLI output, then compares the cached manifests with their bundled originals.

A repair is offered only for a missing or disabled target plugin, or a damaged plugin cache. It uses <code>codex plugin add</code> after a verified backup. An original cache moved for repair remains in a reversible quarantine. Backups stay under <code>~/CodexPluginRepairBackups/</code> until you remove them.

> [!CAUTION]
> If the reserved bundled source itself is missing or invalid, the tool stops and points you to the official Codex Desktop repair or reinstall path. Newer Codex builds can reject manual registration of <code>openai-bundled</code>. This tool never changes WindowsApps permissions, bypasses macOS permissions, or replaces that reserved registration.

### The live test uses your desktop, not your personal data

The <code>--test</code> command creates a disposable text file, opens it in Notepad or TextEdit, and serves one page at <code>127.0.0.1:&lt;port&gt;/mock</code>. It gives you two prompts to send in Codex Desktop. A pass requires Computer Use to edit the temporary file and Chrome to click the page's test button. The tool waits up to five minutes and reports each result separately.

If your editor cannot reach the system temporary folder, use <code>--test-dir &lt;folder-you-own&gt;</code>. The tool creates a temporary subfolder there and does not change directory permissions. It never uploads diagnostics, reads your existing documents, or acts on existing browser tabs.

## Know your result

| Result | Meaning | Next step |
|---|---|---|
| **Both plugins ready** | Codex lists them as installed and enabled, and the local cache matches. | Run <code>--test</code> to check real desktop use. |
| **Repair offered** | A target plugin is missing, disabled, or has a bad cache. | Review the backup and each proposed change. |
| **Bundled source unavailable** | Codex cannot resolve a complete source that matches the app. | Repair or reinstall the official desktop app. |
| **Live test incomplete** | One or both desktop actions did not finish. | Check Codex permissions and the Chrome extension; choose whether to keep the repair or roll it back. |

If Codex edits <code>config.toml</code> after repair, the tool stops an automatic rollback rather than overwrite those newer settings. Your backup remains available.

## Build, test, release

The repair engine remains Python. The desktop window uses pywebview with local HTML, JavaScript, and Tailwind CSS. People using a release ZIP do **not** need Python or Node.js. PyInstaller packages the app; Node.js is used only to build the stylesheet.

Use Python 3.12 or newer. Create a virtual environment and activate it with <code>.\.venv\Scripts\Activate.ps1</code> on Windows or <code>source .venv/bin/activate</code> on macOS:

~~~bash
python -m venv .venv
~~~

Install the pinned GUI and packaging dependency, then install the pinned Tailwind tooling:

~~~bash
python -m pip install -r requirements-gui.txt pyinstaller==6.22.3
npm ci
npm run build:css
~~~

Then run the tests and build both launchers:

~~~bash
python -m unittest discover -s tests -v
python build_release.py
~~~

Build on each target operating system. [GitHub Actions](https://github.com/ChaiBoonHong/codex-bundled-repair/actions/workflows/release.yml) builds both launchers and runs the tests on Windows and macOS. Pushing a <code>v*</code> tag creates a Release with both ZIPs and <code>SHA256SUMS</code>; a tag containing <code>preview</code> is marked as a prerelease. The `v1.0.0` tag is held until the GUI and repair flow are manually verified on both platforms.

The automated tests use temporary directories and mocked Codex CLI responses. They do not change a real Codex installation. For file responsibilities and call flow, see [ARCHITECTURE.md](ARCHITECTURE.md).

### Preview verification

| Check | Windows | macOS |
|---|---|---|
| Automated tests and standalone build | ✅ Passed | ✅ Passed in GitHub Actions |
| Read-only check against Codex Desktop | ✅ Passed | ⏳ Needs a Mac |
| Real Chrome test click | ✅ Passed | ⏳ Needs a Mac |
| Real Computer Use file edit | ⏳ Needs a clean desktop run | ⏳ Needs a Mac |

### v1.0.0 GUI verification

| Check | Windows | macOS |
|---|---|---|
| GUI unit tests and Tailwind build | ✅ Passed locally | ⏳ GitHub Actions build pending |
| Packaged GUI launcher starts | ✅ Passed locally | ⏳ Needs a Mac |
| GUI repair and guided-test interaction | ⏳ Needs manual acceptance | ⏳ Needs manual acceptance |

The Windows launch check only confirmed that the packaged window opens. It did not exercise the repair controls or change the live Codex profile.

<details>
<summary><strong>Search records and design notes</strong></summary>

- [OpenAI's CLI reference](https://learn.chatgpt.com/docs/developer-commands) documents Codex plugin commands and machine-readable output. The tool uses those commands instead of parsing a formatted table.
- [OpenAI's Computer Use guide](https://learn.chatgpt.com/docs/computer-use) places desktop control in the Windows/macOS app. [The browser guide](https://learn.chatgpt.com/docs/browser) says its built-in browser is unavailable in the CLI, so the live test is guided through Codex Desktop.
- [An OpenAI Codex issue](https://github.com/openai/codex/issues/41164) reports that newer builds reject manual registration of the reserved <code>openai-bundled</code> source.
- [An earlier Windows repair script](https://github.com/Jensen-Yao/codex-openai-bundled-plugin-repair) documents the older remove/add approach. This tool takes the supported path and adds macOS checks, verified backups, rollback, and tests.
- No applicable ready-made repair solution was found on skills.sh during the initial search.
- Tailwind's [CLI guide](https://tailwindcss.com/docs/installation/tailwind-cli) confirms CSS can be compiled and bundled as a static file, so the app does not fetch styles at runtime.
- pywebview's [architecture guide](https://pywebview.idepy.com/en/guide/architecture) supports a local relative entry point with its built-in server and a Python/JavaScript bridge. Its [installation guide](https://github.com/r0x0r/pywebview/blob/master/docs/guide/installation.md) documents Windows WebView2 and macOS PyObjC requirements.
- GitHub reference: [python-desktop-app](https://github.com/codingforentrepreneurs/python-desktop-app) demonstrates a Python desktop app with HTML and a Python/JavaScript bridge. It is older, so implementation follows current pywebview documentation and uses no React framework.
- The skills.sh search found [Tailwind best-practice guidance](https://www.skills.sh/sergiodxa/agent-skills/frontend-tailwind-best-practices); no additional skill or UI component library is needed for this three-action window.

</details>

---

<sub>Independent, unofficial project. Not affiliated with OpenAI. Licensed under [MIT](LICENSE).</sub>
