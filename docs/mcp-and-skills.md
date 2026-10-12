# MCP, Skills, AGENTS.md: полная настройка

**MCP** даёт инструменты (screenshots, окна, mouse/keyboard). **Skills** дают процесс выполнения задачи. **AGENTS.md** — постоянные инструкции для Codex. Ничто из этого не создаёт непрерывного наблюдения без отдельного мониторинга.

## Linux — Hypruse

```fish
uvx hypruse doctor
codex mcp list
codex mcp get hypruse
uvx hypruse skill install --agent codex
```

Если MCP отсутствует, новый сервер можно добавить командой:

```fish
codex mcp add hypruse --env HYPRUSE_CONFINE=launched --env HYPRUSE_STRICT=1 --env HYPRUSE_AUTH_GUARD=strict --env HYPRUSE_JOURNAL=1 --env HYPRUSE_MARK=1 -- uvx hypruse
```

При настройке JARVIS вручную учитывай: если этот сервер уже зарегистрирован, `codex mcp add` может конфликтовать с существующим; сначала посмотри `codex mcp get hypruse`. Для GUI с существующими окнами иногда мешает `CONFINE=launched`; не снимай ограничения без понимания рисков.

## Windows 11 — Windows-MCP

```powershell
codex.cmd mcp list
codex.cmd mcp get windows-mcp
uvx windows-mcp serve --help
```

Если подключения нет:

```powershell
codex.cmd mcp add windows-mcp --env WINDOWS_MCP_EXCLUDE_TOOLS=PowerShell,Registry,Process,FileSystem,Clipboard -- uvx windows-mcp serve
```

`uvx windows-mcp serve` — stdio-server. Не нужно включать отдельную HTTP-службу и открывать порт ради локального Codex CLI. Если уже есть настройка MCP, установщик её не перезаписывает.

## Skill JARVIS

Файл `skills/jarvis-desktop/SKILL.md` устанавливается в `~/.agents/skills/jarvis-desktop/SKILL.md` (на Windows под `%USERPROFILE%`). В Linux отдельно устанавливается официальный Skill Hypruse. Перезапусти Codex и проверь `/skills`.

`AGENTS.md` установлен в `~/.codex/AGENTS.md` (на Windows аналог в профиле). Старое содержимое не затирается: добавляется помеченный блок, а существующий файл копируется в timestamp backup.

## Дополнительные MCP по желанию

Официальная документация OpenAI:

```bash
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

Любой новый MCP сервер — внешнее ПО и расширение прав AI-агента. Проверь upstream код, зависимости, security flags и то, какие данные увидит агент. Не включай обход sandbox/approvals ради удобства.

Первоисточники: [Codex MCP](https://developers.openai.com/codex/mcp), [Codex Skills](https://developers.openai.com/codex/skills), [Hypruse](https://github.com/IlyasKhallouki/hypruse), [Windows-MCP](https://github.com/CursorTouch/Windows-MCP).
