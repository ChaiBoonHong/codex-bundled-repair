# Codex Bundled Repair v1.0.0

This release adds a local desktop window for diagnosis, repair, and the guided test. The Windows GUI and CLI, macOS GUI disk image, and macOS CLI are published as separate assets; there are no ZIP bundles.

- Fixes the packaged GUI page path so the bundled dashboard loads in the Windows and macOS launchers.
- The GUI uses pywebview and a locally compiled Tailwind stylesheet. It does not fetch UI files or styles from the network.
- Windows requires the Microsoft Edge WebView2 Runtime. macOS uses the system WebKit view.
- Diagnosis is read-only. Repair still requires a verified backup and confirmation before closing Codex Desktop and changing each plugin.
- The guided test uses a temporary file and a localhost page. The tool does not upload diagnostics, read existing documents, or act on existing browser tabs.
- The tool does not change WindowsApps permissions, bypass macOS system permissions, or re-register Codex's reserved `openai-bundled` marketplace.
- The Windows and macOS automated tests and package builds passed. Both launchers now serve the dashboard from the bundled resource path. Repair and guided-test controls still need manual desktop acceptance on both platforms.

SHA-256 values for each asset are published in `SHA256SUMS`.
