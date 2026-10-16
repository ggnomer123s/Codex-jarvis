import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window
    width: 1440; height: 900
    minimumWidth: 1060; minimumHeight: 760
    visible: !bridge.startHidden
    title: "Tigo - Personal intelligence"
    color: "#080e14"
    font.family: "Segoe UI"
    property bool voiceActive: bridge.voiceState !== "idle"
    property bool locked: bridge.busy || voiceActive || bridge.fullProfile.busy
    property bool compact: width < 1250
    property real coreSize: Math.min(compact ? 280 : 360, Math.max(220, height - 440), Math.max(220, corePanel.width - 30))
    property string liveTranscript: ""
    property bool followConversation: true
    function syncComposerControls() {
        if (!inlineModel.activeFocus && !inlineModel.contentItem.activeFocus) inlineModel.editText = bridge.model || "Codex default"
        inlineEffort.currentIndex = Math.max(0, inlineEffort.indexOfValue(bridge.effort))
    }

    onClosing: function(close) {
        if (bridge.wake.enabled) {
            close.accepted = false
            if (bridge.trayAvailable) window.hide()
            else window.showMinimized()
        }
    }

    Shortcut { sequence: "Escape"; onActivated: { if (bridge.busy) bridge.stop(); else if (window.voiceActive) bridge.cancelVoice(); else if (bridge.fullProfile.busy) bridge.fullProfile.cancel(); else if (bridge.speech.active) bridge.speech.stop() } }
    Shortcut { sequence: "Ctrl+Shift+F"; onActivated: bridge.setChatOnly(!bridge.chatOnly) }
    Shortcut { sequence: "Ctrl+H"; onActivated: historyPopup.open() }
    Shortcut { sequence: "Ctrl+O"; enabled: !window.locked; onActivated: bridge.chooseAttachments() }
    Shortcut { sequence: "Ctrl+Shift+V"; enabled: !window.locked; onActivated: bridge.pasteImage() }
    Shortcut { sequence: "Ctrl+N"; enabled: !window.locked; onActivated: bridge.newSession() }
    Connections {
        target: bridge
        function onTranscriptReady(text) {
            window.liveTranscript = ""
            composer.text = composer.text ? composer.text + "\n" + text : text
            composer.forceActiveFocus()
        }
        function onTranscriptPreview(text) { window.liveTranscript = text }
        function onChanged() {
            if (bridge.voiceState === "starting") window.liveTranscript = ""
            Qt.callLater(window.syncComposerControls)
        }
        function onMessagesChanged() { if (window.followConversation) scrollDelay.restart() }
        function onDraftRequested(text) { composer.text = text; composer.forceActiveFocus() }
    }
    Timer { id: scrollDelay; interval: 50; onTriggered: conversation.positionViewAtEnd() }
    Connections {
        target: bridge.wake
        function onChanged() { wakeToggle.checked = bridge.wake.enabled }
    }

    // Static drafting grid: the animated core is the only moving decoration.
    Canvas {
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            let ctx = getContext("2d"); ctx.reset()
            ctx.strokeStyle = "#0d1a23"; ctx.lineWidth = 1
            for (let x = 0; x < width; x += 44) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke() }
            for (let y = 0; y < height; y += 44) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke() }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            visible: !bridge.chatOnly
            Layout.preferredWidth: window.compact ? 182 : 224
            Layout.fillHeight: true
            color: "#0b131b"
            Rectangle { anchors.right: parent.right; height: parent.height; width: 1; color: "#1a2b36" }
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 22
                spacing: 12
                RowLayout {
                    Layout.topMargin: 12; spacing: 11
                    Rectangle {
                        width: 30; height: 30; radius: 8; color: "#123238"; border.color: "#338981"
                        Text { anchors.centerIn: parent; objectName: "brandMonogram"; text: "T"; color: "#87f9e7"; font.pixelSize: 21 }
                    }
                    Text { objectName: "brandTitle"; text: "Tigo"; color: "#e6f5f7"; font.pixelSize: 20; font.letterSpacing: 3; font.weight: Font.DemiBold }
                }
                Text { Layout.topMargin: 2; text: "PERSONAL INTELLIGENCE"; color: "#627d8d"; font.pixelSize: 9; font.letterSpacing: 1.4 }
                Rectangle { Layout.fillWidth: true; Layout.topMargin: 24; height: 1; color: "#1b2b35" }
                Text { Layout.topMargin: 18; Layout.bottomMargin: 2; text: "YOUR SPACE"; color: "#657c8c"; font.pixelSize: 10; font.letterSpacing: 2 }
                Rectangle {
                    Layout.fillWidth: true; height: 46; radius: 10; color: "#123037"; border.color: "#255158"
                    Row {
                        anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 14; spacing: 12
                        Text { text: "◈"; color: "#69efdc"; font.pixelSize: 17 }
                        Text { text: "Command center"; color: "#bcf8ef"; font.pixelSize: 12 }
                    }
                }
                HudButton { Layout.fillWidth: true; text: "New conversation"; glyph: "+"; enabled: !window.locked; onClicked: bridge.newSession() }
                HudButton { Layout.fillWidth: true; text: "History"; objectName: "historyButton"; onClicked: historyPopup.open() }
                HudButton { Layout.fillWidth: true; objectName: "coreVisibilityButton"; text: bridge.showCore ? "Hide core" : "Show core"; onClicked: bridge.setShowCore(!bridge.showCore) }
                HudButton { Layout.fillWidth: true; text: "Resume previous"; enabled: bridge.canResume; onClicked: bridge.resumePrevious() }
                HudButton { Layout.fillWidth: true; text: "Workspace"; glyph: "⌑"; enabled: !window.locked; onClicked: bridge.chooseFolder() }
                HudButton { Layout.fillWidth: true; text: "Preferences"; glyph: "⚙"; enabled: !bridge.busy && !window.voiceActive; onClicked: preferences.open() }
                Item { Layout.fillHeight: true }
                Rectangle {
                    Layout.fillWidth: true; implicitHeight: workspaceLabel.implicitHeight + 66; radius: 12; color: "#101e27"; border.color: "#213640"
                    Column {
                        anchors.fill: parent; anchors.margins: 14; spacing: 10
                        Text { text: "WORKSPACE"; color: "#718b9b"; font.pixelSize: 9; font.letterSpacing: 1.5 }
                        Text { id: workspaceLabel; width: parent.width; text: bridge.folder; color: "#b9ccd6"; font.pixelSize: 11; wrapMode: Text.WrapAnywhere; maximumLineCount: 3; elide: Text.ElideMiddle }
                        Text { text: bridge.fullAccess ? "◉  FULL ACCESS" : (bridge.access === "read-only" ? "◉  Observe only" : "◉  Workspace edits"); color: bridge.fullAccess ? "#f3b972" : "#64d3c3"; font.pixelSize: 10 }
                    }
                }
                Text { Layout.topMargin: 14; text: "BUILT FOR YOUR DESKTOP"; color: "#536c7d"; font.pixelSize: 8; font.letterSpacing: 1.2 }
                Text {
                    Layout.fillWidth: true; visible: bridge.wake.enabled
                    text: bridge.wake.state === "listening" ? "MIC ON / VOICE ACTIVATION" : "VOICE ACTIVATION / " + bridge.wake.state.toUpperCase()
                    color: bridge.wake.state === "error" ? "#ff8ba9" : "#69dfce"
                    font.pixelSize: 8; wrapMode: Text.WordWrap
                }
                Text { Layout.bottomMargin: 8; text: "Codex app-server"; color: "#8ca3b2"; font.pixelSize: 11 }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            spacing: 0
            Rectangle {
                Layout.fillWidth: true; height: 82; color: "#0a121a"
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#1a2b36" }
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 30; anchors.rightMargin: 30
                    Column {
                        visible: !window.compact
                        spacing: 5
                        Text { text: "Command center"; color: "#dcebf0"; font.pixelSize: 16; font.weight: Font.DemiBold }
                        Text { text: "A little less friction. A little more possibility."; color: "#6d8798"; font.pixelSize: 11 }
                    }
                    Item { Layout.fillWidth: true }
                    HudButton { text: "History"; implicitHeight: 30; font.pixelSize: 11; onClicked: historyPopup.open() }
                    HudButton { objectName: "chatOnlyButton"; text: bridge.chatOnly ? "Command center" : "Full chat"; implicitHeight: 30; font.pixelSize: 11; onClicked: bridge.setChatOnly(!bridge.chatOnly) }
                    HudButton {
                        implicitHeight: 30; Layout.maximumWidth: window.compact ? 140 : 200
                        text: bridge.model || "Codex default"; font.pixelSize: 10
                        enabled: !bridge.busy && !window.voiceActive
                        onClicked: { preferences.open(); preferenceTabs.currentIndex = 0 }
                        ToolTip.visible: hovered; ToolTip.text: "Choose a model and reasoning mode"
                    }
                    Rectangle {
                        visible: bridge.fullAccess
                        width: 106; height: 30; radius: 15; color: "#332619"; border.color: "#8e5f32"
                        Text { anchors.centerIn: parent; text: "FULL ACCESS"; color: "#ffd29a"; font.pixelSize: 9; font.letterSpacing: 1 }
                    }
                    Rectangle {
                        width: 128; height: 30; radius: 15; color: "#10251f"; border.color: "#254c3e"
                        Row { anchors.centerIn: parent; spacing: 8
                            Rectangle { width: 6; height: 6; radius: 3; anchors.verticalCenter: parent.verticalCenter; color: bridge.codexAvailable ? "#7af0ad" : "#f0b57a" }
                            Text { text: bridge.serverReady ? "CONNECTED" : (bridge.codexAvailable ? "READY TO CONNECT" : "CLI MISSING"); color: "#a3c8b7"; font.pixelSize: 8; font.letterSpacing: 0.5 }
                        }
                    }
                }
            }

            SplitView {
                id: panelSplit; objectName: "panelSplit"
                Layout.fillWidth: true; Layout.fillHeight: true
                orientation: Qt.Horizontal
                onResizingChanged: if (!resizing) bridge.setChatWidth(Math.round(chatPane.width))
                handle: Rectangle {
                    implicitWidth: 8; color: SplitHandle.hovered || SplitHandle.pressed ? "#275b60" : "#10212c"
                    Rectangle { anchors.centerIn: parent; width: 2; height: 36; radius: 1; color: "#4c8d91" }
                }
                ColumnLayout {
                    id: corePanel; objectName: "corePanel"
                    visible: bridge.showCore && !bridge.chatOnly
                    SplitView.fillWidth: true; SplitView.minimumWidth: 310
                    spacing: 0
                    Text {
                        Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 34
                        text: "YOUR PERSONAL INTELLIGENCE SYSTEM"; color: "#668f9c"; font.pixelSize: 9; font.letterSpacing: 2.2
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 12
                        text: "At your command."; color: "#e2f4f5"; font.pixelSize: corePanel.width < 440 ? 27 : 36; font.weight: Font.Light
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 10
                        text: "Think it. Say it. Let's make it happen."; color: "#7e9aa9"; font.pixelSize: 12
                    }
                    Item { Layout.fillHeight: true; Layout.minimumHeight: 8 }
                    Orb {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: window.coreSize
                        Layout.preferredHeight: window.coreSize
                        Layout.minimumHeight: 220
                        active: bridge.busy || window.voiceActive || bridge.fullProfile.busy || bridge.speech.active
                        listening: bridge.voiceState === "recording"
                        targetLevel: bridge.audioLevel
                        stage: bridge.fullProfile.busy ? "connecting" : bridge.stage
                        animate: corePanel.visible && window.visibility !== Window.Minimized
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter; spacing: 8
                        Rectangle { width: 5; height: 5; radius: 3; color: "#43e8da" }
                        Text {
                            Layout.maximumWidth: Math.max(200, corePanel.width - 30)
                            text: bridge.fullProfile.busy ? "Preparing profile / waiting for sign-in" : bridge.activity; color: "#89b9be"; font.pixelSize: 11; elide: Text.ElideRight
                        }
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 10; spacing: 14
                        Text { text: bridge.effort.toUpperCase() + " REASONING"; color: "#567986"; font.pixelSize: 8; font.letterSpacing: 1 }
                        Rectangle { width: 1; height: 10; color: "#2a4752" }
                        Text { text: "LOCAL VOICE / " + bridge.language.toUpperCase() + " / " + (bridge.voiceModels.indexOf(bridge.voiceModel) >= 0 ? bridge.voiceModel.toUpperCase() : "CUSTOM"); color: "#567986"; font.pixelSize: 8; font.letterSpacing: 1 }
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter; Layout.maximumWidth: Math.max(200, corePanel.width - 30)
                        visible: window.voiceActive && window.liveTranscript.length > 0
                        text: window.liveTranscript; color: "#b6e8df"; font.pixelSize: 11
                        maximumLineCount: 2; elide: Text.ElideRight; wrapMode: Text.WordWrap
                    }
                    Item { Layout.fillHeight: true; Layout.minimumHeight: 14 }
                    RowLayout {
                        Layout.fillWidth: true; Layout.bottomMargin: 20; spacing: 10
                        Repeater {
                            model: [{label: "Explore my workspace", prompt: "Inspect this workspace and explain what I can work on."},
                                    {label: "Check my desktop", prompt: "Use the available desktop MCP to report the active app and available capabilities without changing anything."}]
                            HudButton {
                                required property var modelData
                                Layout.fillWidth: true; text: modelData.label; font.pixelSize: 11
                                enabled: !window.locked
                                onClicked: { composer.text = modelData.prompt; composer.forceActiveFocus() }
                            }
                        }
                    }

                }

                Rectangle {
                    id: chatPane; objectName: "chatPane"
                    SplitView.preferredWidth: bridge.chatWidth
                    SplitView.minimumWidth: 420
                    SplitView.fillWidth: !corePanel.visible
                    color: "#0b151e"
                    Rectangle { width: 1; height: parent.height; color: "#1b2c36" }
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 16; spacing: 10
                        RowLayout {
                            Layout.fillWidth: true; Layout.topMargin: 9; spacing: 6
                            Text { text: "CONVERSATION"; color: "#a5bfcc"; font.pixelSize: 10; font.letterSpacing: 2 }
                            Item { Layout.fillWidth: true }
                            HudButton {
                                objectName: "conversationFontSmaller"
                                text: "A−"; implicitWidth: 34; implicitHeight: 30; font.pixelSize: 12
                                enabled: bridge.conversationFontSize > 12
                                Accessible.name: "Decrease conversation text size"
                                onClicked: bridge.setConversationFontSize(bridge.conversationFontSize - 2)
                                ToolTip.visible: hovered; ToolTip.text: "Smaller conversation text"
                            }
                            Text {
                                Layout.preferredWidth: 32; horizontalAlignment: Text.AlignHCenter
                                text: bridge.conversationFontSize + " px"; color: "#89b9be"; font.pixelSize: 10
                                Accessible.name: "Conversation text size: " + bridge.conversationFontSize + " pixels"
                            }
                            HudButton {
                                objectName: "conversationFontLarger"
                                text: "A+"; implicitWidth: 34; implicitHeight: 30; font.pixelSize: 12
                                enabled: bridge.conversationFontSize < 28
                                Accessible.name: "Increase conversation text size"
                                onClicked: bridge.setConversationFontSize(bridge.conversationFontSize + 2)
                                ToolTip.visible: hovered; ToolTip.text: "Larger conversation text"
                            }
                        }
                        Text { Layout.fillWidth: true; text: bridge.conversationTitle; color: "#7ca2b2"; font.pixelSize: 11; elide: Text.ElideRight }
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#20333f" }
                        Item {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            Column {
                                visible: bridge.messages.length === 0
                                anchors.centerIn: parent; width: parent.width - 18; spacing: 14
                                Rectangle {
                                    anchors.horizontalCenter: parent.horizontalCenter; width: 58; height: 58; radius: 18; color: "#132a34"; border.color: "#2b4955"
                                    Text { anchors.centerIn: parent; text: "✧"; color: "#78d8d0"; font.pixelSize: 30 }
                                }
                                Text { width: parent.width; text: "A space for your ideas."; horizontalAlignment: Text.AlignHCenter; color: "#c5dce2"; font.pixelSize: 15 }
                                Text { width: parent.width; text: "Ask a question, explore a project,\nor let Tigo help with your desktop."; horizontalAlignment: Text.AlignHCenter; color: "#718e9f"; font.pixelSize: 12; lineHeight: 1.5 }
                                Text { width: parent.width; text: bridge.codexAvailable ? "Uses your existing Codex login.\nDesktop tools use your configured MCPs." : "Install Codex CLI and run codex login,\nthen reopen this app."; horizontalAlignment: Text.AlignHCenter; color: "#536f80"; font.pixelSize: 10; lineHeight: 1.5 }
                            }
                            ListView {
                                id: conversation; objectName: "conversation"
                                anchors.fill: parent; clip: true; spacing: 16
                                model: bridge.messageModel
                                onHeightChanged: if (window.followConversation) scrollDelay.restart()
                                onWidthChanged: if (window.followConversation) scrollDelay.restart()
                                onMovementStarted: window.followConversation = false
                                onMovementEnded: window.followConversation = atYEnd
                                ScrollBar.vertical: ScrollBar { onPressedChanged: window.followConversation = pressed ? false : conversation.atYEnd }
                                delegate: MessageCard {
                                    width: conversation.width - 12
                                    locked: window.locked
                                    onPreviewRequested: function(attachment) { attachmentPreview.show(attachment) }
                                }
                            }
                        }
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#20333f" }
                        RowLayout {
                            Layout.fillWidth: true
                            BusyIndicator { running: bridge.busy || window.voiceActive || bridge.speech.active; visible: running; implicitWidth: 24; implicitHeight: 24 }
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 4
                                Text { text: bridge.taskStatus.title + (bridge.taskStatus.elapsed ? "  ·  " + bridge.taskStatus.elapsed : ""); color: bridge.taskStatus.state === "failed" ? "#ff9baf" : "#8ae0d1"; font.pixelSize: 12 }
                                Text { Layout.fillWidth: true; text: bridge.taskStatus.detail; color: "#89a8b7"; font.pixelSize: 10; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight }
                            }
                            HudButton {
                                visible: window.locked; text: "Stop"; danger: true; implicitHeight: 30; font.pixelSize: 11
                                onClicked: { if (bridge.busy) bridge.stop(); else if (window.voiceActive) bridge.cancelVoice(); else bridge.fullProfile.cancel() }
                            }
                            HudButton { objectName: "stopSpeechButton"; visible: bridge.speech.active; text: "Stop speech"; danger: true; implicitHeight: 30; font.pixelSize: 11; onClicked: bridge.speech.stop() }
                            HudButton { visible: !window.followConversation; text: "Latest ↓"; implicitHeight: 28; font.pixelSize: 10; onClicked: { window.followConversation = true; conversation.positionViewAtEnd() } }
                        }
                        Text { Layout.fillWidth: true; visible: bridge.speech.state === "error"; text: bridge.speech.status; color: "#f0b0a2"; font.pixelSize: 11; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight }
                        Text { Layout.fillWidth: true; visible: bridge.notice.length > 0; text: bridge.notice; color: "#efc389"; font.pixelSize: 11; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight }
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: bridge.attachments.length > 0 ? 232 : 174
                        radius: 16; color: "#111f29"; border.color: composer.activeFocus ? "#40867f" : "#2a404c"
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 14; spacing: 8
                            RowLayout {
                                Layout.fillWidth: true; spacing: 8
                                HudButton { text: "Attach files"; objectName: "attachFilesButton"; implicitHeight: 28; font.pixelSize: 10; enabled: !window.locked; onClicked: bridge.chooseAttachments() }
                                HudButton { text: "Paste image"; implicitHeight: 28; font.pixelSize: 10; enabled: !window.locked; onClicked: bridge.pasteImage() }
                                HudButton { objectName: "speechToggleButton"; text: bridge.speech.enabled ? "Speech on" : "Speech off"; implicitHeight: 28; font.pixelSize: 10; onClicked: bridge.speech.setEnabled(!bridge.speech.enabled); ToolTip.visible: hovered; ToolTip.text: "Automatic spoken replies; choose a voice in Preferences > Speech" }
                                Text { Layout.fillWidth: true; text: "Drop files here"; color: "#668d9b"; font.pixelSize: 10; elide: Text.ElideRight }
                            }
                            ScrollView {
                                visible: bridge.attachments.length > 0
                                Layout.fillWidth: true; Layout.preferredHeight: 66; clip: true
                                contentWidth: attachmentRow.implicitWidth; contentHeight: 58
                                Row {
                                    id: attachmentRow; spacing: 8
                                    Repeater {
                                        model: bridge.attachments
                                        delegate: Rectangle {
                                            required property var modelData
                                            required property int index
                                            width: 190; height: 55; radius: 8; color: "#172f3a"; border.color: "#31515e"
                                            RowLayout {
                                                anchors.fill: parent; anchors.margins: 5
                                                Image { visible: modelData.kind === "image"; source: visible ? modelData.url : ""; sourceSize.width: 44; sourceSize.height: 44; Layout.preferredWidth: 38; Layout.preferredHeight: 38; fillMode: Image.PreserveAspectFit }
                                                HudButton { Layout.fillWidth: true; text: modelData.name; implicitHeight: 40; font.pixelSize: 10; onClicked: attachmentPreview.show(modelData) }
                                                HudButton { text: "×"; implicitWidth: 25; implicitHeight: 28; enabled: !window.locked; Accessible.name: "Remove attachment"; onClicked: bridge.removeAttachment(index) }
                                            }
                                        }
                                    }
                                }
                            }
                            ScrollView {
                                Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                                TextArea {
                                    id: composer
                                    objectName: "composer"
                                    placeholderText: "Ask Tigo anything, or use your voice..."
                                    placeholderTextColor: "#688291"
                                    color: "#e0f1f4"; font.pixelSize: 13
                                    wrapMode: TextEdit.Wrap; selectByMouse: true
                                    background: null; padding: 2
                                    enabled: !bridge.busy
                                    Accessible.name: "Message to Tigo"
                                    Keys.onPressed: function(event) {
                                        if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && !(event.modifiers & Qt.ShiftModifier) && !window.locked) {
                                            sendButton.clicked(); event.accepted = true
                                        }
                                    }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true; spacing: 8
                                HudButton {
                                    id: micButton; objectName: "microphoneButton"
                                    implicitWidth: 34; implicitHeight: 34; text: ""
                                    primary: bridge.voiceState === "recording"
                                    enabled: !bridge.busy && !bridge.fullProfile.busy && bridge.voiceState !== "transcribing"
                                    Accessible.name: bridge.voiceState === "recording" ? "Finish voice recording" : "Start voice recording"
                                    onClicked: bridge.toggleVoice()
                                    ToolTip.visible: hovered
                                    ToolTip.text: bridge.voiceAvailable ? "Click to record. Click again to transcribe." : "Install the voice extra to enable your microphone."
                                    Image {
                                        anchors.centerIn: parent; width: 21; height: 21
                                        source: bridge.voiceState === "recording" ? "microphone-active.svg" : "microphone.svg"
                                    }
                                }
                                HudComboBox {
                                    id: inlineModel; objectName: "inlineModel"
                                    Layout.preferredWidth: Math.min(180, Math.max(100, chatPane.width * 0.24))
                                    implicitHeight: 34; font.pixelSize: 10
                                    model: bridge.models; editable: true; enabled: !window.locked
                                    Accessible.name: "Codex model"
                                    Component.onCompleted: editText = bridge.model || "Codex default"
                                    onActivated: bridge.selectModel(currentText)
                                    onAccepted: bridge.selectModel(editText)
                                    ToolTip.visible: hovered; ToolTip.text: bridge.model || "Codex default"
                                }
                                HudComboBox {
                                    id: inlineEffort; objectName: "inlineEffort"
                                    Layout.preferredWidth: 96
                                    implicitHeight: 34; font.pixelSize: 10
                                    model: bridge.reasoningOptions; textRole: "label"; valueRole: "code"
                                    enabled: !window.locked
                                    currentIndex: Math.max(0, indexOfValue(bridge.effort))
                                    Component.onCompleted: Qt.callLater(window.syncComposerControls)
                                    onModelChanged: Qt.callLater(window.syncComposerControls)
                                    Accessible.name: "Reasoning level"
                                    onActivated: bridge.selectReasoning(currentValue)
                                    ToolTip.visible: hovered; ToolTip.text: "Reasoning level; availability depends on the model"
                                }
                                Text {
                                    Layout.fillWidth: true; Layout.minimumWidth: 0
                                    visible: chatPane.width > 700
                                    text: bridge.voiceState === "recording" ? "Listening · max 60 seconds" : (bridge.voiceState === "transcribing" ? "Transcribing locally..." : (bridge.voiceReady ? "Local voice model ready" : "Voice stays local until you send"))
                                    color: "#7897a7"; font.pixelSize: 9; elide: Text.ElideRight
                                }
                                HudButton {
                                    id: sendButton; objectName: "sendButton"
                                    primary: true; text: "Send"; implicitWidth: 66; implicitHeight: 34; font.pixelSize: 11
                                    enabled: !window.locked && (composer.text.trim().length > 0 || bridge.attachments.length > 0) && bridge.codexAvailable
                                    onClicked: {
                                        if ((composer.text.trim().length > 0 || bridge.attachments.length > 0) && !window.locked && bridge.codexAvailable) {
                                            if (bridge.send(composer.text)) { composer.clear(); window.followConversation = true; scrollDelay.restart() }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    }
                }
            }
        }
    }

    HistoryPopup { id: historyPopup }
    AttachmentPreview { id: attachmentPreview }
    DropArea {
        anchors.fill: parent
        onEntered: function(drag) { drag.accepted = drag.hasUrls && !window.locked }
        onDropped: function(drop) { if (drop.hasUrls && bridge.addAttachments(drop.urls)) drop.acceptProposedAction() }
        Rectangle { anchors.fill: parent; visible: parent.containsDrag; color: "#201ad4c5"; border.color: "#60ead9"; border.width: 3 }
    }

    Popup {
        id: preferences
        objectName: "preferences"
        anchors.centerIn: parent
        width: 700; height: Math.min(window.height - 60, 700); padding: 24
        modal: true; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { radius: 18; color: "#111f2b"; border.color: "#345463" }
        Overlay.modal: Rectangle { color: "#b0081018" }
        function applyWake() {
            return bridge.wake.configure(wakeToggle.checked, wakeAutostart.checked, wakeModel.editText.trim(),
                wakeLanguage.currentValue, wakeMic.currentIndex >= 0 ? String(wakeMic.currentValue) : wakeMic.editText.trim(), wakeFuzzy.checked)
        }
        onOpened: {
            speechPage.sync()
            effortChoice.currentIndex = Math.max(0, effortChoice.indexOfValue(bridge.effort))
            accessChoice.currentIndex = ["read-only", "workspace-write"].indexOf(bridge.normalAccess)
            modelChoice.currentIndex = bridge.models.indexOf(bridge.model || "Codex default")
            modelChoice.editText = bridge.model || "Codex default"
            languageChoice.currentIndex = languageChoice.indexOfValue(bridge.language)
            voiceModelChoice.currentIndex = bridge.voiceModels.indexOf(bridge.voiceModel)
            voiceModelChoice.editText = bridge.voiceModel
            adaptiveChoice.checked = bridge.autoReasoning
            deviceChoice.currentIndex = ["cpu", "cuda"].indexOf(bridge.voiceDevice)
            beamChoice.currentIndex = [1, 3, 5].indexOf(bridge.voiceBeam)
            previewChoice.checked = bridge.voicePreview
            micChoice.currentIndex = micChoice.indexOfValue(bridge.microphone)
            workflowEditor.text = bridge.workflowsText
            wakeToggle.checked = bridge.wake.enabled
            wakeAutostart.checked = bridge.wake.autostart
            wakeFuzzy.checked = bridge.wake.fuzzy
            wakeModel.editText = bridge.wake.model
            wakeLanguage.currentIndex = Math.max(0, wakeLanguage.indexOfValue(bridge.wake.language))
            wakeMic.currentIndex = wakeMic.indexOfValue(bridge.wake.microphone)
            if (wakeMic.currentIndex < 0) wakeMic.editText = bridge.wake.microphone
        }
        contentItem: ColumnLayout {
            spacing: 14
            Text { text: "Make it yours."; color: "#def2f4"; font.pixelSize: 26; font.weight: Font.Light }
            Text { text: "Your model. Your voice. Your level of control."; color: "#6d929f"; font.pixelSize: 11 }
            RowLayout {
                id: preferenceTabs
                objectName: "preferenceTabs"
                property int currentIndex: 0
                onCurrentIndexChanged: if (currentIndex === 6) { bridge.speech.refresh(); speechPage.sync() }
                Layout.fillWidth: true; spacing: 8
                Repeater {
                    model: ["Intelligence", "Voice", "Access", "Runtime", "Automation", "Wake", "Speech"]
                    HudButton {
                        required property string modelData
                        required property int index
                        Layout.fillWidth: true; text: modelData; implicitHeight: 36; font.pixelSize: 10
                        primary: preferenceTabs.currentIndex === index
                        onClicked: preferenceTabs.currentIndex = index
                    }
                }
            }
            StackLayout {
                currentIndex: preferenceTabs.currentIndex
                Layout.fillWidth: true; Layout.fillHeight: true
                ColumnLayout {
                    spacing: 14
                    Text { text: "Codex model"; color: "#8eadbd"; font.pixelSize: 12 }
                    HudComboBox { id: modelChoice; objectName: "modelChoice"; Layout.fillWidth: true; editable: true; model: bridge.models; enabled: !window.locked }
                    RowLayout {
                        Text { Layout.fillWidth: true; text: "Live app-server catalog when connected; local cache before connection."; color: "#6e919f"; font.pixelSize: 10; wrapMode: Text.WordWrap }
                        HudButton { text: "Refresh"; implicitHeight: 30; enabled: !window.locked; onClicked: bridge.refreshModels() }
                    }
                    Text { text: "Reasoning"; color: "#8eadbd"; font.pixelSize: 12 }
                    HudComboBox {
                        id: effortChoice; Layout.fillWidth: true; enabled: !window.locked
                        model: bridge.reasoningOptions; textRole: "label"; valueRole: "code"
                    }
                    CheckBox {
                        id: adaptiveChoice; text: "Adapt reasoning to task difficulty"; enabled: !window.locked
                        contentItem: Text { text: parent.text; color: "#a8d4d0"; leftPadding: 30; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter }
                    }
                    Text { Layout.fillWidth: true; text: "Model availability depends on your Codex account and provider. Normal uses the configured reasoning default. Changing model starts a fresh conversation."; color: "#6f909f"; font.pixelSize: 11; wrapMode: Text.WordWrap; lineHeight: 1.4 }
                    Item { Layout.fillHeight: true }
                }
                ScrollView {
                    clip: true; contentWidth: availableWidth
                    ColumnLayout {
                    width: parent.width
                    spacing: 14
                    Text { text: "Speech language"; color: "#8eadbd"; font.pixelSize: 12 }
                    HudComboBox {
                        id: languageChoice; objectName: "languageChoice"; Layout.fillWidth: true; enabled: !window.locked
                        model: bridge.languageOptions; textRole: "label"; valueRole: "code"
                    }
                    Text { Layout.fillWidth: true; text: "15 language presets, including Russian. Auto detect also handles other languages supported by multilingual Whisper."; color: "#6f909f"; font.pixelSize: 11; wrapMode: Text.WordWrap; lineHeight: 1.4 }
                    Text { text: "Local Whisper model"; color: "#8eadbd"; font.pixelSize: 12 }
                    HudComboBox { id: voiceModelChoice; Layout.fillWidth: true; editable: true; model: bridge.voiceModels; enabled: !window.locked }
                    Text { Layout.fillWidth: true; text: "tiny: smaller and faster. base: balanced. small / medium: larger models for more demanding speech. You can enter a local multilingual model folder for offline use."; color: "#6f909f"; font.pixelSize: 11; wrapMode: Text.WordWrap; lineHeight: 1.4 }
                    RowLayout {
                        HudComboBox { id: deviceChoice; Layout.fillWidth: true; model: ["CPU / int8", "NVIDIA CUDA / int8-fp16"]; enabled: !window.locked }
                        HudComboBox { id: beamChoice; Layout.fillWidth: true; model: ["Beam 1 / fast", "Beam 3 / balanced", "Beam 5 / thorough"]; enabled: !window.locked }
                    }
                    Text { text: "Microphone"; color: "#8eadbd"; font.pixelSize: 12 }
                    HudComboBox { id: micChoice; Layout.fillWidth: true; model: bridge.microphones; textRole: "label"; valueRole: "id"; enabled: !window.locked }
                    CheckBox {
                        id: previewChoice; text: "Show provisional text while recording"; enabled: !window.locked
                        contentItem: Text { text: parent.text; color: "#a8d4d0"; leftPadding: 30; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter }
                    }
                    Text { Layout.fillWidth: true; text: "Model stays ready for five idle minutes. Preview uses extra CPU and may change in the final transcript. CUDA requires compatible NVIDIA libraries. Audio stays in memory; review before sending."; color: "#6f909f"; font.pixelSize: 11; wrapMode: Text.WordWrap; lineHeight: 1.4 }
                    HudButton { text: bridge.voiceReady ? "Voice model ready" : "Prepare saved model / list microphones"; enabled: !window.locked && bridge.voiceAvailable; onClicked: bridge.warmVoice() }
                    }
                }
                ScrollView {
                    clip: true
                    contentWidth: availableWidth
                    ColumnLayout {
                        width: parent.width; spacing: 12
                        Text { text: "Normal workspace access"; color: "#8eadbd"; font.pixelSize: 12 }
                        HudComboBox {
                            id: accessChoice; objectName: "accessChoice"; Layout.fillWidth: true; enabled: !window.locked && !bridge.fullAccess
                            model: ["Observe only", "Allow workspace edits"]
                        }
                        Text { Layout.fillWidth: true; text: "Workspace edits allow changes in the selected folder. Desktop MCP permissions come from your existing profile. Commands needing additional approval fail in the normal GUI modes."; color: "#6f909f"; font.pixelSize: 11; wrapMode: Text.WordWrap; lineHeight: 1.4 }
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#34515b" }
                        CheckBox {
                            id: fullAccessToggle; objectName: "fullAccessToggle"
                            text: "Enable Full Access"
                            checked: bridge.fullAccess
                            enabled: !window.locked
                            hoverEnabled: true
                            onClicked: bridge.setFullAccess(checked)
                            indicator: Rectangle {
                                width: 24; height: 24; radius: 6
                                x: fullAccessToggle.leftPadding; y: (fullAccessToggle.height - height) / 2
                                color: fullAccessToggle.checked ? "#f1bd7b" : "#10232d"
                                border.color: fullAccessToggle.checked || fullAccessToggle.hovered ? "#d4a369" : "#41606a"
                                Text { anchors.centerIn: parent; text: fullAccessToggle.checked ? "✓" : ""; color: "#11202a"; font.pixelSize: 17 }
                            }
                            contentItem: Text { text: fullAccessToggle.text; color: "#f3c38d"; font.pixelSize: 13; leftPadding: fullAccessToggle.indicator.width + 10; verticalAlignment: Text.AlignVCenter }
                        }
                        Text { Layout.fillWidth: true; text: "One Codex profile, login and MCP configuration for every access mode."; color: "#84b9b0"; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        Text { Layout.fillWidth: true; text: "Full Access is on by default and allows changes to your user files and commands without the Codex sandbox or command approvals. Turn it off above to use the selected sandbox. This setting is saved and shared with the tigo CLI. OS authentication and root / Administrator protections remain in place."; color: "#dfb987"; font.pixelSize: 11; wrapMode: Text.WordWrap; lineHeight: 1.4 }
                        Text { visible: bridge.fullAccess; text: "FULL ACCESS IS ACTIVE"; color: "#f4c185"; font.pixelSize: 10; font.letterSpacing: 1 }
                        Text {
                            visible: bridge.windowsDesktop; Layout.fillWidth: true
                            text: "Windows desktop control is separate. After sending a task, leave the mouse and keyboard idle for the service interval (usually 10 seconds). Physical input, including Check, restarts that wait. Full Access does not override your control of the screen."
                            color: "#99bdc5"; font.pixelSize: 11; wrapMode: Text.WordWrap
                        }
                        HudButton {
                            objectName: "desktopControlCheckButton"; visible: bridge.windowsDesktop
                            text: "Check desktop control"; enabled: !window.locked
                            onClicked: bridge.checkDesktopControl()
                        }
                        Text {
                            objectName: "desktopControlStatus"; visible: bridge.windowsDesktop; Layout.fillWidth: true
                            text: bridge.desktopControlStatus; color: "#82c9bc"; font.pixelSize: 11; wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            HudButton { text: "Sign in to Codex"; enabled: !window.locked; onClicked: bridge.fullProfile.login() }
                            HudButton { text: "Open sign-in page"; visible: bridge.fullProfile.loginUrl.length > 0; onClicked: bridge.fullProfile.openLoginPage() }
                            HudButton { text: "Cancel"; visible: bridge.fullProfile.busy; danger: true; onClicked: bridge.fullProfile.cancel() }
                        }
                        Text { Layout.fillWidth: true; text: "Your existing Codex login is reused. Sign in only if Codex is not authenticated. No extra profile is installed and no credentials are copied."; color: "#6f909f"; font.pixelSize: 10; wrapMode: Text.WordWrap }
                        TextArea {
                            Layout.fillWidth: true; Layout.preferredHeight: 115
                            visible: bridge.fullProfile.output.length > 0
                            text: bridge.fullProfile.output; color: "#acc9d0"; font.pixelSize: 10; wrapMode: TextEdit.Wrap
                            readOnly: true; selectByMouse: true; textFormat: TextEdit.PlainText
                            background: Rectangle { color: "#08141c"; radius: 8 }
                        }
                    }
                }
                ColumnLayout {
                    spacing: 12
                    Text { Layout.fillWidth: true; text: "Task timings and connection state"; color: "#bde5de"; font.pixelSize: 14 }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                        TextArea { text: bridge.runtimeDetails; readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap; color: "#bad4dc"; font.pixelSize: 12; background: Rectangle { color: "#0a1720"; radius: 8 } }
                    }
                    Text { Layout.fillWidth: true; text: "Timings exclude task content. Connected does not prove model login or desktop input permission. Resume restores conversation context and does not replay actions."; color: "#6f909f"; font.pixelSize: 11; wrapMode: Text.WordWrap }
                    RowLayout {
                        HudButton { text: "Export timings"; onClicked: bridge.exportMetrics() }
                        HudButton { text: "Resume previous"; enabled: bridge.canResume; onClicked: bridge.resumePrevious() }
                    }
                }
                ColumnLayout {
                    spacing: 12
                    Text { Layout.fillWidth: true; text: "Exact commands, verified desktop steps"; color: "#bde5de"; font.pixelSize: 14 }
                    Text { Layout.fillWidth: true; text: "Add a JSON array of named workflows with exact aliases and 1–5 steps. Each step calls your configured desktop MCP and checks its result. See docs/runtime.md for examples."; color: "#6f909f"; font.pixelSize: 11; wrapMode: Text.WordWrap }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                        TextArea {
                            id: workflowEditor; objectName: "workflowEditor"; text: "[]"; selectByMouse: true
                            enabled: !window.locked; wrapMode: TextEdit.Wrap; color: "#bad4dc"; font.pixelSize: 11; font.family: "monospace"
                            background: Rectangle { color: "#0a1720"; radius: 8 }
                        }
                    }
                    Text { Layout.fillWidth: true; text: "Save only workflows you reviewed. The executor stops on changed preconditions, refusal or failed verification. It does not bypass MCP guards or retry actions automatically."; color: "#6f909f"; font.pixelSize: 11; wrapMode: Text.WordWrap }
                }
                ScrollView {
                    clip: true; contentWidth: availableWidth
                    ColumnLayout {
                        width: parent.width; spacing: 12
                        Text { text: "Open Tigo by voice"; color: "#bde5de"; font.pixelSize: 15 }
                        Text {
                            Layout.fillWidth: true
                            text: "Optional background listening keeps your microphone on. Speech is transcribed locally in memory; only the wake name opens the window. Nothing is sent as a task or saved as a transcript."
                            color: "#8eafbb"; font.pixelSize: 11; wrapMode: Text.WordWrap
                        }
                        HudCheckBox {
                            id: wakeToggle; objectName: "wakeToggle"; text: "Listen for Tigo in the background"
                            checked: bridge.wake.enabled; enabled: !window.voiceActive
                            onClicked: { if (!preferences.applyWake()) checked = bridge.wake.enabled }
                            contentItem: Text { text: parent.text; color: "#b8eee4"; leftPadding: 30; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter }
                        }
                        HudCheckBox {
                            id: wakeAutostart; text: "Start listening when I sign in"
                            contentItem: Text { text: parent.text; color: "#a8d4d0"; leftPadding: 30; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter }
                        }
                        HudCheckBox {
                            id: wakeFuzzy; text: "Recognize similar pronunciations of Tigo"
                            contentItem: Text { text: parent.text; color: "#a8d4d0"; leftPadding: 30; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter }
                        }
                        Text { Layout.fillWidth: true; text: "Tolerant matching also handles Russian and small transcription errors. It can cause false activations. Turn it off for exact Tigo / Russian-name matching. Repeated activations have an 8-second cooldown."; color: "#6f909f"; font.pixelSize: 10; wrapMode: Text.WordWrap }
                        Text { text: "Wake language"; color: "#8eadbd"; font.pixelSize: 12 }
                        HudComboBox { id: wakeLanguage; Layout.fillWidth: true; model: bridge.languageOptions; textRole: "label"; valueRole: "code" }
                        Text { text: "Local wake model (CPU)"; color: "#8eadbd"; font.pixelSize: 12 }
                        HudComboBox { id: wakeModel; Layout.fillWidth: true; editable: true; model: bridge.voiceModels }
                        Text { Layout.fillWidth: true; text: "base balances speed and recognition; tiny uses fewer resources. First use downloads the model. Russian may work better with Russian selected explicitly."; color: "#6f909f"; font.pixelSize: 10; wrapMode: Text.WordWrap }
                        Text { text: "Wake microphone / device ID"; color: "#8eadbd"; font.pixelSize: 12 }
                        HudComboBox { id: wakeMic; Layout.fillWidth: true; editable: true; model: bridge.microphones; textRole: "label"; valueRole: "id" }
                        Text { Layout.fillWidth: true; text: "List microphones with Prepare saved model in the Voice tab, or enter a device ID/name. Closing the window keeps listening in the tray (minimized when the tray is unavailable). Quit Tigo stops it; disabling voice activation also removes its login startup entry."; color: "#6f909f"; font.pixelSize: 10; wrapMode: Text.WordWrap }
                        Text { objectName: "wakeStatus"; Layout.fillWidth: true; text: bridge.wake.status; color: bridge.wake.state === "error" ? "#ff8ba9" : "#84dec9"; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        HudButton { text: "Quit Tigo / stop listening"; onClicked: Qt.quit() }
                    }
                }
                SpeechSettings { id: speechPage }
            }
            HudButton {
                Layout.fillWidth: true; primary: true; text: preferenceTabs.currentIndex === 5 ? "Apply voice activation" : "Save preferences"
                enabled: !window.locked
                onClicked: {
                    if (preferenceTabs.currentIndex === 6) { if (speechPage.apply()) preferences.close(); return }
                    if (preferenceTabs.currentIndex === 5) { if (preferences.applyWake()) preferences.close(); return }
                    let model = modelChoice.editText === "Codex default" ? "" : modelChoice.editText
                    let access = bridge.fullAccess ? "full-access" : ["read-only", "workspace-write"][accessChoice.currentIndex]
                    if (bridge.saveAllPreferences(effortChoice.currentValue, access, model, languageChoice.currentValue, voiceModelChoice.editText,
                        workflowEditor.text, adaptiveChoice.checked, ["cpu", "cuda"][deviceChoice.currentIndex], [1, 3, 5][beamChoice.currentIndex], previewChoice.checked, micChoice.currentValue || "")) preferences.close()
                }
            }
            Text { Layout.fillWidth: true; visible: bridge.preferencesError.length > 0; text: bridge.preferencesError; color: "#f5a4a4"; font.pixelSize: 11; wrapMode: Text.WordWrap }
        }
    }
}
