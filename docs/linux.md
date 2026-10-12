# CachyOS / Arch / Hyprland: полный гайд

## 1. Что происходит

`fish → jarvis → Codex CLI → Hypruse MCP → Hyprland` для GUI. Отдельно `systemd --user timer → watcher → Codex exec read-only → отчёт` для диагностики *упавших пользовательских служб*.

Нужны уже установленные и авторизованные Codex CLI и текущая сессия Hyprland. Hypruse не предназначен для KDE/GNOME без Hyprland.

## 2. Проверить зависимости

```fish
command -v codex
command -v uvx
command -v hyprctl
command -v grim
command -v wtype
command -v notify-send
uvx hypruse doctor
```

При необходимости на CachyOS:

```fish
sudo pacman -S --needed git uv grim wtype libnotify
```

Установить/авторизовать Codex CLI можно по [официальным инструкциям](https://github.com/openai/codex). Существующую рабочую установку заново ставить не нужно.

## 3. Инсталлятор

```fish
git clone https://github.com/ggnomer123s/Codex-jarvis.git
cd Codex-jarvis
bash scripts/install-linux.sh
```

Скрипт:
- сохраняет уже зарегистрированный Hypruse MCP (не сбрасывает твои параметры безопасности);
- при отсутствии MCP регистрирует `codex mcp add hypruse --env HYPRUSE_CONFINE=launched --env HYPRUSE_STRICT=1 --env HYPRUSE_AUTH_GUARD=strict --env HYPRUSE_JOURNAL=1 --env HYPRUSE_MARK=1 -- uvx hypruse`;
- ставит официальный `uvx hypruse skill install --agent codex` и собственный `jarvis-desktop` Skill;
- добавляет правила `~/.codex/AGENTS.md` с бэкапом старого содержимого;
- пишет `~/.local/bin/jarvis`, `jarvis-codex`, функцию fish в `~/.config/fish/functions/jarvis.fish`;
- включает systemd --user таймер проверки failed services каждые 2 минуты.

Перезапусти fish — и просто:

```fish
jarvis
```

## 4. Команды

```fish
jarvis status
jarvis reports
jarvis monitor off
jarvis monitor on
jarvis test
jarvis stop
```

`jarvis test` создаёт намеренно падающий временный user-service `jarvis-codex-test-failure`, вызывает мониторинг и снимает failed flag после теста. Он **не** удаляет пользовательские файлы. Для просмотра watcher-лога: `journalctl --user -u jarvis-codex-watch.service -n 80 --no-pager`.

## 5. MCP и права

`HYPRUSE_CONFINE=launched` позволяет управление только окнами, запущенными через Hypruse. Поэтому Codex может видеть старый Dolphin, но не обязательно нажимать на него. `HYPRUSE_STRICT` защищает от действий при вмешательстве пользователя, `HYPRUSE_AUTH_GUARD` ограничивает работу с auth dialogs. `JOURNAL` записывает действия, `MARK` отмечает активность. Это **ограничения внутри MCP**, а не изоляция всей системы.

```fish
codex mcp list
codex mcp get hypruse
uvx hypruse doctor
```

Не отключай защитные механизмы ради одного теста. Опасные изменения Codex должен обсуждать с человеком. Аварийная остановка: `jarvis stop` или `uvx hypruse stop`.

## 6. Мониторинг

Отчёты: `~/.local/state/jarvis-codex/reports`. Watcher обрабатывает только изменения набора failed systemd-user services, запрашивает `systemctl --user show` и последние строки `journalctl --user`. Затем пытается выполнить `codex exec` без MCP в read-only режиме и показать desktop notification. Логи могут включать личные данные и отправляться модели. Выключение: `jarvis monitor off`. **Автоматического ремонта нет.**

## 7. Если не работает

- `jarvis` не найден: начни новую fish-сессию; проверь `~/.config/fish/functions/jarvis.fish`.
- `uvx hypruse doctor` сообщает missing: установи только указанную зависимость.
- MCP конфигурация есть, но действий нет: проверь `HYPRUSE_CONFINE=launched`, реальные MCP approvals и новую сессию Codex.
- `jarvis status` или `systemctl --user status jarvis-codex-watch.timer` показывает проблему: посмотри user-journal.
- Изменения устаревших Skills могут требовать перезапуска Codex.

Источник: [Hypruse](https://github.com/IlyasKhallouki/hypruse).
