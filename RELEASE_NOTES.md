Codex Bundled Repair is an independent, unofficial helper for the Chrome and Computer Use plugins in Codex Desktop.

- Windows: this unsigned **preview** passes automated tests, a read-only check against Codex Desktop, and a real Chrome plugin click. The full Computer Use file-edit test has not passed in the development environment. Extract the Windows ZIP and run the executable from a terminal.
- macOS: this unsigned **preview** passes automated tests and a hosted macOS build, but has not passed a real Mac desktop test. Extract the ZIP and run the executable from Terminal. Do not treat it as a verified Mac repair.
- Both platforms: the default run only diagnoses. Repair always requires a verified backup and confirmation for each plugin change. `--test` starts a guided test against temporary local targets.
- The tool does not change WindowsApps permissions, bypass macOS system permissions, or re-register Codex's reserved `openai-bundled` marketplace.

The ZIP SHA-256 values are published in `SHA256SUMS`.
