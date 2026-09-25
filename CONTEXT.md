# Current state

- Stable `v1.0.0` is published as separate Windows GUI/CLI files and macOS GUI DMG/CLI files, with matching SHA-256 checksums and no ZIP release assets.
- The user reported a Windows GUI 404 caused by the relative page URL resolving outside PyInstaller's one-file bundle. The launcher now passes the absolute bundled page path and enables pywebview's local HTTP server; CI and the v1.0.0 asset refresh are in progress.
- Manual GUI action and repair-flow interaction remains unverified on both platforms; the release notes and README disclose this limit. Do not claim those interactions have been manually verified.
- The workspace directory is a clean Git checkout on `main` and tracks the connected GitHub repository's `origin/main` branch.
- README is a polished v1.0.0 landing page with launcher details, collapsible sections, a Mermaid flow, and the current platform-verification status.
- Keep user-facing content in English. The GUI uses bundled Tailwind CSS and never loads styling from a CDN.
