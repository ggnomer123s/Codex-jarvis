# Repository maintenance rules

Read [USER_HANDOFF.md](USER_HANDOFF.md) for the user's standing preferences,
latest corrections and Git workflow, then [readmeai.md](readmeai.md) for the
current architecture and constraints before changing the project. New direct
user instructions supersede archived preferences; check actual source/status.

- Record every implemented change in [changes.md](changes.md), including code,
  configuration, dependencies, documentation and installation scripts. Use a
  dated entry with the newest changes first. State what changed, the checks
  actually performed and any remaining limitations. Do not claim unperformed
  verification or expose private data.
- Whenever installation dependencies or requirements change, update the relevant
  installation instructions in the same change. For the desktop app, keep
  [docs/install-desktop.md](docs/install-desktop.md), affected platform guides,
  manifests, lockfiles and installer/update scripts consistent. Document new or
  removed packages, system prerequisites, model downloads and any upgrade steps.
- A change is not complete until its change report and any affected installation
  instructions are up to date.
- Keep the one-step entry points `install.sh`, `install.ps1` and `install.cmd`,
  platform installers/updaters and GUI Update Center compatible whenever setup,
  dependencies, supported systems, launch paths or update behavior changes.
  Update these scripts and their documented commands as part of the same task
  when needed. Preserve existing settings/login and never reset or stash user
  work to make an update succeed. Test changed installer/update paths with
  isolated fixtures before reporting them as ready.
