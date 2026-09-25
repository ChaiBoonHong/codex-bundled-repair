<div align="center">

<h1>🧰 Codex Bundled Repair</h1>
<p><strong>A calm, careful tune-up for Codex Desktop.</strong></p>
<p>Check Chrome and Computer Use. Repair only with your approval. Verify with temporary test targets.</p>
<p>
  <a href="https://github.com/ChaiBoonHong/codex-bundled-repair/releases/tag/v1.0.0">⬇️ Download v1.0.0</a>
  &nbsp;·&nbsp; <a href="#choose-your-launcher">Choose a launcher</a>
  &nbsp;·&nbsp; <a href="#safety-first">How safety works</a>
  &nbsp;·&nbsp; <a href="https://github.com/ChaiBoonHong/codex-bundled-repair/issues">Report an issue</a>
</p>
<p>
  <a href="https://github.com/ChaiBoonHong/codex-bundled-repair/actions/workflows/release.yml"><img alt="Build and tests pass" src="https://github.com/ChaiBoonHong/codex-bundled-repair/actions/workflows/release.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/ChaiBoonHong/codex-bundled-repair/releases/tag/v1.0.0"><img alt="Stable release v1.0.0" src="https://img.shields.io/github/v/release/ChaiBoonHong/codex-bundled-repair?label=stable"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-2ea44f"></a>
</p>

</div>

> [!IMPORTANT]
> **v1.0.0 is unsigned.** Automated tests and Windows/macOS package builds pass. The packaged GUI opened on the Windows development machine. Manual repair and guided-test interactions have not been completed on either platform, so those desktop interactions remain unverified.

## At a glance

| 🔎 Inspect | 🛡️ Repair | 🧪 Verify |
|---|---|---|
| Read plugin and cache status. No changes. | Back up first. Confirm before each change. | Use a temporary text file and local test page. |

## Quick navigation

- [Choose your launcher](#choose-your-launcher)
- [How it works](#how-it-works)
- [Safety first](#safety-first)
- [Read the results](#read-the-results)
- [Build and test](#build-and-test)
- [Platform verification](#platform-verification)

## Choose your launcher

The release ZIP includes a desktop window and a separate command-line launcher for each platform.

<details open>
<summary><strong>🪟 Windows</strong></summary>

**Desktop window:** double-click <code>codex-bundled-repair-windows-gui.exe</code>.

Windows needs the [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/). If it is missing, the app explains how to install it.

**Command line:** open PowerShell in the extracted folder:

~~~powershell
.\codex-bundled-repair-windows-cli.exe
.\codex-bundled-repair-windows-cli.exe --repair
.\codex-bundled-repair-windows-cli.exe --test
~~~

</details>

<details>
<summary><strong>🍎 macOS</strong></summary>

**Desktop window:** open <code>codex-bundled-repair-macos-gui.app</code>.

**Command line:** open Terminal in the extracted folder:

~~~bash
./codex-bundled-repair-macos-cli
./codex-bundled-repair-macos-cli --repair
./codex-bundled-repair-macos-cli --test
~~~

macOS may warn that the app is unsigned. The tool does not ask you to weaken macOS security settings.

</details>

### Check your download

Download <code>SHA256SUMS</code> next to the ZIP, then verify it:

- **macOS:** <code>shasum -a 256 -c SHA256SUMS</code>
- **Windows PowerShell:** compare <code>(Get-FileHash .\codex-bundled-repair-windows.zip -Algorithm SHA256).Hash</code> with the Windows line in <code>SHA256SUMS</code>.

## How it works

~~~mermaid
flowchart LR
    A["🔎 Read-only inspection"] --> B{"Bundled source valid?"}
    B -- No --> C["Stop with a clear diagnosis"]
    B -- Yes --> D{"Repair needed?"}
    D -- No --> G["🧪 Run the guided test"]
    D -- Yes --> E["📦 Verify backup"]
    E --> F["Ask before each change"]
    F --> H["Recheck plugins and cache"]
    H --> G
    G --> I{"Both temporary checks pass?"}
    I -- No --> J["Choose whether to keep or roll back"]
~~~

The tool checks <code>chrome@openai-bundled</code> and <code>computer-use@openai-bundled</code> through Codex's JSON CLI output. It compares plugin caches with the source bundled in Codex Desktop when that package can be located.

## Safety first

<details open>
<summary><strong>What happens before a repair?</strong></summary>

1. **Inspection:** read the marketplace, plugin status, cache manifests, and bundled source.
2. **Backup:** copy the plugin folder and available configuration/state files. Stop if the backup cannot be verified.
3. **Consent:** ask before closing Codex Desktop and before changing each plugin.
4. **Verification:** recheck plugin status and cache. Keep rollback available if verification fails.

</details>

<details>
<summary><strong>What will the tool never do?</strong></summary>

- Re-register or remove the reserved <code>openai-bundled</code> marketplace.
- Take ownership of or change WindowsApps permissions.
- Bypass macOS security settings.
- Read your existing documents, use your existing browser tabs, or upload diagnostics.
- Overwrite a newer <code>config.toml</code> during rollback.

Backups stay under <code>~/CodexPluginRepairBackups/</code> until you remove them.

</details>

## Read the results

| Result | Meaning | Next step |
|---|---|---|
| **Both plugins ready** | Installed, enabled, and cached manifests match. | Run the guided test to check desktop use. |
| **Repair offered** | A plugin is missing, disabled, or has a damaged cache. | Review the backup and approve each proposed change. |
| **Bundled source unavailable** | Codex cannot resolve a complete source that matches the app. | Repair or reinstall the official Codex Desktop app. |
| **Live test incomplete** | A temporary file edit or local browser click did not finish. | Review the message, then decide whether to keep or roll back a repair. |

If Codex changes <code>config.toml</code> after a repair, automatic rollback stops to protect the newer settings.

## The guided test

The **Guided Test** action creates a disposable text file, opens it in Notepad or TextEdit, and serves one local page at <code>127.0.0.1:&lt;port&gt;/mock</code>. The app shows two prompts for Codex Desktop: edit the temporary file and click the page’s test button. A pass requires both actions. The test waits up to five minutes and reports each result.

If the editor cannot reach the system temporary folder, the CLI accepts <code>--test-dir &lt;folder-you-own&gt;</code>. The tool creates a temporary subfolder there and does not change folder permissions.

## Build and test

People using the release ZIP do not need Python or Node.js. Source builds use Python 3.12+, Node.js 24, pywebview, and the pinned Tailwind CLI. Tailwind compiles to a local stylesheet; the desktop UI does not fetch styles from a CDN.

~~~bash
python -m venv .venv
python -m pip install -r requirements-gui.txt pyinstaller==6.22.3
npm ci
npm run build:css
python -m unittest discover -s tests -v
python build_release.py
~~~

Run <code>python gui.py</code> to launch the desktop window from a source checkout after building the stylesheet. Build on Windows for the Windows ZIP and macOS for the macOS ZIP. [GitHub Actions](https://github.com/ChaiBoonHong/codex-bundled-repair/actions/workflows/release.yml) tests and packages both platforms.

## Platform verification

| Check | Windows | macOS |
|---|---|---|
| Automated tests and GUI/CLI package builds | ✅ Passed in GitHub Actions | ✅ Passed in GitHub Actions |
| Packaged GUI opens on a real desktop | ✅ Opened on the development machine | ⏳ Needs a Mac desktop run |
| GUI repair and guided-test interaction | ⏳ Manual acceptance incomplete | ⏳ Manual acceptance incomplete |

The automated repair tests use temporary profiles and mocked Codex CLI responses. They do not change a real Codex installation. The release notes also record that manual desktop interactions remain unverified.

<details>
<summary><strong>Search records and design notes</strong></summary>

- [Codex CLI reference](https://learn.chatgpt.com/docs/developer-commands) documents machine-readable plugin status. The repair engine uses Codex's JSON output.
- [Computer Use guide](https://learn.chatgpt.com/docs/computer-use) and [browser guide](https://learn.chatgpt.com/docs/browser) explain why the live test is guided through Codex Desktop.
- [Tailwind CLI guide](https://tailwindcss.com/docs/installation/tailwind-cli) describes the static CSS build used for the offline interface.
- [pywebview architecture](https://pywebview.idepy.com/en/guide/architecture) and [installation requirements](https://github.com/r0x0r/pywebview/blob/master/docs/guide/installation.md) describe the local Python/JavaScript bridge and platform webviews.
- [An earlier Windows repair script](https://github.com/Jensen-Yao/codex-openai-bundled-plugin-repair) documents an older marketplace remove/add approach; this tool stops instead of re-registering the reserved source.

</details>

---

<sub>Independent, unofficial project. Not affiliated with OpenAI. Licensed under [MIT](LICENSE).</sub>
