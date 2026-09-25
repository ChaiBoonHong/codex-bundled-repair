# Current state

- Adding a Tailwind and pywebview desktop GUI for Windows and macOS, while preserving the CLI as a separate launcher.
- The GUI exposes read-only diagnosis, confirmed repair, and the guided temporary-target test. It uses the existing repair engine and retains verified backups, per-plugin consent, rollback, and the reserved-source safety stop.
- The source branch has 17 passing tests. The Windows GUI and CLI launchers package successfully, and the GUI opens on the development Windows machine. Cross-platform Actions and macOS desktop checks are pending.
- Stable `v1.0.0` remains gated on manual GUI and isolated repair-flow verification on both Windows and macOS. The existing public release is still `v0.1.0-preview.1`.
- The workspace directory has no Git metadata; the source is being prepared in a clean clone for a GitHub pull request.
- Keep user-facing content in English. The GUI uses bundled Tailwind CSS and never loads styling from a CDN.
