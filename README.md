# JARVIS — Codex desktop assistant

**Одна команда запуска: `jarvis`.** Настройка Codex CLI + MCP для управления рабочим столом, Skill, AGENTS.md и безопасная диагностика. Это пользовательский community-проект, не официальный продукт OpenAI.

| Возможность | Linux (CachyOS/Hyprland) | Windows 11 |
|---|---|---|
| GUI MCP | [Hypruse](https://github.com/IlyasKhallouki/hypruse) | [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) |
| Запуск | `jarvis` (fish) | `jarvis` (PowerShell/cmd) |
| Skills | Hypruse + JARVIS | JARVIS |
| Монитор | failed user systemd services | Windows Application errors (включить отдельно) |
| Самостоятельные исправления | Нет, нужно разрешение | Нет, нужно разрешение |

## Установка — CachyOS / Arch + Hyprland

Нужен установленный и авторизованный Codex CLI. Зависимости: `git`, `uvx`, `grim`, `wtype`, `notify-send`, `systemctl --user`.

```bash
sudo pacman -S --needed git uv grim wtype libnotify
git clone https://github.com/ggnomer123s/Codex-jarvis.git
cd Codex-jarvis
bash scripts/install-linux.sh
```

Открой новую сессию fish и запусти `jarvis`. Скрипт сохраняет существующее MCP-подключение, добавляет Skills/AGENTS.md, лаунчер и systemd-user monitor. Подробности — [Linux guide](docs/linux.md).

## Установка — Windows 11

Открой обычный PowerShell (не WSL). Установи базовые зависимости:

```powershell
winget install -e --id Git.Git
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id astral-sh.uv
```

Перезапусти PowerShell. Затем:

```powershell
npm.cmd install -g @openai/codex
codex.cmd
git clone https://github.com/ggnomer123s/Codex-jarvis.git
cd Codex-jarvis
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1
```

Перезапусти PowerShell и введи `jarvis`. Используй `codex.cmd` вместо `codex.ps1`, если блокирует Execution Policy. Полное руководство — [Windows 11](docs/windows11.md).

## Управление

| Команда | Назначение |
|---|---|
| `jarvis` | Открыть GUI-ассистента Codex |
| `jarvis status` | Проверить MCP/monitor |
| `jarvis reports` | Найти отчёты |
| `jarvis monitor off` | Выключить монитор |
| `jarvis monitor on` | Включить существующий монитор |
| `jarvis test` | Linux: сымитировать сбой test user-service |
| `jarvis stop` | Linux: аварийно остановить Hypruse |

**Важно:** Codex не наблюдает экран постоянно. MCP вызывается только во время задач. Monitoring проверяет лишь конкретные системные сигналы. Выводы логов/скриншоты могут содержать личные данные и передаваться модели. `--sandbox read-only` **не является блокировкой GUI-MCP инструментов**. Никогда не давай агенту sudo/пароли или обход подтверждений.

Документация: [Linux](docs/linux.md) · [Windows 11](docs/windows11.md) · [usage](docs/usage.md) · [MCP & Skills](docs/mcp-and-skills.md) · [security](docs/security.md).

Upstream: [Codex CLI](https://github.com/openai/codex), [Hypruse](https://github.com/IlyasKhallouki/hypruse), [Windows-MCP](https://github.com/CursorTouch/Windows-MCP), [uv](https://docs.astral.sh/uv/getting-started/installation/).
