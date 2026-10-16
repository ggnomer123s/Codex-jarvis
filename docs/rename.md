# Tigo naming and upgrade compatibility (0.8.0)

The application and assistant are **Tigo**. Public commands are `tigo`,
`tigo-full` and `tigo-gui`; the Python package is `tigo_gui` and distribution
is `tigo-desktop-ui`. Installers, application menus, tray controls, messages,
Skill, managed instructions, icons and documentation use this identity.

## Voice activation

Enable Preferences > Wake to listen for **Tigo**, including its Russian
spelling. Exact matching is case-insensitive and respects word boundaries.
Tolerant matching additionally accepts a bounded list of likely transcripts
(`teego`, `tiggo`, `tygo`, a doubled Russian consonant) and split syllables.
It does not apply arbitrary one-edit distance to a four-letter name: ordinary
words such as `time` and `togo` must not activate the app. The previous product
name is not a wake alias. Waking still restores the window without sending a task.
Actual microphone/model accuracy depends on the user's hardware and speech.

## Existing installations

- Qt preferences migrate once from `QSettings("Jarvis", "Desktop")` to
  `QSettings("Tigo", "Desktop")`. Existing Tigo choices win. This preserves
  model, language, microphone, speech, wake, layout and other saved options.
- New private data uses `tigo-codex`. Existing `jarvis-codex` history,
  attachment references and repair databases stay at their original location.
  History and memory fallback are independent of the access preference. No
  transcripts or memory records are rewritten as part of the rename.
- An existing access preference remains authoritative. GUI and ordinary CLI
  use it consistently; rebranding must not enable Full Access over a saved
  restricted choice. The Codex home, login and authentication are unchanged.
- Verified neural voices reuse an existing `jarvis/voices` cache. Fresh caches
  use `tigo/voices`. No extra model download is needed for the name change.
- New environment options use `TIGO_`; relevant `JARVIS_` voice, input, memory
  and Codex overrides remain accepted, with Tigo options taking precedence.
- Existing `jarvis-x11` / `jarvis-wayland` MCP registrations and saved workflow
  server IDs remain valid without replacing permissions. New ones use Tigo IDs.
  The private instance-lock identity stays stable across versions so two
  applications cannot own microphone capture independently.
- Managed wake-startup entries move to Tigo and launch the current interpreter.
  Unrelated files/registry entries are preserved. The new menu shortcut replaces
  an owned old shortcut. Owned old CLI commands forward to Tigo, with backups.
  The old managed Skill is backed up outside the active skills directory.
- Existing monitor/report locations and scheduling identities remain compatible.
  No optional background monitor is newly enabled by the rename.

The source repository is still
[ggnomer123s/Codex-jarvis](https://github.com/ggnomer123s/Codex-jarvis).
Its clone URLs, commit/CI links and origin validation retain the real GitHub
address. References to other projects keep their actual upstream names.
Renaming a repository on GitHub is a separate owner action.

Run the normal GUI installer from the updated checkout, then quit the old
application completely and launch `tigo-gui`. The original checkout directory
can keep any name; moving it is unnecessary. Start a new conversation to load
the new installed assistant instructions.
