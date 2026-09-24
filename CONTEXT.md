# Current state

- Building an independent Windows/macOS Codex bundled-plugin repair utility for public GitHub source and unsigned release ZIPs.
- The default command is read-only; repairs require a verified backup and per-plugin consent. Missing or invalid reserved sources stop with an official-app repair recommendation.
- Windows read-only diagnosis and Chrome live click passed. Ten automated tests and both GitHub Actions builds passed. Computer Use file-edit was blocked by the development environment and concurrent input; macOS desktop verification is unavailable. Both first binaries are labeled preview.
- The public GitHub repository and `v0.1.0-preview.1` release exist. The release is marked prerelease and contains both ZIPs plus a corrected `SHA256SUMS`; all published digests match GitHub's asset metadata.
- Next: complete a real Windows Computer Use file-edit test and a real macOS desktop test before describing either platform as fully verified.
- The README is now an English GitHub landing page with a preview notice, release links, a repair flow diagram, verification status, and contributor instructions. The user requested English throughout the application.
