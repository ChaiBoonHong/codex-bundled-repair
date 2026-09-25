# Codex Bundled Repair v1.0.0

This release adds a local desktop window for diagnosis, repair, and the guided test. The existing command-line launcher remains available in each platform ZIP.

- The GUI uses pywebview and a locally compiled Tailwind stylesheet. It does not fetch UI files or styles from the network.
- Windows requires the Microsoft Edge WebView2 Runtime. macOS uses the system WebKit view.
- Diagnosis is read-only. Repair still requires a verified backup and confirmation before closing Codex Desktop and changing each plugin.
- The guided test uses a temporary file and a localhost page. The tool does not upload diagnostics, read existing documents, or act on existing browser tabs.
- The tool does not change WindowsApps permissions, bypass macOS system permissions, or re-register Codex's reserved `openai-bundled` marketplace.
- This stable tag is created only after the packaged GUI and isolated repair flow have been verified on both Windows and macOS.

The unsigned ZIP SHA-256 values are published in `SHA256SUMS`.
