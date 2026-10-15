import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window
    width: 1440; height: 900
    minimumWidth: 1060; minimumHeight: 760
    visible: true
    title: "JARVIS - Personal intelligence"
    color: "#080e14"
    font.family: "Segoe UI"
    property bool voiceActive: bridge.voiceState !== "idle"
    property bool locked: bridge.busy || voiceActive || bridge.fullProfile.busy
    property bool compact: width < 1250
    property real coreSize: Math.min(compact ? 310 : 360, Math.max(220, height - 520))
    property string liveTranscript: ""

    Shortcut { sequence: "Escape"; onActivated: { if (bridge.busy) bridge.stop(); else if (window.voiceActive) bridge.cancelVoice(); else if (bridge.fullProfile.busy) bridge.fullProfile.cancel() } }
    Shortcut { sequence: "Ctrl+N"; enabled: !window.locked; onActivated: bridge.newSession() }
    Connections {
        target: bridge
        function onTranscriptReady(text) {
            window.liveTranscript = ""
            composer.text = composer.text ? composer.text + "\n" + text : text
            composer.forceActiveFocus()
        }
        function onTranscriptPreview(text) { window.liveTranscript = text }
        function onChanged() { if (bridge.voiceState === "starting") window.liveTranscript = "" }
        function onMessagesChanged() { scrollDelay.restart() }
    }
    Timer { id: scrollDelay; interval: 50; onTriggered: conversation.positionViewAtEnd() }

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
                        Text { anchors.centerIn: parent; text: "J"; color: "#87f9e7"; font.pixelSize: 21 }
                    }
                    Text { text: "JARVIS"; color: "#e6f5f7"; font.pixelSize: 20; font.letterSpacing: 3; font.weight: Font.DemiBold }
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
                        spacing: 5
                        Text { text: "Command center"; color: "#dcebf0"; font.pixelSize: 16; font.weight: Font.DemiBold }
                        Text { text: "A little less friction. A little more possibility."; color: "#6d8798"; font.pixelSize: 11 }
                    }
                    Item { Layout.fillWidth: true }
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

            RowLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                spacing: 0
                ColumnLayout {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    Layout.leftMargin: window.compact ? 20 : 34; Layout.rightMargin: window.compact ? 20 : 34
                    spacing: 0
                    Text {
                        Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 34
                        text: "YOUR PERSONAL INTELLIGENCE SYSTEM"; color: "#668f9c"; font.pixelSize: 9; font.letterSpacing: 2.2
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 12
                        text: "At your command."; color: "#e2f4f5"; font.pixelSize: window.compact ? 31 : 40; font.weight: Font.Light
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
                        active: bridge.busy || window.voiceActive || bridge.fullProfile.busy
                        listening: bridge.voiceState === "recording"
                        targetLevel: bridge.audioLevel
                        stage: bridge.fullProfile.busy ? "connecting" : bridge.stage
                        animate: window.visibility !== Window.Minimized
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter; spacing: 8
                        Rectangle { width: 5; height: 5; radius: 3; color: "#43e8da" }
                        Text {
                            Layout.maximumWidth: window.compact ? 310 : 400
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
                        Layout.alignment: Qt.AlignHCenter; Layout.maximumWidth: window.compact ? 310 : 420
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
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 154
                        radius: 16; color: "#111f29"; border.color: composer.activeFocus ? "#40867f" : "#2a404c"
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 14; spacing: 8
                            ScrollView {
                                Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                                TextArea {
                                    id: composer
                                    objectName: "composer"
                                    placeholderText: "Ask JARVIS anything, or use your voice..."
                                    placeholderTextColor: "#688291"
                                    color: "#e0f1f4"; font.pixelSize: 13
                                    wrapMode: TextEdit.Wrap; selectByMouse: true
                                    background: null; padding: 2
                                    enabled: !bridge.busy
                                    Accessible.name: "Message to JARVIS"
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
                                    implicitWidth: 44; text: ""
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
                                Text {
                                    Layout.fillWidth: true
                                    text: bridge.voiceState === "recording" ? "Listening · max 60 seconds" : (bridge.voiceState === "transcribing" ? "Transcribing locally..." : (bridge.voiceReady ? "Local voice model ready" : "Voice stays local until you send"))
                                    color: "#7897a7"; font.pixelSize: 9; elide: Text.ElideRight
                                }
                                HudButton {
                                    visible: window.locked; text: "Stop"; danger: true
                                    onClicked: { if (bridge.busy) bridge.stop(); else if (window.voiceActive) bridge.cancelVoice(); else bridge.fullProfile.cancel() }
                                }
                                HudButton {
                                    id: sendButton; objectName: "sendButton"
                                    primary: true; text: "Send"; glyph: "↗"
                                    enabled: !window.locked && composer.text.trim().length > 0 && bridge.codexAvailable
                                    onClicked: {
                                        if (composer.text.trim().length > 0 && !window.locked && bridge.codexAvailable) {
                                            bridge.send(composer.text); composer.clear()
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 11; Layout.bottomMargin: 20
                        text: "ENTER TO SEND   /   SHIFT + ENTER FOR A NEW LINE"; color: "#536f7e"; font.pixelSize: 8; font.letterSpacing: 1
                    }
                }

                Rectangle {
                    Layout.preferredWidth: window.compact ? 326 : 374; Layout.fillHeight: true
                    color: "#0b151e"
                    Rectangle { width: 1; height: parent.height; color: "#1b2c36" }
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 22; spacing: 14
                        RowLayout {
                            Layout.fillWidth: true; Layout.topMargin: 9
                            Text { text: "CONVERSATION"; color: "#a5bfcc"; font.pixelSize: 10; font.letterSpacing: 2 }
                            Item { Layout.fillWidth: true }
                            Text { text: "01"; color: "#38606f"; font.pixelSize: 11; font.family: "monospace" }
                        }
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
                                Text { width: parent.width; text: "Ask a question, explore a project,\nor let JARVIS help with your desktop."; horizontalAlignment: Text.AlignHCenter; color: "#718e9f"; font.pixelSize: 12; lineHeight: 1.5 }
                                Text { width: parent.width; text: bridge.codexAvailable ? "Uses your existing Codex login.\nDesktop tools use your configured MCPs." : "Install Codex CLI and run codex login,\nthen reopen this app."; horizontalAlignment: Text.AlignHCenter; color: "#536f80"; font.pixelSize: 10; lineHeight: 1.5 }
                            }
                            ListView {
                                id: conversation; objectName: "conversation"
                                anchors.fill: parent; clip: true; spacing: 16
                                model: bridge.messageModel
                                ScrollBar.vertical: ScrollBar {}
                                delegate: Rectangle {
                                    required property string messageRole
                                    required property string messageText
                                    width: conversation.width - 8
                                    height: messageColumn.implicitHeight + 28
                                    radius: 12
                                    color: messageRole === "user" ? "#142c36" : (messageRole === "error" ? "#2b1d26" : "#101f2a")
                                    border.color: messageRole === "error" ? "#633d46" : "#243b47"
                                    Column {
                                        id: messageColumn
                                        width: parent.width - 28; x: 14; y: 14; spacing: 10
                                        Text {
                                            text: messageRole === "user" ? "YOU" : (messageRole === "assistant" ? "JARVIS" : (messageRole === "error" ? "ATTENTION" : "SESSION"))
                                            color: messageRole === "error" ? "#fca5a5" : "#68cec7"
                                            font.pixelSize: 9; font.letterSpacing: 1.7
                                        }
                                        TextEdit {
                                            width: parent.width
                                            text: messageText; color: "#cbdde5"; font.pixelSize: 12
                                            readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap
                                            textFormat: TextEdit.PlainText
                                            Accessible.name: messageRole + " message"
                                        }
                                    }
                                }
                            }
                        }
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#20333f" }
                        Text {
                            Layout.fillWidth: true; text: bridge.metricsSummary; color: "#84aeb8"
                            font.pixelSize: 9; wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "●"; color: "#48bcad"; font.pixelSize: 9 }
                            Text { text: "LOCAL VOICE · CODEX INTELLIGENCE"; color: "#587889"; font.pixelSize: 8; font.letterSpacing: 0.7 }
                        }
                    }
                }
            }
        }
    }

    Popup {
        id: preferences
        objectName: "preferences"
        anchors.centerIn: parent
        width: 600; height: Math.min(window.height - 60, 700); padding: 24
        modal: true; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { radius: 18; color: "#111f2b"; border.color: "#345463" }
        Overlay.modal: Rectangle { color: "#b0081018" }
        onOpened: {
            effortChoice.currentIndex = ["low", "default", "high"].indexOf(bridge.effort)
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
        }
        contentItem: ColumnLayout {
            spacing: 14
            Text { text: "Make it yours."; color: "#def2f4"; font.pixelSize: 26; font.weight: Font.Light }
            Text { text: "Your model. Your voice. Your level of control."; color: "#6d929f"; font.pixelSize: 11 }
            RowLayout {
                id: preferenceTabs
                objectName: "preferenceTabs"
                property int currentIndex: 0
                Layout.fillWidth: true; spacing: 8
                Repeater {
                    model: ["Intelligence", "Voice", "Access", "Runtime", "Automation"]
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
                        model: ["Fast - low reasoning", "Normal - Codex default", "Deep - high reasoning"]
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
                        Text { Layout.fillWidth: true; text: bridge.fullProfile.ready ? "Full Access profile is included and ready." : (bridge.fullProfile.busy ? "Preparing the Full Access profile..." : "The profile will be prepared when you enable the checkbox."); color: "#84b9b0"; font.pixelSize: 10; wrapMode: Text.WordWrap }
                        Text { Layout.fillWidth: true; text: "Allows Codex to change your user files and run commands without its sandbox or command approvals. Uses a separate profile and login. Root / Administrator privileges and OS authentication are unchanged."; color: "#dfb987"; font.pixelSize: 11; wrapMode: Text.WordWrap; lineHeight: 1.4 }
                        Text { visible: bridge.fullAccess; text: "FULL ACCESS IS ACTIVE FOR THIS WINDOW"; color: "#f4c185"; font.pixelSize: 10; font.letterSpacing: 1 }
                        RowLayout {
                            HudButton { text: "Sign in to full profile"; enabled: bridge.fullProfile.ready && !window.locked; onClicked: bridge.fullProfile.login() }
                            HudButton { text: "Open sign-in page"; visible: bridge.fullProfile.loginUrl.length > 0; onClicked: bridge.fullProfile.openLoginPage() }
                            HudButton { text: "Cancel"; visible: bridge.fullProfile.busy; danger: true; onClicked: bridge.fullProfile.cancel() }
                        }
                        Text { Layout.fillWidth: true; text: "Sign in once if this separate profile has no login. Follow the device link and code below. Full Access returns to your normal mode when you reopen JARVIS."; color: "#6f909f"; font.pixelSize: 10; wrapMode: Text.WordWrap; lineHeight: 1.4 }
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
            }
            HudButton {
                Layout.fillWidth: true; primary: true; text: "Save preferences"
                enabled: !window.locked
                onClicked: {
                    let model = modelChoice.editText === "Codex default" ? "" : modelChoice.editText
                    let access = bridge.fullAccess ? "full-access" : ["read-only", "workspace-write"][accessChoice.currentIndex]
                    if (bridge.saveAllPreferences(["low", "default", "high"][effortChoice.currentIndex], access, model, languageChoice.currentValue, voiceModelChoice.editText,
                        workflowEditor.text, adaptiveChoice.checked, ["cpu", "cuda"][deviceChoice.currentIndex], [1, 3, 5][beamChoice.currentIndex], previewChoice.checked, micChoice.currentValue || "")) preferences.close()
                }
            }
            Text { Layout.fillWidth: true; visible: bridge.preferencesError.length > 0; text: bridge.preferencesError; color: "#f5a4a4"; font.pixelSize: 11; wrapMode: Text.WordWrap }
        }
    }
}
