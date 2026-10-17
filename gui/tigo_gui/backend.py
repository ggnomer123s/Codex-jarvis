"""Qt coordinator for persistent Codex, local voice and checked desktop actions."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
import sys
import uuid

from PySide6.QtCore import QObject, Property, QProcess, QProcessEnvironment, QSettings, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QFileDialog

from .app_server import AppServer, terminate_tree
from .core import find_codex, launch_command, thread_options, turn_options
from .messages import Messages
from .voice import dependencies_available
from .preferences import LANGUAGES, VOICE_MODELS, REASONING, cached_models, elevated, valid_model_id, valid_voice_model
from .profiles import FullProfile
from .runtime import Checkpoints, Profiler
from .workflows import WorkflowRunner, match_workflow, validate_workflows
from .wake_control import WakeControl
from .access import codex_home, access_file, read_access, write_access
from .history import History
from .attachments import inspect_file, validate_files, MAX_FILES
from .speech import Speech
from .desktop_control import control_summary
from .interface_tools import interface_summary
from .screen_activity import ScreenActivity
from .updates import Updates
from .compat import desktop_settings, environment, existing_path, LEGACY


class Backend(QObject):
    changed = Signal()
    conversationFontSizeChanged = Signal()
    layoutChanged = Signal()
    historyChanged = Signal()
    attachmentsChanged = Signal()
    noticeChanged = Signal()
    draftRequested = Signal(str)
    messagesChanged = Signal()
    transcriptReady = Signal(str)
    transcriptPreview = Signal(str)

    def __init__(self, settings=None, *, codex_command=None, voice_command=None, codex_home_override=None, start_hidden=False, tray_available=False, access_path=None, speech_engine_factory=None):
        super().__init__()
        self.settings = settings if settings is not None else desktop_settings()
        self._reduced_motion = str(self.settings.value('reducedMotion', 'false')).lower() == 'true'
        try:
            font_size = int(self.settings.value("conversationFontSize", 14))
        except (TypeError, ValueError):
            font_size = 14
        self._conversation_font_size = max(12, min(28, font_size))
        self._chat_only = str(self.settings.value('chatOnly', 'false')).lower() == 'true'
        self._show_core = str(self.settings.value('showCore', 'true')).lower() == 'true'
        try:
            self._chat_width = max(420, min(1000, int(self.settings.value('chatWidth', 600))))
        except (ValueError, TypeError):
            self._chat_width = 600
        self._attachments = []
        self._turn_attachments = []
        self._conversation_id = str(uuid.uuid4())
        self._history_query = ''
        self._conversation_title = 'New conversation'
        self._notice = ''
        self._desktop_control_status = 'Not checked. Full Access and desktop ownership are separate.'
        self.screen_activity = ScreenActivity(self)
        self._start_hidden = start_hidden
        self._tray_available = tray_available
        self.wake_control = WakeControl(self.settings, self)
        self.speaker = Speech(self.settings, self, prepare=self._prepare_speech, engine_factory=speech_engine_factory)
        self.speaker.changed.connect(self.changed.emit)
        self._speech_handoff = ''
        self._speech_start_row = 0
        self._speech_completed = set()
        saved = str(self.settings.value("folder", str(Path.home())))
        self._folder = saved if Path(saved).is_dir() else str(Path.home())
        self._effort = str(self.settings.value("effort", "low"))
        self._access_path = Path(access_path) if access_path else (Path(settings.fileName()).with_suffix(".access") if settings is not None else access_file())
        self._access = read_access(self._access_path)
        if self._effort not in REASONING:
            self._effort = "low"
        self._model = str(self.settings.value("model", ""))
        if not valid_model_id(self._model):
            self._model = ""
        self._language = str(self.settings.value("language", environment("VOICE_LANGUAGE") or "auto"))
        if self._language not in dict(LANGUAGES):
            self._language = "auto"
        self._voice_model = str(self.settings.value("voiceModel", environment("VOICE_MODEL", "small")))
        if not valid_voice_model(self._voice_model):
            self._voice_model = "base"
        self._transcription_provider = str(self.settings.value("transcriptionProvider", "local"))
        if self._transcription_provider not in ("local", "online"):
            self._transcription_provider = "local"
        self._voice_auto_send = str(self.settings.value("voiceAutoSend", "false")).lower() == "true"
        try:
            self._voice_silence_ms = max(800, min(4000, int(self.settings.value("voiceSilenceMs", 1600))))
        except (TypeError, ValueError):
            self._voice_silence_ms = 1600
        self._draft_present = False
        self._voice_auto_blocked = False
        self._record_auto_send = False
        self._pending_voice_submit = None
        self._shutting_down = False
        self._wake_record_token = 0
        self._auto_reasoning = str(self.settings.value("autoReasoning", "false")).lower() == "true"
        try:
            beam = int(self.settings.value("voiceBeam", 3))
        except (TypeError, ValueError):
            beam = 3
        self._voice_options = {"device": str(self.settings.value("voiceDevice", "cpu")),
                               "beam": beam,
                               "preview": str(self.settings.value("voicePreview", "true")).lower() == "true",
                               "microphone": str(self.settings.value("microphone", ""))}
        if self._voice_options["device"] not in ("cpu", "cuda"):
            self._voice_options["device"] = "cpu"
        if self._voice_options["beam"] not in (1, 3, 5):
            self._voice_options["beam"] = 3
        self._normal_home = Path(codex_home_override) if codex_home_override else codex_home()
        self._models = cached_models(self._normal_home)
        self._model_efforts = {}
        self._codex = environment("GUI_CODEX") or find_codex() or ""
        self._codex_command = codex_command
        if codex_command:
            self._codex = codex_command[0]
        python = str(Path(sys.executable).with_name("python.exe")) if os.name == "nt" else sys.executable
        self._voice_command = voice_command or [python, "-u", "-m", "tigo_gui.voice"]
        self._busy = False
        self._stage = "idle"
        self._voice_state = "idle"
        self._voice_ready = False
        self._level = 0.0
        self._activity = "Ready when you are" if self._codex else "Install Codex CLI to connect"
        self.chat = Messages(self)
        self._messages = self.chat.items
        self._preferences_error = ""
        self._thread_id = ""
        self._thread_loaded = False
        self._turn_id = ""
        self._retired_turns = set()
        self._epoch = 0
        self._task_id = ""
        self._cancelled = False
        self._completed_steps = 0
        self._needs_deep = False
        self._server_waiters = []
        self._item_rows = {}
        self._pending_text = {}
        self._mcp_status = "Not inspected yet"
        self._interface_status = "Not inspected yet"
        self._voice_id = ""
        self._voice_buffer = b""
        self._voice_stop_requested = False
        self._voice_cancelled = False
        self._microphones = [{"id": "", "label": "System default"}]
        self._workflows_text = str(self.settings.value("workflows", "[]"))
        try:
            self._workflows = validate_workflows(self._workflows_text)
        except ValueError:
            self._workflows = []
        self.profiler = Profiler()
        self.checkpoints = Checkpoints(self.settings)
        self.server = AppServer(self)
        self.process = self.server.process
        self.server.ready.connect(self._server_ready)
        self.server.notification.connect(self._notification)
        self.server.failed.connect(self._server_failed)
        self.server.disconnected.connect(self._disconnected)
        self.runner = WorkflowRunner(self.server, self.profiler, self)
        self.runner.desktopEvent.connect(self.screen_activity.handle_item)
        self.runner.progress.connect(self._workflow_progress)
        self.runner.finished.connect(self._workflow_finished)
        self.voice = QProcess(self)
        self.voice.started.connect(self._voice_started)
        self.voice.readyReadStandardOutput.connect(self._read_voice)
        self.voice.readyReadStandardError.connect(lambda: self.voice.readAllStandardError())
        self.voice.finished.connect(self._voice_finished)
        self.voice.errorOccurred.connect(self._voice_error)
        self._stop_timer = QTimer(self)
        self._stop_timer.setSingleShot(True)
        self._stop_timer.timeout.connect(self._force_stop)
        self._stream_timer = QTimer(self)
        self._stream_timer.setSingleShot(True)
        self._stream_timer.setInterval(33)
        self._stream_timer.timeout.connect(self._flush_text)
        self._voice_idle_timer = QTimer(self)
        self._voice_idle_timer.setSingleShot(True)
        self._voice_idle_timer.setInterval(300000)
        self._voice_idle_timer.timeout.connect(self._close_voice)
        self._ui_tick = QTimer(self)
        self._ui_tick.setInterval(1000)
        self._ui_tick.timeout.connect(self.changed.emit)
        self.profile = FullProfile(self._codex_launch, self, home=self._normal_home)
        self.updater = Updates(self)
        self.profile.changed.connect(self.changed.emit)
        self.profile.error.connect(lambda text: self._message("error", text))
        self.changed.connect(lambda: self.wake_control.set_suspended(self._shutting_down or self._voice_state != "idle" or self.speaker.active or self._busy))
        self.wake_control.activated.connect(self._on_wake_activated)
        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(lambda: self._show_notice(''))
        self._history_timer = QTimer(self)
        self._history_timer.setSingleShot(True)
        self._history_timer.setInterval(750)
        self._history_timer.timeout.connect(self._save_history)
        self.history = None
        history_path = Path(settings.fileName()).with_suffix('.history.sqlite3') if settings is not None else existing_path(
            access_file().parent.parent / 'tigo-codex/conversations.sqlite3',
            access_file().parent.parent / (LEGACY + '-codex/conversations.sqlite3'))
        try:
            self.history = History(history_path, self._normal_home)
        except (OSError, ValueError, sqlite3.Error) as exc:
            self._show_notice('Local history unavailable: ' + str(exc))
        self.messagesChanged.connect(self._queue_history)


    @Property("QVariantList", notify=messagesChanged)
    def messages(self):
        return self._messages

    @Property(int, notify=conversationFontSizeChanged)
    def conversationFontSize(self):
        return self._conversation_font_size

    @Slot(int)
    def setConversationFontSize(self, size):
        size = max(12, min(28, size))
        if size != self._conversation_font_size:
            self._conversation_font_size = size
            self.settings.setValue("conversationFontSize", size)
            self.conversationFontSizeChanged.emit()

    @Property(bool, notify=layoutChanged)
    def chatOnly(self):
        return self._chat_only

    @Property(bool, notify=layoutChanged)
    def showCore(self):
        return self._show_core

    @Property(int, notify=layoutChanged)
    def chatWidth(self):
        return self._chat_width

    @Slot(bool)
    def setChatOnly(self, value):
        self._chat_only = value
        self.settings.setValue('chatOnly', value)
        self.layoutChanged.emit()

    @Slot(bool)
    def setShowCore(self, value):
        self._show_core = value
        self.settings.setValue('showCore', value)
        self.layoutChanged.emit()

    @Slot(int)
    def setChatWidth(self, value):
        self._chat_width = max(420, min(1000, value))
        self.settings.setValue('chatWidth', self._chat_width)

    @Property(str, notify=noticeChanged)
    def notice(self):
        return self._notice

    @Property(QObject, constant=True)
    def updates(self):
        return self.updater

    @Property(bool, notify=layoutChanged)
    def reducedMotion(self):
        return self._reduced_motion

    @Slot(bool)
    def setReducedMotion(self, value):
        self._reduced_motion = value
        self.settings.setValue('reducedMotion', value)
        self.layoutChanged.emit()

    @Slot(bool)
    def installUpdate(self, has_draft=False):
        if self._locked() or self._attachments or has_draft:
            self._show_notice('Finish the current task and save or clear the draft and attachments before updating.')
            return
        self.speaker.stop()
        self.updater.install()

    @Slot()
    def dismissNotice(self):
        self._notice_timer.stop()
        self._show_notice('')

    def _show_notice(self, text):
        self._notice = text
        self.noticeChanged.emit()
        if text:
            self._notice_timer.start(6000)

    @Slot(str)
    def copyText(self, text):
        QGuiApplication.clipboard().setText(text)
        self._show_notice('Copied to clipboard')

    @Slot(str)
    def openLink(self, value):
        url = QUrl(value)
        if url.isValid() and url.scheme().lower() in ('http', 'https'):
            QDesktopServices.openUrl(url)

    @Property('QVariantList', notify=attachmentsChanged)
    def attachments(self):
        return self._attachments

    @Slot('QVariantList', result=bool)
    def addAttachments(self, urls):
        if self._locked():
            return False
        try:
            added = []
            paths = {x['path'] for x in self._attachments}
            for url in urls:
                item = inspect_file(url)
                if item['path'] not in paths:
                    paths.add(item['path'])
                    added.append(item)
            if len(self._attachments) + len(added) > MAX_FILES:
                raise ValueError('Attach up to 10 files per request.')
        except (OSError, ValueError) as exc:
            self._show_notice('Could not attach file: ' + str(exc))
            return False
        self._attachments.extend(added)
        self.attachmentsChanged.emit()
        return True

    @Slot()
    def chooseAttachments(self):
        if not self._locked():
            paths, _ = QFileDialog.getOpenFileNames(None, 'Attach local files', self._folder)
            self.addAttachments(paths)

    @Slot()
    def pasteImage(self):
        if self._locked():
            return
        image = QGuiApplication.clipboard().image()
        if image.isNull():
            self._show_notice('No image in clipboard. Copy a screenshot first.')
            return
        if len(self._attachments) >= MAX_FILES or image.width()*image.height() > 20_000_000:
            self._show_notice('Image too large or attachment limit reached.')
            return
        try:
            folder = (self.history.path.parent if self.history else self._access_path.parent) / 'attachments'
            folder.mkdir(parents=True, exist_ok=True, mode=0o700)
            path = folder / ('screenshot-' + str(uuid.uuid4()) + '.png')
            if not image.save(str(path), 'PNG'):
                raise ValueError('Could not save clipboard image.')
            path.chmod(0o600)
            if not self.addAttachments([str(path)]):
                path.unlink(missing_ok=True)
            else:
                self._attachments[-1]['clipboard'] = True
        except (OSError, ValueError) as exc:
            self._show_notice('Could not paste image: ' + str(exc))

    @Slot(int)
    def removeAttachment(self, index):
        if not self._locked() and 0 <= index < len(self._attachments):
            removed = self._attachments.pop(index)
            self._clean_clipboard_images([removed])
            self.attachmentsChanged.emit()

    def _clean_clipboard_images(self, files):
        folder = ((self.history.path.parent if self.history else self._access_path.parent) / 'attachments').resolve()
        for item in files:
            if not item.get('clipboard') or any(x['path'] == item['path'] for x in self._attachments):
                continue
            path = Path(item['path'])
            try:
                if path.parent.resolve() == folder and path.name.startswith('screenshot-') and self.history and not self.history.references(str(path)):
                    path.unlink(missing_ok=True)
            except (OSError, sqlite3.Error):
                pass  # Retain a cache file if its history reference cannot be checked.

    @Slot(int)
    def editMessage(self, index):
        if self._locked() or not 0 <= index < len(self._messages):
            return
        item = self._messages[index]
        if item['role'] != 'user':
            return
        notice = 'Edit the draft, then Send as a new request. Earlier actions remain.'
        try:
            attached = validate_files(item.get('attachments', []))
        except (OSError, ValueError, KeyError) as exc:
            notice = 'Reattach unavailable files before sending: ' + str(exc)
            attached = []
        pending, self._attachments = self._attachments, attached
        self._clean_clipboard_images(pending)
        self.attachmentsChanged.emit()
        self.draftRequested.emit(item['text'])
        self._show_notice(notice)

    def _queue_history(self):
        if self.history and not self._history_timer.isActive():
            self._history_timer.start()

    def _save_history(self):
        self._history_timer.stop()
        if not self.history:
            return
        try:
            self.history.save(self._conversation_id, self._folder, self._model, self._access,
                              self._thread_id, 'running' if self._busy else self._stage, self._messages)
            self.historyChanged.emit()
        except (OSError, ValueError, sqlite3.Error) as exc:
            self._show_notice('Could not save local history: ' + str(exc))

    @Property(str, notify=historyChanged)
    def conversationTitle(self):
        return self._conversation_title

    @Property('QVariantList', notify=historyChanged)
    def historyEntries(self):
        if not self.history:
            return []
        try:
            return self.history.list(self._history_query)
        except sqlite3.Error:
            return []

    @Slot(str)
    def searchHistory(self, text):
        self._history_query = text[:200]
        self.historyChanged.emit()

    @Slot(str, bool)
    def pinConversation(self, key, pinned):
        if self.history:
            try:
                self.history.update(key, pinned=pinned)
                self.historyChanged.emit()
            except sqlite3.Error as exc:
                self._show_notice('Could not pin conversation: ' + str(exc))

    @Slot(str, str)
    def renameConversation(self, key, title):
        if self.history and title.strip():
            try:
                self.history.update(key, title=title)
                if key == self._conversation_id:
                    self._conversation_title = title.strip()[:120]
                self.historyChanged.emit()
            except sqlite3.Error as exc:
                self._show_notice('Could not rename conversation: ' + str(exc))

    @Slot(str)
    def deleteConversation(self, key):
        if self.history and not self._locked():
            try:
                try:
                    previous = self.history.load(key)
                except ValueError:
                    previous = None
                self.history.delete(key)
                if key == self._conversation_id:
                    self._conversation_id = ''
                    self._reset_context()
                self._clean_clipboard_images([file for message in (previous or {}).get('messages', []) for file in message.get('attachments', [])])
                self.historyChanged.emit()
            except (ValueError, sqlite3.Error) as exc:
                self._show_notice('Could not delete conversation: ' + str(exc))

    @Slot(str, result=bool)
    def openConversation(self, key):
        if not self.history or self._locked():
            return False
        try:
            value = self.history.load(key)
            if not value:
                raise ValueError('Conversation no longer exists.')
            if value['access'] != self._access:
                raise ValueError('Choose the same access mode in Preferences before continuing this conversation.')
            thread_options(value['folder'], self._access, value['model'])
        except (OSError, ValueError, sqlite3.Error) as exc:
            self._show_notice('Could not open conversation: ' + str(exc))
            return False
        self._reset_context()
        self._conversation_id = value['id']
        self._conversation_title = value['title']
        self._folder, self._model = value['folder'], value['model']
        self.settings.setValue('folder', self._folder)
        self.settings.setValue('model', self._model)
        self._thread_id, self._thread_loaded = value['thread'], False
        for message in value['messages']:
            self.chat.append(message['role'], message['text'], message.get('attachments'))
        pending, self._attachments = self._attachments, []
        self._clean_clipboard_images(pending)
        self.attachmentsChanged.emit()
        self.messagesChanged.emit()
        self._activity = 'Conversation restored. Send a message to continue.'
        if not self._thread_id:
            self._show_notice('Local transcript restored; the next request starts a new Codex session.')
        self.historyChanged.emit()
        self.changed.emit()
        return True

    @Property('QVariantMap', notify=changed)
    def taskStatus(self):
        labels = {'connecting':'Connecting', 'planning':'Thinking', 'acting':'Using tools',
                  'verifying':'Checking results', 'complete':'Completed', 'failed':'Failed',
                  'stopping':'Stopping', 'stopped':'Stopped', 'idle':'Ready'}
        title = labels.get(self._stage, 'Working')
        if self._busy and self._activity == 'Writing the answer':
            title = 'Writing reply'
        if self._voice_state != 'idle':
            title = 'Voice: ' + self._voice_state
        detail = self._activity
        if self.speaker.active and not self._busy and self._voice_state == 'idle':
            title, detail = 'Speaking', self.speaker.status
        if self._stage == 'failed' and not self.speaker.active and self._voice_state == 'idle':
            detail = next((x['text'] for x in reversed(self._messages) if x['role']=='error'), detail)
        current = self.profiler.current
        last = self.profiler.history[-1] if self.profiler.history else None
        seconds = (self.profiler.clock() - self.profiler._started) if current else ((last or {}).get('durationMs',0)/1000)
        return {'title':title, 'detail':detail[:500], 'elapsed':f'{int(seconds)//60}:{int(seconds)%60:02d}' if self._voice_state == 'idle' and self._stage != 'idle' and not self.speaker.active else '',
                'busy':self._busy, 'state':self._stage}


    @Property(QObject, constant=True)
    def speech(self):
        return self.speaker

    def _prepare_speech(self, callback):
        if self._voice_state != 'idle' or self.profile.busy:
            self.speaker.stop()
            return
        self.wake_control.reserve_microphone(callback)

    @Slot(int)
    def readMessage(self, index):
        if not self._locked() and 0 <= index < len(self._messages):
            message = self._messages[index]
            if message['role'] == 'assistant':
                self.speaker.read(message['text'])

    @Slot()
    def testSpeech(self):
        if not self._locked():
            voice = self.speaker.voice
            russian = voice.startswith('ru_') or (voice in ('', 'auto:female') and self._language != 'en')
            self.speaker.read('Здравствуйте, наставник. Я Тиго. Проверим естественную речь.' if russian
                              else 'Hello, mentor. I am Tigo. Let us check my voice.')

    @Property(QObject, constant=True)
    def wake(self):
        return self.wake_control

    @Property(bool, constant=True)
    def startHidden(self):
        return self._start_hidden

    @Property(bool, constant=True)
    def trayAvailable(self):
        return self._tray_available

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def activity(self):
        return self._activity

    @Property(str, notify=changed)
    def folder(self):
        return self._folder

    @Property(str, notify=changed)
    def effort(self):
        return self._effort

    @Property(str, notify=changed)
    def access(self):
        return self._access

    @Property(str, notify=changed)
    def normalAccess(self):
        saved = str(self.settings.value("access", "read-only"))
        return saved if saved in ("read-only", "workspace-write") else "read-only"

    @Property(bool, notify=changed)
    def fullAccess(self):
        return self._access == "full-access"

    @Property(QObject, constant=True)
    def fullProfile(self):
        return self.profile

    @Property(str, notify=changed)
    def model(self):
        return self._model

    @Property("QStringList", notify=changed)
    def models(self):
        names = list(self._models)
        if self._model and self._model not in names:
            names.append(self._model)
        return ["Codex default", *names]

    @Property("QVariantList", notify=changed)
    def reasoningOptions(self):
        known = self._model_efforts.get(self._model)
        choices = known if known is not None else ("low", "medium", "high", "xhigh")
        labels = {"default": "Model default", "none": "None", "minimal": "Minimal", "low": "Low", "medium": "Medium", "high": "High", "xhigh": "Extra high"}
        return [{"code": key, "label": labels[key]} for key in REASONING if key == "default" or key in choices]

    @Slot(str, result=bool)
    def selectModel(self, model):
        model = "" if model.strip() == "Codex default" else model.strip()
        effort = self._effort
        supported = self._model_efforts.get(model)
        if supported is not None and effort not in supported:
            effort = "default"
        return self.savePreferences(effort, self._access, model, self._language, self._voice_model)

    @Slot(str, result=bool)
    def selectReasoning(self, effort):
        supported = self._model_efforts.get(self._model)
        if supported is not None and effort != "default" and effort not in supported:
            return self._settings_error("This model does not advertise that reasoning level.")
        return self.savePreferences(effort, self._access, self._model, self._language, self._voice_model)

    @Property(str, notify=changed)
    def language(self):
        return self._language

    @Property("QVariantList", constant=True)
    def languageOptions(self):
        return [{"code": code, "label": label} for code, label in LANGUAGES]

    @Property(str, notify=changed)
    def voiceModel(self):
        return self._voice_model

    @Property("QStringList", constant=True)
    def voiceModels(self):
        return VOICE_MODELS

    @Property(str, notify=changed)
    def preferencesError(self):
        return self._preferences_error

    def _settings_error(self, text):
        self._preferences_error = text
        self._message("error", text)
        self.changed.emit()
        return False

    @Property(bool, notify=changed)
    def codexAvailable(self):
        return bool(self._codex)

    @Property(bool, notify=changed)
    def voiceAvailable(self):
        return dependencies_available() if self._transcription_provider == "local" else dependencies_available("online")

    @Property(bool, notify=changed)
    def voiceAutoSend(self):
        return self._voice_auto_send

    @Property(int, notify=changed)
    def voiceSilenceMs(self):
        return self._voice_silence_ms

    @Slot(bool, int, result=bool)
    def saveVoiceAutomation(self, auto_send, silence_ms):
        if self._locked():
            return False
        if type(silence_ms) is not int or not 800 <= silence_ms <= 4000:
            return self._settings_error("Choose a speech pause between 0.8 and 4 seconds.")
        self._voice_auto_send, self._voice_silence_ms = auto_send, silence_ms
        self.settings.setValue("voiceAutoSend", auto_send)
        self.settings.setValue("voiceSilenceMs", silence_ms)
        self.changed.emit()
        return True

    @Slot(bool)
    def updateDraftState(self, present):
        self._draft_present = present
        if self._voice_state != "idle":
            self._voice_auto_blocked = True

    def _on_wake_activated(self):
        if not self.wake_control.recordAfterWake or self._locked() or self._shutting_down:
            return
        self._wake_record_token += 1
        token = self._wake_record_token
        # App's wake slot shows the window synchronously; capture starts next tick.
        def record():
            if token == self._wake_record_token and self.wake_control.enabled and self.wake_control.recordAfterWake and not self._locked() and not self._shutting_down:
                self.toggleVoice()
        QTimer.singleShot(0, record)

    @Property(str, notify=changed)
    def transcriptionProvider(self):
        return self._transcription_provider

    @Slot(str, result=bool)
    def saveTranscriptionPreferences(self, provider):
        if self._locked():
            return False
        if provider not in ("local", "online"):
            return self._settings_error("Choose Local Whisper or Online Google Web Speech.")
        if provider != self._transcription_provider:
            self._close_voice()
        self._transcription_provider = provider
        self.settings.setValue("transcriptionProvider", provider)
        self.changed.emit()
        return True

    @Property(str, notify=changed)
    def voiceState(self):
        return self._voice_state

    @Property(float, notify=changed)
    def audioLevel(self):
        return self._level

    @Property(QObject, constant=True)
    def messageModel(self):
        return self.chat

    @Property(str, notify=changed)
    def stage(self):
        if self.speaker.active and not self._busy and self._voice_state == "idle":
            return "speaking"
        return self._voice_state if self._voice_state != "idle" else self._stage

    @Property(bool, notify=changed)
    def serverReady(self):
        return self.server.connected

    @Property(bool, notify=changed)
    def voiceReady(self):
        return self._voice_ready

    @Property(str, notify=changed)
    def metricsSummary(self):
        return self.profiler.summary()

    @Property(str, notify=changed)
    def runtimeDetails(self):
        voice = json.dumps(self.profiler.voice, indent=2)
        return (f"Codex app-server: {'connected' if self.server.connected else 'not connected'}\n"
                f"Desktop MCP: {self._mcp_status}\nInterface structure: {self._interface_status}\nWindows desktop: {self._desktop_control_status}\nTask: {self.profiler.summary()}\n"
                f"Verified/completed steps: {self._completed_steps}\nDictation timings (ms):\n{voice}")

    @Property(bool, constant=True)
    def windowsDesktop(self):
        return os.name == 'nt'

    @Property(str, notify=changed)
    def desktopControlStatus(self):
        return self._desktop_control_status

    @Slot()
    def checkDesktopControl(self):
        if self._locked():
            return
        self._desktop_control_status = 'Checking Windows-MCP ownership (read only)...'
        self._begin('desktop-check')

        def failed(message):
            self._finish('failed', message)

        def returned(result, error):
            if error:
                failed('Control status unavailable: ' + error)
                return
            try:
                self._desktop_control_status = control_summary(result)
            except ValueError as exc:
                failed(str(exc))
                return
            self._finish('completed')

        def inventory(cursor=None, pages=0):
            params = {'threadId': self._thread_id, 'limit': 100}
            if cursor:
                params['cursor'] = cursor

            def listed(result, error):
                if error:
                    failed('Desktop inventory unavailable: ' + error)
                    return
                servers = result.get('data', []) if isinstance(result, dict) else []
                if not isinstance(servers, list):
                    failed('Desktop inventory returned an invalid server list.')
                    return
                server = next((x for x in servers if isinstance(x, dict) and x.get('name') == 'windows-mcp'), None)
                if server is None:
                    cursor = result.get('nextCursor') if isinstance(result, dict) else None
                    if isinstance(cursor, str) and cursor and pages < 4:
                        inventory(cursor, pages + 1)
                    else:
                        failed('windows-mcp was not reported. Check its registration in your existing Codex profile.')
                    return
                tools = server.get('tools', {})
                available = 'ControlStatus' in tools if isinstance(tools, dict) else (
                    isinstance(tools, list) and any(isinstance(x, dict) and x.get('name') == 'ControlStatus' for x in tools))
                if not available:
                    failed('This windows-mcp does not expose ControlStatus. Check its version and tool exclusions; no fallback input was attempted.')
                    return
                self._activity, self._stage = 'Reading Windows desktop ownership', 'verifying'
                self.changed.emit()
                self.server.request('mcpServer/tool/call', {'threadId': self._thread_id, 'server': 'windows-mcp',
                                    'tool': 'ControlStatus', 'arguments': {}}, self._guard(returned), 15000)

            self.server.request('mcpServerStatus/list', params, self._guard(listed), 15000)

        self._ensure_server(lambda: self._ensure_thread(inventory))

    @Property(bool, notify=changed)
    def canResume(self):
        return bool(self.checkpoints.get(self._checkpoint_key())) and not self._locked()

    @Property(str, notify=changed)
    def workflowsText(self):
        return self._workflows_text

    @Property(bool, notify=changed)
    def autoReasoning(self):
        return self._auto_reasoning

    @Property(str, notify=changed)
    def voiceDevice(self):
        return self._voice_options["device"]

    @Property(int, notify=changed)
    def voiceBeam(self):
        return self._voice_options["beam"]

    @Property(bool, notify=changed)
    def voicePreview(self):
        return self._voice_options["preview"]

    @Property(str, notify=changed)
    def microphone(self):
        return self._voice_options["microphone"]

    @Property("QVariantList", notify=changed)
    def microphones(self):
        names = list(self._microphones)
        selected = self._voice_options["microphone"]
        if selected and not any(x["id"] == selected for x in names):
            names.append({"id": selected, "label": "Saved microphone " + selected})
        return names

    def _checkpoint_key(self):
        home = self._normal_home
        return Checkpoints.key(home, Path(self._folder), self._access, self._model)

    def _message(self, role, text, attachments=None):
        self.chat.append(role, text, attachments)
        if role == 'user' and self._conversation_title == 'New conversation':
            self._conversation_title = text.strip().split('\n')[0][:100]
            self.historyChanged.emit()
        self.messagesChanged.emit()

    def _codex_launch(self, args):
        if not self._codex:
            raise ValueError("Codex CLI was not found. Install it and reopen Tigo.")
        if self._codex_command:
            return self._codex_command[0], self._codex_command[1:] + args
        return launch_command(self._codex, args)

    def _locked(self):
        return self._busy or self._voice_state != "idle" or self.profile.busy or self.updater.installing

    def _guard(self, callback):
        epoch, task = self._epoch, self._task_id
        def guarded(result, error):
            if epoch == self._epoch and task == self._task_id:
                callback(result, error)
        return guarded

    def _ensure_server(self, callback):
        if self.server.connected:
            self.profiler.mark("serverReady")
            callback()
            return
        self._server_waiters.append((self._epoch, callback))
        if self.process.state() == QProcess.ProcessState.NotRunning:
            try:
                program, args = self._codex_launch(["app-server", "--listen", "stdio://"])
            except ValueError as exc:
                self._server_failed(str(exc))
                return
            environment = QProcessEnvironment.systemEnvironment()
            environment.insert("CODEX_HOME", str(self._normal_home))
            self.server.start(program, args, environment, self._folder)
        self.changed.emit()

    def _server_ready(self):
        self.profiler.mark("serverReady")
        self._fetch_models()
        waiters, self._server_waiters = self._server_waiters, []
        for epoch, callback in waiters:
            if epoch == self._epoch:
                callback()
        self.changed.emit()

    def _ensure_thread(self, callback, *, restore=False):
        if self._thread_id and self._thread_loaded:
            callback()
            return
        options = thread_options(self._folder, self._access, self._model)
        method = "thread/resume" if self._thread_id else "thread/start"
        if self._thread_id:
            options["threadId"] = self._thread_id
        def ready(result, error):
            if error:
                self._finish("failed", error)
                return
            thread = result.get("thread", {}) if isinstance(result, dict) else {}
            if not isinstance(thread.get("id"), str) or not thread["id"]:
                self._finish("failed", "Codex did not return a valid thread ID.")
                return
            self._thread_id = thread["id"]
            self._thread_loaded = True
            self.profiler.mark("threadReady")
            self.checkpoints.save(self._checkpoint_key(), self._thread_id, "running", self._completed_steps)
            if restore:
                self._restore_chat(thread)
            self._inspect_mcp()
            callback()
        self.server.request(method, options, self._guard(ready), 60000)

    def _inspect_mcp(self):
        epoch = self._epoch
        def returned(result, error):
            if epoch != self._epoch:
                return
            if error:
                self._mcp_status = "Inventory unavailable: " + error
                self._interface_status = "Inventory unavailable"
            else:
                servers = result.get("data", []) if isinstance(result, dict) else []
                self._interface_status = interface_summary(servers)
                self._mcp_status = ", ".join(str(x.get("name", "MCP")) for x in servers if isinstance(x, dict)) or "No desktop servers reported"
            self.changed.emit()
        self.server.request("mcpServerStatus/list", {"threadId": self._thread_id, "limit": 100}, returned)

    def _fetch_models(self):
        epoch = self._epoch
        def returned(result, error):
            if epoch != self._epoch or error or not isinstance(result, dict):
                return
            entries = result.get("data", [])
            if not isinstance(entries, list):
                return
            names = []
            for item in entries:
                if not isinstance(item, dict) or item.get("hidden"):
                    continue
                name = item.get("model", item.get("id", ""))
                if isinstance(name, str) and name and valid_model_id(name) and name not in names:
                    names.append(name)
                    efforts = [x.get("reasoningEffort") for x in item.get("supportedReasoningEfforts", []) if isinstance(x, dict)]
                    self._model_efforts[name] = efforts
                    if item.get("isDefault"):
                        self._model_efforts[""] = efforts
            self._models = names
            supported = self._model_efforts.get(self._model)
            if supported is not None and self._effort != "default" and self._effort not in supported:
                self._effort = "default"
                self.settings.setValue("effort", "default")
            self.changed.emit()
        self.server.request("model/list", {"limit": 100}, returned)

    def _begin(self, kind):
        self.speaker.stop()
        self._speech_start_row = len(self._messages)
        self._speech_completed.clear()
        self.speaker.begin_stream()
        self._task_id = str(uuid.uuid4())
        self._busy = True
        self._cancelled = False
        self._turn_id = ""
        self._task_kind = kind
        self._completed_steps = 0
        self._item_rows = {}
        self._pending_text = {}
        self.profiler.begin(kind)
        self._ui_tick.start()
        self._stage = "connecting"
        self._activity = "Connecting to Codex app-server"
        self.changed.emit()

    @Slot(str, result=bool)
    def send(self, prompt):
        prompt = prompt.strip()
        if (not prompt and not self._attachments) or self._locked():
            return False
        if len(prompt) > 200000:
            self._message("error", "Request is too long.")
            return
        if not self._attachments and self._local_command(prompt):
            return True
        try:
            thread_options(self._folder, self._access, self._model)
            if self.fullAccess and elevated():
                raise ValueError("Full Access must run as a normal user, not root or Administrator.")
            if not self._codex:
                raise ValueError("Install Codex CLI, run codex login, then reopen Tigo.")
        except ValueError as exc:
            self._message("error", str(exc))
            return
        try:
            attached = validate_files(self._attachments)
        except (OSError, ValueError, KeyError) as exc:
            self._show_notice('Could not send attachment: ' + str(exc))
            return False
        prompt = prompt or 'Please inspect the attached files.'
        workflow = None if attached else match_workflow(self._workflows, prompt)
        self._turn_attachments = attached
        self._begin("workflow" if workflow else "codex")
        self._message("user", prompt, attached)
        self._attachments = []
        self.attachmentsChanged.emit()
        if workflow:
            action = lambda: self.runner.start(workflow, self._thread_id)
        else:
            action = lambda: self._start_turn(prompt)
        self._ensure_server(lambda: self._ensure_thread(action))
        return True

    def _chosen_effort(self, prompt):
        effort = self._effort
        if self._auto_reasoning:
            deep = ("debug", "diagnos", "investigat", "architecture", "crash", "ошиб", "диагност", "исслед", "сбой")
            simple = ("open ", "focus ", "play ", "открой", "включи", "переключи")
            if self._needs_deep or any(x in prompt.casefold() for x in deep):
                effort = "high"
            elif any(prompt.casefold().startswith(x) for x in simple):
                effort = "low"
        supported = self._model_efforts.get(self._model)
        return "default" if supported and effort != "default" and effort not in supported else effort

    def _start_turn(self, prompt):
        self._stage = "planning"
        self._activity = "Understanding your request"
        def started(result, error):
            if error:
                if "timed out" in error:
                    # An accepted start may be running after the RPC timed out.
                    self.server.close()
                self._finish("failed", error)
                return
            turn = result.get("turn", {}) if isinstance(result, dict) else {}
            turn_id = turn.get("id")
            if not isinstance(turn_id, str) or not turn_id:
                self._finish("failed", "Codex did not return a valid turn ID.")
                return
            if self._busy:
                self._turn_id = turn_id
                if self._cancelled:
                    self._interrupt()
        self.server.request("turn/start", turn_options(self._thread_id, prompt, self._chosen_effort(prompt), self._model, self._turn_attachments), self._guard(started), 60000)
        self.changed.emit()

    def _notification(self, method, params):
        if method == "tigo/requestDeclined":
            self._message("system", "A request needing additional input/approval was declined. Use the interactive CLI for that request.")
            return
        if not self._busy or self._task_kind != "codex" or params.get("threadId") != self._thread_id:
            return
        turn = params.get("turn", {})
        turn_id = params.get("turnId") or (turn.get("id") if isinstance(turn, dict) else None)
        if (self._epoch, turn_id) in self._retired_turns or (self._turn_id and turn_id and turn_id != self._turn_id):
            return
        if method == "turn/started" and isinstance(turn_id, str):
            self._turn_id = turn_id
        if method == "turn/completed":
            if not self._turn_id and isinstance(turn_id, str):
                self._turn_id = turn_id
            status = turn.get("status", "failed")
            error = turn.get("error")
            message = error.get("message", "Codex turn failed.") if isinstance(error, dict) else ""
            self._finish("interrupted" if self._cancelled else status, message)
            return
        if self._cancelled:
            return
        if method in ('item/started', 'item/completed'):
            self.screen_activity.handle_item(method, params.get('item'))
        if method == "item/agentMessage/delta":
            item_id, delta = params.get("itemId"), params.get("delta")
            if isinstance(item_id, str) and isinstance(delta, str):
                self.profiler.mark("firstText")
                self._activity = "Writing the answer"
                self._pending_text[item_id] = self._pending_text.get(item_id, "") + delta
                if not self._stream_timer.isActive():
                    self._stream_timer.start()
        elif method in ("item/started", "item/completed"):
            item = params.get("item", {})
            if not isinstance(item, dict):
                return
            kind, item_id = item.get("type"), item.get("id", "")
            if kind == "agentMessage" and method == "item/completed":
                self._flush_text()
                text = item.get("text", "")
                if isinstance(text, str):
                    self.profiler.mark("firstText")
                    self._set_item_text(item_id, text, replace=True)
                    # One speech job per completed Copy/Read message card.
                    if item_id not in self._speech_completed:
                        self._speech_completed.add(item_id)
                        self.speaker.enqueue(text)
            elif kind in ("mcpToolCall", "commandExecution", "fileChange", "webSearch"):
                name = str(item.get("tool", kind))
                if method == "item/started":
                    self.profiler.tool_start(item_id, name)
                    self._stage = "acting"
                    self._activity = "Using " + name[:100]
                else:
                    self.profiler.tool_end(item_id)
                    self._completed_steps += 1
                    self.checkpoints.save(self._checkpoint_key(), self._thread_id, "running", self._completed_steps)
                    self._stage = "verifying"
                    self._activity = "Checking task progress"
            elif kind == "reasoning":
                self._stage = "planning"
                self._activity = "Planning the next step"
        elif method == "error" and not params.get("willRetry"):
            error = params.get("error", {})
            self._message("error", str(error.get("message", "Codex reported an error.")))
        self.changed.emit()

    def _set_item_text(self, item_id, text, replace=False):
        row = self._item_rows.get(item_id)
        if row is None:
            row = self.chat.append("assistant", text)
            self._item_rows[item_id] = row
        else:
            previous = self._messages[row]["text"]
            self.chat.update(row, text if replace else previous + text)
        self.messagesChanged.emit()

    def _flush_text(self):
        self._stream_timer.stop()
        values, self._pending_text = self._pending_text, {}
        for item_id, delta in values.items():
            self._set_item_text(item_id, delta)

    def _finish(self, status, error=""):
        if not self._busy:
            return
        self.screen_activity.clear()
        self._stop_timer.stop()
        self._ui_tick.stop()
        self._flush_text()
        if self._turn_id:
            self._retired_turns.add((self._epoch, self._turn_id))
            if len(self._retired_turns) > 100:
                self._retired_turns = {(self._epoch, self._turn_id)}
        self.profiler.finish(status)
        self.checkpoints.save(self._checkpoint_key(), self._thread_id, status, self._completed_steps)
        self._busy = False
        self._task_id = ""
        if self._task_kind == 'desktop-check' and (error or status != 'completed'):
            self._desktop_control_status = 'Check stopped.' if status == 'interrupted' else 'Check unavailable: ' + (error or status)
        if status == "interrupted":
            self._message("system", "Task stopped. Completed actions have not been undone; inspect before resuming.")
            self._stage, self._activity = "stopped", "Task stopped"
        elif error or status == "failed":
            self._message("error", error or "Codex task failed.")
            self._stage, self._activity = "failed", "Request failed"
            if self._task_kind != 'desktop-check':
                self._needs_deep = True
        else:
            self._stage, self._activity = "complete", "Ready when you are"
            if self._task_kind != 'desktop-check':
                self._needs_deep = False
        self._save_history()
        if not error and status == 'completed' and self._task_kind == 'workflow':
            reply = next((m['text'] for m in reversed(self._messages[self._speech_start_row:]) if m['role'] == 'assistant'), '')
            self.speaker.enqueue(reply)
        elif error or status != 'completed' or self._task_kind != 'codex':
            self.speaker.stop()
        self.changed.emit()

    def _server_failed(self, text):
        self._thread_loaded = False
        self._server_waiters = []
        if self._busy:
            self.runner.cancel()
            self._finish("interrupted" if self._cancelled else "failed", text)
        else:
            self._message("error", text)
        self.changed.emit()

    def _disconnected(self):
        self.screen_activity.clear()
        self._thread_loaded = False
        self.changed.emit()

    def _workflow_progress(self, text, count):
        self._completed_steps = count
        self._stage = "verifying" if text.startswith("Verified") else "acting"
        self._activity = text
        self.checkpoints.save(self._checkpoint_key(), self._thread_id, "running", count)
        self.changed.emit()

    def _workflow_finished(self, error, count):
        self._completed_steps = count
        if not error:
            self._message("assistant", f"Workflow completed: {count} steps verified.")
        self._finish("failed" if error else "completed", error)

    def _local_command(self, prompt):
        if not prompt.startswith("/"):
            return False
        commands = {
            "/help": "Local commands: /status, /desktop-status, /metrics, /workflows, /open-workspace, /resume, /new. Exact workflow aliases execute checked desktop steps without model inference.",
            "/status": self.runtimeDetails,
            "/metrics": json.dumps(self.profiler.export(), indent=2),
            "/workflows": "\n".join(item["name"] + ": " + ", ".join(item["aliases"]) for item in self._workflows) or "No workflows saved. Add one in Preferences > Automation.",
        }
        if prompt in commands:
            self._message("system", commands[prompt])
        elif prompt == '/desktop-status':
            self.checkDesktopControl()
        elif prompt == "/open-workspace":
            accepted = QDesktopServices.openUrl(QUrl.fromLocalFile(self._folder))
            self._message("system" if accepted else "error", "Workspace open request accepted by the desktop." if accepted else "The desktop could not open this workspace.")
        elif prompt == "/resume":
            self.resumePrevious()
        elif prompt == "/new":
            self.newSession()
        else:
            return False
        return True

    @Slot()
    def takeControl(self):
        """Human emergency stop: cancel the owned task, not just its indicator."""
        self.screen_activity.clear()
        self.speaker.stop()
        if self._busy:
            self._cancelled = True
            self._force_stop()
        self._show_notice('Control returned to you. Completed actions have not been undone.')

    @Slot()
    def stop(self):
        if not self._busy:
            return
        self._cancelled = True
        self.screen_activity.clear()
        self._stage, self._activity = "stopping", "Stopping task"
        if self.runner.running or not self._turn_id:
            self._force_stop()
        else:
            self._interrupt()
        self.changed.emit()

    def _interrupt(self):
        self.server.request("turn/interrupt", {"threadId": self._thread_id, "turnId": self._turn_id},
                            self._guard(lambda result, error: self._force_stop() if error else None), 2000)
        self._stop_timer.start(2500)

    def _force_stop(self):
        self.runner.cancel()
        self.server.close()
        self._thread_loaded = False
        self._server_waiters = []
        self._finish("interrupted" if self._cancelled else "failed", "Codex connection stopped.")

    def _reset_context(self):
        self.speaker.stop()
        self._save_history()
        self._conversation_id = str(uuid.uuid4())
        self._turn_attachments = []
        self._conversation_title = 'New conversation'
        self.historyChanged.emit()
        self._epoch += 1
        self._task_id = ""
        self._server_waiters = []
        self._thread_id = ""
        self._thread_loaded = False
        self._turn_id = ""
        self._pending_text = {}
        self._item_rows = {}
        self.chat.clear()
        self._mcp_status = "Not inspected yet"
        self._interface_status = "Not inspected yet"
        self._activity, self._stage = "Ready when you are", "idle"
        self.messagesChanged.emit()
        self.changed.emit()

    @Slot()
    def newSession(self):
        if self._locked():
            return
        self.checkpoints.forget(self._checkpoint_key())
        self._reset_context()

    def _restore_chat(self, thread):
        self.chat.clear()
        for turn in thread.get("turns", [])[-8:]:
            for item in turn.get("items", []):
                if item.get("type") == "agentMessage":
                    self.chat.append("assistant", str(item.get("text", "")))
                elif item.get("type") == "userMessage":
                    text = "\n".join(str(x.get("text", "")) for x in item.get("content", []) if x.get("type") == "text")
                    self.chat.append("user", text)
        self.messagesChanged.emit()

    @Slot()
    def resumePrevious(self):
        if self._locked():
            return
        checkpoint = self.checkpoints.get(self._checkpoint_key())
        if not checkpoint:
            self._message("system", "No conversation checkpoint for this workspace, model and access profile.")
            return
        self._reset_context()
        self._thread_id = checkpoint["threadId"]
        self._begin("resume")
        self._ensure_server(lambda: self._ensure_thread(lambda: self._finish("completed"), restore=True))

    @Slot()
    def chooseFolder(self):
        if self._locked():
            return
        folder = QFileDialog.getExistingDirectory(None, "Choose your workspace", self._folder)
        if folder and folder != self._folder:
            self._reset_context()
            self._folder = folder
            self.settings.setValue("folder", folder)
            self.changed.emit()

    @Slot(str, str)
    def configure(self, effort, access):
        return self.savePreferences(effort, access, self._model, self._language, self._voice_model)

    @Slot(str, str, str, str, str, result=bool)
    def savePreferences(self, effort, access, model, language, voice_model):
        if self._locked():
            return False
        model, voice_model = model.strip(), voice_model.strip()
        self._preferences_error = ""
        try:
            thread_options(self._folder, access, model)
            if effort not in REASONING or language not in dict(LANGUAGES) or not valid_voice_model(voice_model):
                raise ValueError("Choose supported reasoning, voice language and multilingual model settings.")
        except ValueError as exc:
            return self._settings_error(str(exc))
        try:
            write_access(self._access_path, access)
        except (OSError, ValueError) as exc:
            return self._settings_error("Could not save access mode: " + str(exc))
        if access != self._access:
            self._reset_context()
            self.server.close()
            self._model_efforts = {}
        elif model != self._model:
            self._reset_context()
        if voice_model != self._voice_model:
            self._close_voice()
        self._effort, self._access = effort, access
        self._model, self._language, self._voice_model = model, language, voice_model
        self.settings.setValue("effort", effort)
        if access != "full-access":
            self.settings.setValue("access", access)
        for key, value in (("model", model), ("language", language), ("voiceModel", voice_model)):
            self.settings.setValue(key, value)
        self._models = cached_models(self._normal_home)
        if self.server.connected:
            self._fetch_models()
        self.changed.emit()
        return True

    @Slot()
    def refreshModels(self):
        if self._locked():
            return
        self._models = cached_models(self._normal_home)
        self._ensure_server(lambda: None)
        if self.server.connected:
            self._fetch_models()
        self.changed.emit()

    @Slot(bool, result=bool)
    def setFullAccess(self, enabled):
        if self._locked():
            return False
        if not enabled:
            self.disableFullAccess()
            return True
        if elevated():
            return self._settings_error("Run Tigo as a normal user before enabling Full Access.")
        return self.savePreferences(self._effort, "full-access", self._model, self._language, self._voice_model)

    @Slot()
    def disableFullAccess(self):
        if self.fullAccess and not self._locked():
            self.configure(self._effort, self.normalAccess)

    @Slot(str, bool, str, int, bool, str, result=bool)
    def saveRuntimePreferences(self, workflows, adaptive, device, beam, preview, microphone):
        if self._locked():
            return False
        try:
            definitions = validate_workflows(workflows)
            if device not in ("cpu", "cuda") or beam not in (1, 3, 5) or len(microphone) > 200:
                raise ValueError("Choose CPU/CUDA and beam size 1, 3 or 5.")
        except ValueError as exc:
            return self._settings_error(str(exc))
        self._workflows, self._workflows_text = definitions, workflows
        self._auto_reasoning = adaptive
        options = {"device": device, "beam": beam, "preview": preview, "microphone": microphone}
        if options != self._voice_options:
            self._close_voice()
        self._voice_options = options
        for key, value in (("workflows", workflows), ("autoReasoning", adaptive), ("voiceDevice", device),
                           ("voiceBeam", beam), ("voicePreview", preview), ("microphone", microphone)):
            self.settings.setValue(key, value)
        self._preferences_error = ""
        self.changed.emit()
        return True

    @Slot(str, str, str, str, str, str, bool, str, int, bool, str, result=bool)
    def saveAllPreferences(self, effort, access, model, language, voice_model, workflows, adaptive, device, beam, preview, microphone):
        if self._locked():
            return False
        try:
            thread_options(self._folder, access, model.strip())
            if effort not in REASONING or language not in dict(LANGUAGES) or not valid_voice_model(voice_model.strip()):
                raise ValueError("Choose supported reasoning, voice language and multilingual model settings.")
            validate_workflows(workflows)
            if device not in ("cpu", "cuda") or beam not in (1, 3, 5) or len(microphone) > 200:
                raise ValueError("Choose CPU/CUDA and beam size 1, 3 or 5.")
        except ValueError as exc:
            return self._settings_error(str(exc))
        self.saveRuntimePreferences(workflows, adaptive, device, beam, preview, microphone)
        return self.savePreferences(effort, access, model, language, voice_model)

    @Slot()
    def exportMetrics(self):
        path, _ = QFileDialog.getSaveFileName(None, "Export timings (no task content)", "tigo-timings.json", "JSON (*.json)")
        if path:
            try:
                Path(path).write_text(json.dumps(self.profiler.export(), indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                self._message("error", "Could not export timings: " + str(exc))

    def _record_voice(self):
        self._voice_write("record", language=self._language, **self._voice_options,
                          auto_stop=self._record_auto_send, silence_ms=self._voice_silence_ms)

    def _complete_auto_voice(self):
        pending, self._pending_voice_submit = self._pending_voice_submit, None
        if not pending:
            return
        token, text = pending
        if token != self._voice_id or self._voice_cancelled or self._shutting_down:
            return
        if (not self._voice_auto_blocked and not self._draft_present and not self._attachments
                and self._voice_auto_send and not self._locked() and self.send(text)):
            self.draftRequested.emit('')
            return
        self.transcriptReady.emit(text)
        self._show_notice("Voice request kept in the draft: review it and press Send. Existing draft, attachments or task state prevented automatic sending.")

    def _voice_write(self, command, **values):
        self.voice.write((json.dumps({"command": command, "id": self._voice_id, **values}) + "\n").encode())

    @Slot()
    def warmVoice(self):
        if self._locked() or not self.voiceAvailable:
            return
        self._voice_cancelled = False
        self._voice_id = str(uuid.uuid4())
        self._voice_state, self._activity = "loading", "Preparing " + self._transcription_provider + " transcription"
        self._start_voice()
        self.changed.emit()

    def _start_voice(self):
        if self.speaker.active and self._voice_state != 'idle' and not self._voice_cancelled:
            if self._speech_handoff != self._voice_id:
                self._speech_handoff = self._voice_id
                token = self._voice_id
                self.speaker.when_quiet(lambda: self._voice_after_speech(token))
            return
        if self._voice_state == "idle" or self._voice_cancelled:
            return
        if self._voice_state == "transcribing" and self._voice_stop_requested:
            self.cancelVoice()  # Stop arrived while waiting for the wake mic.
            return
        if self.wake_control.enabled and self.wake_control.process.state() != QProcess.NotRunning and self.wake_control.state != "paused":
            self.wake_control.reserve_microphone(self._start_voice)
            return
        self._voice_idle_timer.stop()
        if self.voice.state() == QProcess.ProcessState.Running and self._voice_ready:
            if self._voice_state == "starting":
                self._record_voice()
            else:
                self._voice_state = "idle"
            return
        if self.voice.state() == QProcess.ProcessState.NotRunning:
            self._voice_buffer = b""
            self._voice_ready = False
            self.voice.start(self._voice_command[0], [*self._voice_command[1:], "--worker", "--model", self._voice_model,
                              "--device", self._voice_options["device"], "--provider", self._transcription_provider])

    def _voice_after_speech(self, token):
        self._speech_handoff = ''
        if token == self._voice_id and not self._voice_cancelled and self._voice_state != 'idle':
            self._start_voice()

    @Slot()
    def toggleVoice(self):
        if self._busy or self.profile.busy:
            return
        if self._voice_state in ("starting", "recording"):
            self._voice_stop_requested = True
            if self._voice_ready:
                self._voice_write("stop")
            self._voice_state, self._activity = "transcribing", "Transcribing " + ("locally" if self._transcription_provider == "local" else "online")
        elif self._voice_state == "idle":
            if self._transcription_provider == "online" and self._language == "auto":
                self._message("error", "Select a speech language in Voice settings for online dictation. Auto detect is local-only.")
                return
            if not self.voiceAvailable:
                self._message("error", "Voice packages are missing. Use the voice-enabled launcher.")
                return
            self._voice_id = str(uuid.uuid4())
            self._voice_cancelled = False
            self._voice_stop_requested = False
            self._record_auto_send = self._voice_auto_send
            self._voice_auto_blocked = self._draft_present or bool(self._attachments)
            self._pending_voice_submit = None
            self._voice_state, self._activity = "starting", "Opening " + self._transcription_provider + " voice input"
            self._start_voice()
        self.changed.emit()

    def _voice_started(self):
        pass  # Worker reports ready after loading; microphone remains off until record.

    @Slot()
    def cancelVoice(self):
        self._wake_record_token += 1
        self._pending_voice_submit = None
        self._voice_cancelled = True
        self._voice_id = str(uuid.uuid4())  # Late transcripts belong to the abandoned recording.
        self._close_voice()
        self._voice_state, self._activity = "idle", "Voice cancelled"
        self._level = 0
        self.changed.emit()

    def _read_voice(self):
        self._voice_buffer += bytes(self.voice.readAllStandardOutput())
        if len(self._voice_buffer) > 1000000:
            self.cancelVoice()
            self._message("error", "Voice worker sent an oversized event.")
            return
        while b"\n" in self._voice_buffer:
            line, self._voice_buffer = self._voice_buffer.split(b"\n", 1)
            try:
                event = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(event, dict):
                continue
            kind = event.get("type")
            if kind == "ready":
                self._voice_ready = True
                self.profiler.voice["modelLoadMs"] = event.get("modelLoadMs", 0)
                self._microphones = [{"id": "", "label": "System default"}, *event.get("microphones", [])]
                if self._voice_state in ("starting", "transcribing") and not self._voice_cancelled:
                    self._record_voice()
                    if self._voice_stop_requested:
                        self._voice_write("stop")
                else:
                    self._voice_state = "idle"
                    self._activity = "Transcription ready"
                    self._voice_idle_timer.start()
                self.changed.emit()
                continue
            if event.get("id") != self._voice_id or self._voice_cancelled:
                if kind == "error" and not event.get("id"):
                    self._message("error", str(event.get("message", "Voice failed.")))
                continue
            if kind == "recording":
                if not self._voice_stop_requested:
                    self._voice_state = "recording"
                    self._activity = "Listening - pause to send; Escape cancels" if self._record_auto_send else "Listening - click microphone to finish"
            elif kind == "speech_end":
                self._voice_state, self._activity = "transcribing", "Speech ended; preparing transcription"
            elif kind == "transcribing":
                self._voice_state, self._activity = "transcribing", "Transcribing " + ("locally" if self._transcription_provider == "local" else "online")
            elif kind == "level":
                self._level = max(0, min(1, float(event.get("value", 0))))
            elif kind == "preview":
                self.transcriptPreview.emit(str(event.get("text", "")))
            elif kind == "transcript":
                self.profiler.voice.update(event.get("timings", {}))
                text = str(event.get("text", ""))[:60000].strip()
                if self._record_auto_send and event.get("endReason") == "silence" and text:
                    self._pending_voice_submit = (self._voice_id, text)
                    self._activity = "Speech recognized; preparing voice request"
                else:
                    self.transcriptReady.emit(text)
                    self._activity = "Review your transcript, then press Send"
            elif kind == "error":
                self._pending_voice_submit = None
                self._message("error", str(event.get("message", "Voice failed.")))
                self._activity = "Voice unavailable"
            elif kind == "idle":
                self._voice_state = "idle"
                self._level = 0
                self._voice_idle_timer.start()
                self._complete_auto_voice()
            self.changed.emit()

    def _voice_finished(self, code, status):
        self._read_voice()
        self._voice_ready = False
        pending, self._pending_voice_submit = self._pending_voice_submit, None
        if pending and pending[0] == self._voice_id and not self._voice_cancelled and not self._shutting_down:
            self.transcriptReady.emit(pending[1])
            self._show_notice("Voice worker exited before completion; transcript kept for review.")
        if self._voice_state != "idle" and not self._voice_cancelled:
            self._message("error", "Voice worker stopped before producing a transcript. Check the model and microphone.")
            self._activity = "Voice unavailable"
        self._voice_state = "idle"
        self._level = 0
        self.changed.emit()

    def _voice_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._voice_state = "idle"
            self._message("error", "Could not start the voice worker: " + self.voice.errorString())
            self.changed.emit()

    def _close_voice(self):
        self._voice_idle_timer.stop()
        self._voice_ready = False
        if self.voice.state() != QProcess.ProcessState.NotRunning:
            self._voice_write("shutdown")
            if not self.voice.waitForFinished(200):
                self.voice.kill()
                self.voice.waitForFinished(1000)

    @Slot()
    def shutdown(self):
        self._shutting_down = True
        self._wake_record_token += 1
        self._pending_voice_submit = None
        self.updater.close()
        self.screen_activity.clear()
        self.speaker.shutdown()
        self._history_timer.stop()
        self.wake_control.shutdown()
        self.profile.shutdown()
        if self._busy:
            self._cancelled = True
            self._force_stop()
        self._save_history()
        pending, self._attachments = self._attachments, []
        self._clean_clipboard_images(pending)
        if self.history:
            self.history.close()
            self.history = None
        self._epoch += 1
        self.server.close()
        self._voice_cancelled = True
        self._close_voice()
