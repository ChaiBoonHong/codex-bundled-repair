# Current state

- Building an independent Windows/macOS Codex bundled-plugin repair utility for public GitHub source and unsigned release ZIPs.
- The default command is read-only; repairs require a verified backup and per-plugin consent. Missing or invalid reserved sources stop with an official-app repair recommendation.
- Windows read-only diagnosis and Chrome live click passed. Ten automated tests cover source, cache, backup, rollback, and the local live-test harness. The Computer Use file-edit test needs an accessible non-sandbox folder; macOS desktop verification is unavailable, so its binary is labeled preview.
- Next: rebuild the final ZIP, inspect the source set, and publish the repository only when the release claims match verification.
