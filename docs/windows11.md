# Установка на Windows 11 (полный гайд)

**Работаем в обычном PowerShell на Windows, не внутри WSL.** Hypruse предназначен для Hyprland, поэтому здесь применяется [Windows-MCP](https://github.com/CursorTouch/Windows-MCP), который использует Windows UI Automation и screenshot/click/keyboard tools.

## 1. Подготовка Windows

Открой Windows Terminal → PowerShell (без «Запуск от администратора»). Если WinGet не установлен — поставь Microsoft App Installer. Затем:

\`\`\`powershell
winget install -e --id Git.Git
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id astral-sh.uv
\`\`\`

**Перезапусти** PowerShell, чтобы обновился PATH. Проверка:

\`\`\`powershell
git --version
node --version
npm.cmd --version
uvx --version
\`\`\`

Codex CLI:

\`\`\`powershell
npm.cmd install -g @openai/codex
codex.cmd --version
codex.cmd
\`\`\`

Войди через поддерживаемый ChatGPT-способ или другой предлагаемый способ. Отдельный API key не обязателен, если используешь поддерживаемый вход через ChatGPT.

**Ошибка \`codex.ps1\` заблокирован Execution Policy:** PowerShell иногда находит npm wrapper \`codex.ps1\`. Используй **\`codex.cmd\`**, не меняй системную Execution Policy. В JARVIS скрипт также выбирает исполняемый \`.exe\` или \`.cmd\`.

## 2. Установи JARVIS

\`\`\`powershell
git clone https://github.com/ggnomer123s/Codex-jarvis.git
cd Codex-jarvis
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1
\`\`\`

Здесь \`ExecutionPolicy Bypass\` действует только для **дочернего процесса**, а не всей ОС. Изучи скрипт перед запуском.

Установщик:
1. Сохраняет уже настроенный \`windows-mcp\`, если он есть; иначе добавляет \`codex mcp add windows-mcp -- uvx windows-mcp serve\` с ограничением PowerShell/Registry/Process/FileSystem/Clipboard tools.
2. Создаёт \`%USERPROFILE%\.local\bin\jarvis.cmd\` и \`jarvis.ps1\`, добавляет каталог к User PATH.
3. Добавляет правила в \`%USERPROFILE%\.codex\AGENTS.md\` с резервной копией старых правил.
4. Копирует \`skills/jarvis-desktop/SKILL.md\` в \`%USERPROFILE%\.agents\skills\jarvis-desktop\`.
5. По умолчанию **не включает** фоновый мониторинг событий.

**Закрой и заново открой PowerShell**, затем:

\`\`\`powershell
jarvis
\`\`\`

## 3. MCP диагностика

\`\`\`powershell
codex.cmd mcp list
codex.cmd mcp get windows-mcp
jarvis status
\`\`\`

Внутри Codex отправь: «Самостоятельно найди GUI MCP, прочитай активное окно и сделай screenshot. Открой Notepad, через GUI введи JARVIS_ONLINE, проверь текст. Не сохраняй файлы и ничего не меняй».

Windows-MCP при первом старте может подгружать Python-зависимости; в upstream указано Python 3.13+. Если \`uvx windows-mcp serve\` падает, сперва проверь \`uvx windows-mcp serve --help\`, версию Python и полный путь к \`uvx.exe\`. Не пытайся запускать Windows-MCP из Linux/WSL для native desktop.

## 4. Опциональный автоматический монитор

Монитор отслеживает **только Windows Application Error события**, а не вообще все сбои приложений, драйверов и ядра. Запускать его стоит лишь когда тебя устраивает отправка части данных Event Log в Codex для AI-анализа.

\`\`\`powershell
# В каталоге Codex-jarvis:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1 -EnableMonitor
\`\`\`

Появится пользовательская Scheduled Task \`JARVIS-Codex-Watch\`, опрашивающая Application Error раз в 5 минут. Отчёты хранятся в \`%LOCALAPPDATA%\jarvis-codex\reports\`. Это **read-only диагностика**, не auto-fix.

\`\`\`powershell
jarvis reports
jarvis monitor off
jarvis monitor on
\`\`\`

На некоторых корпоративных Windows создание Scheduled Task может быть запрещено — GUI-ассистент от этого не ломается.

## 5. Настройка и безопасность

Новый MCP сервер запускается локально по **stdio** — сетевой порт для него не нужен. Для базовой безопасности установщик исключает Windows-MCP tools \`PowerShell,Registry,Process,FileSystem,Clipboard\`. Однако через мышь/клавиатуру агент всё ещё может менять состояние приложения: \`--sandbox read-only\` в Codex контролирует shell, но не гарантирует запрет GUI-кликов. Не запускай от администратора и не вводи через агента пароли.

Проверь перечень исключений в \`codex mcp get windows-mcp\`. Существующее подключение не переписывается автоматически.

## 6. Troubleshooting

- \`jarvis : term is not recognized\` — открой новый PowerShell, проверь \`%USERPROFILE%\.local\bin\jarvis.cmd\` и User PATH.
- \`codex.ps1 cannot be loaded\` — пользуйся \`codex.cmd\`.
- \`Connection closed\` — \`codex.cmd mcp get windows-mcp\`, \`uvx windows-mcp serve --help\`, проверь PATH и Python 3.13+; иногда помогает полный путь к \`uvx.exe\`.
- Skill не найден — открой новую сессию Codex; проверь файл \`%USERPROFILE%\.agents\skills\jarvis-desktop\SKILL.md\`.
- Ничего не кликает — проверь доступность Windows UI Automation, ограничения пользователя и MCP permissions. **Не отключай UAC и антивирус**.
- Аварийная остановка GUI: Ctrl+C в Codex, затем завершение сессии. Windows-MCP — stdio subprocess Codex, не отдельный фоновый сетевой сервер.

Upstream: [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) · [Codex CLI](https://github.com/openai/codex) · [uv](https://docs.astral.sh/uv/getting-started/installation/).
