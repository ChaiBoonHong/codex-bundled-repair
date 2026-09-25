# Current state

- Stable `v1.0.0` is published with separate Tailwind/pywebview GUI and CLI launchers for Windows and macOS.
- The 17-test suite, local Tailwind build, and Windows/macOS GitHub Actions builds passed. The packaged GUI opens on the development Windows machine.
- Manual GUI action and repair-flow interaction remains unverified on both platforms; the release notes and README disclose this limit. Do not claim those interactions have been manually verified.
- The workspace directory has no Git metadata; source and release history are maintained in the connected GitHub repository.
- Keep user-facing content in English. The GUI uses bundled Tailwind CSS and never loads styling from a CDN.
