"""Describe semantic interface tools actually reported by connected MCPs."""


def interface_summary(servers):
    found = []
    for server in servers if isinstance(servers, list) else []:
        if not isinstance(server, dict):
            continue
        name = str(server.get('name', ''))
        raw = server.get('tools', {})
        values = raw.values() if isinstance(raw, dict) else raw if isinstance(raw, list) else []
        tools = {str(item.get('name', '')).casefold().removesuffix('-tool') for item in values if isinstance(item, dict)}
        if isinstance(raw, dict):
            tools.update(str(key).casefold().removesuffix('-tool') for key in raw)
        if name == 'windows-mcp' and 'snapshot' in tools:
            found.append('Windows UI Automation: Snapshot available')
        elif name == 'hypruse' and {'ui', 'click_ui'} <= tools:
            found.append('Hyprland accessibility: ui + click_ui available')
        elif name in ('tigo-x11', 'jarvis-x11') and {'ui_elements', 'click_ui'} <= tools:
            found.append('X11 AT-SPI: ui_elements + click_ui available')
    return '; '.join(found) + '. Availability does not prove app accessibility or input ownership.' if found else 'No semantic interface tools reported. Check backend version/registration; use supported visual tools when needed.'
