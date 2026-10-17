# Desktop MCP backends, Skills and Codex instructions

This project has **one Tigo command** and different GUI MCP implementations. The graphics **session**, not the Linux distribution, determines which input/screenshot APIs exist.

## Overview

| Session | Primary backend | Notes |
|---|---|---|
| Hyprland/Wayland | [Hypruse](https://github.com/IlyasKhallouki/hypruse) | Compositor-specific IPC + native virtual input |
| Native X11: GNOME Xorg, Plasma X11, XFCE, Cinnamon, MATE, i3, Openbox, bspwm | Bundled `scripts/x11_mcp.py` | Requires xdotool, maim, wmctrl; input enabled for new registrations |
| GNOME / KDE / COSMIC and other Wayland | [wayland-mcp-kurojs](https://github.com/kurojs/wayland-mcp) | Portal/capture-dependent; experimental outside tested upstream setup |
| Windows 11 | [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) | Native Windows UI Automation |

**MCP** supplies tools. **Skills** supply workflows. **AGENTS.md** gives Codex persistent instructions. No component by itself means continuous observation or autonomous safe fixing.

## Hyprland

~~~sh
uvx hypruse doctor
codex mcp get hypruse
uvx hypruse skill install --agent codex
~~~

When missing, register the server (the Linux installer does this automatically):

~~~sh
codex mcp add hypruse --env HYPRUSE_STRICT=1 --env HYPRUSE_AUTH_GUARD=strict --env HYPRUSE_JOURNAL=1 --env HYPRUSE_MARK=0 -- uvx hypruse
~~~

New registrations have no confinement filter. An existing `HYPRUSE_CONFINE=launched` still blocks unrelated windows; registrations are preserved rather than silently reset.

## X11

The repository contains an X11 backend implemented with Python FastMCP and standard X11 tools. It provides `desktop_info`, `windows`, `active_window`, `ui_elements`, `click_ui`, `screenshot`, `screenshot_region`, `user_select_screenshot`, `focus_window`, `click`, `drag`, `key`, `type_text` and `scroll`. `drag` (application selection or moving objects) requires GUI input to be enabled in its registration; `screenshot_region` is read-only; `user_select_screenshot` waits for the human to draw a capture rectangle. The X11 drag always attempts to release its button, even after a failed movement.

~~~sh
codex mcp get tigo-x11
~~~

The installer registers:

~~~sh
codex mcp add tigo-x11 --env TIGO_X11_ALLOW_INPUT=1 -- uv run --no-project --with mcp python "$HOME/.local/share/tigo-codex/x11_mcp.py"
~~~

Named controls use the bundled `x11_accessibility.py` helper with `/usr/bin/python3`, system PyGObject and AT-SPI typelibs. See [semantic targeting](gui-operator.md#semantic-interface-targeting) for selectors and prerequisites. New registrations enable input; existing read-only registrations remain unchanged. To update one deliberately, follow [Linux instructions](linux.md#enable-x11-gui-input). X11 MCP **does not** work on Wayland merely because XWayland is running.

## General Wayland: GNOME, KDE Plasma, Sway, Niri, COSMIC, River

The generic backend is [kurojs/wayland-mcp](https://github.com/kurojs/wayland-mcp):

~~~sh
codex mcp get tigo-wayland
# If missing:
codex mcp add tigo-wayland --env WAYLAND_MCP_NO_PERSIST=1 -- uvx wayland-mcp-kurojs
~~~

In your agent session ask for the MCP's `describe_environment` tool. It reports available capture/input methods. Full functionality is **not** guaranteed. GNOME and KDE commonly provide `org.freedesktop.portal.RemoteDesktop`, while many wlroots compositors do **not**. Portals may display an OS consent prompt and can require PyGObject.

### PyGObject and uvx isolation

Your distro `python3-gi` may not be importable from `uvx`. A user-level Python environment with system packages visible is an option:

~~~sh
mkdir -p "$HOME/.local/share/tigo-codex"
uv venv --system-site-packages "$HOME/.local/share/tigo-codex/wayland-venv"
uv pip install --python "$HOME/.local/share/tigo-codex/wayland-venv/bin/python" wayland-mcp-kurojs
~~~

After checking that the installed environment has the required portal runtime, point the `tigo-wayland` Codex MCP command at `$HOME/.local/share/tigo-codex/wayland-venv/bin/wayland-mcp-kurojs`. Remove/re-add an old registration **only deliberately**, because that changes a security boundary:

~~~sh
codex mcp get tigo-wayland
codex mcp remove tigo-wayland
codex mcp add tigo-wayland --env WAYLAND_MCP_NO_PERSIST=1 -- "$HOME/.local/share/tigo-codex/wayland-venv/bin/wayland-mcp-kurojs"
~~~

Do not run upstream legacy scripts that give world-writable access to `/dev/input`, install permissive udev rules or NOPASSWD sudoers changes.

### Optional compositor-specific alternatives

**GNOME Wayland:** [GNOME Desktop MCP](https://github.com/sbuysse/gnome-desktop-mcp) uses a GNOME Shell extension + D-Bus and an explicit consent/kill switch. Requires supported GNOME Shell and Python versions; follow upstream extension installation. Register its published command with Codex **only after** enabling the extension and verifying its own health check. Do not assume that `uvx gnome-desktop-mcp` installs the extension.

**KDE Plasma 6 Wayland:** [kwin-mcp](https://github.com/isac322/kwin-mcp) supports virtual isolated sessions and opt-in live sessions. One example registration, after satisfying native build/runtime dependencies:

~~~sh
codex mcp add kwin-mcp -- uvx kwin-mcp --default-live-session
~~~

This targets the **real desktop**; use virtual mode for isolated tests when appropriate. Check upstream documentation for PyGObject/C compiler packages and KWin version compatibility.

**Sway / River / Niri / COSMIC:** Portal support, screenshot backends and input vary; no single universal compositor-specific tool is assumed. Use `describe_environment` and test screenshots before attempting input.

## Tigo Skill and AGENTS.md

The installer copies `skills/tigo-desktop/SKILL.md` to `~/.agents/skills/tigo-desktop/SKILL.md`. On Windows, the analogous path is under `%USERPROFILE%`.

It also appends a managed block to `CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`), preserving and backing up any existing instructions. New Codex sessions discover these instructions and installed MCPs. The Skill now routes requests involving real app interactions to the GUI backend automatically, including drag selection and region screenshots. For exact workflows, see [GUI Operator](gui-operator.md). The managed `AGENTS.md` block is refreshed safely on reinstall, preserving personal instructions.

The Tigo Skill and managed instructions require capability discovery before an
assistant reports that browser/desktop access is missing. Browser integration,
desktop MCP and a shell executable are independent: `hypruse` can be absent
from PATH while its MCP is available through uvx. A missing/disconnected browser
integration should lead to inspection of the session's available desktop MCP
and a read-only inventory before declaring the task impossible. A refusal,
authentication requirement or ownership hold still stops that action; this is
not a workaround for access restrictions. Opening a URL and inspecting its
images are separate outcomes and require separate evidence.

Normal installers already copy the Skill and refresh only the managed AGENTS
blocks with backups, preserving personal instructions. No new dependency or
access grant is required for this instruction update. Restart Tigo and start a
new conversation to load changed instructions; a resumed conversation may keep
its older context.

Open a **fresh Codex session** after changing MCPs or Skills:

~~~sh
codex mcp list
tigo status
tigo
~~~

Upstream references: [Codex MCP](https://developers.openai.com/codex/mcp), [Codex Skills](https://developers.openai.com/codex/skills), [Hypruse](https://github.com/IlyasKhallouki/hypruse), [Wayland MCP](https://github.com/kurojs/wayland-mcp), [GNOME Desktop MCP](https://github.com/sbuysse/gnome-desktop-mcp), [kwin-mcp](https://github.com/isac322/kwin-mcp).
