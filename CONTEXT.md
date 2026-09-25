# Current state

- Adding a Tailwind and pywebview desktop GUI for Windows and macOS, while preserving the CLI as a separate launcher.
- The GUI exposes read-only diagnosis, confirmed repair, and the guided temporary-target test. It uses the existing repair engine and retains verified backups, per-plugin consent, rollback, and the reserved-source safety stop.
- The source branch has 17 passing tests; GitHub Actions passed the Windows and macOS tests, stylesheet builds, and GUI/CLI packaging. The packaged GUI opens on the development Windows machine. Manual GUI and repair-flow checks are still required on both platforms.
- The merged GUI source passed Windows and macOS GitHub Actions. Stable `v1.0.0` is being published at the user's direction while manual GUI and repair-flow checks remain incomplete on both platforms; this status is stated in the release notes.
- The workspace directory has no Git metadata; source and release documentation are maintained through the connected GitHub repository.
- Keep user-facing content in English. The GUI uses bundled Tailwind CSS and never loads styling from a CDN.
