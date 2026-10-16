# Repository maintenance rules

Read [readmeai.md](readmeai.md) for the current architecture and constraints
before changing the project.

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
