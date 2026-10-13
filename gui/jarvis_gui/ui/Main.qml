import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1440; height: 900
    minimumWidth: 1060; minimumHeight: 760
    visible: true
    title: "JARVIS - Personal intelligence"
    color: "#080e14"
    font.family: "Segoe UI"
    property bool voiceActive: bridge.voiceState !== "idle"
    property bool locked: bridge.busy || voiceActive
    property bool compact: width < 1250

    Shortcut { sequence: "Escape"; onActivated: { if (bridge.busy) bridge.stop(); else if (window.voiceActive) bridge.cancelVoice() } }
    Shortcut { sequence: "Ctrl+N"; enabled: !window.locked; onActivated: bridge.newSession() }
    Connections {
        target: bridge
        function onTranscriptReady(text) {
            composer.text = composer.text ? composer.text + "\n" + text : text
            composer.forceActiveFocus()
        }
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
                HudButton { Layout.fillWidth: true; text: "Workspace"; glyph: "⌑"; enabled: !window.locked; onClicked: bridge.chooseFolder() }
                HudButton { Layout.fillWidth: true; text: "Preferences"; glyph: "⚙"; enabled: !window.locked; onClicked: preferences.open() }
                Item { Layout.fillHeight: true }
                Rectangle {
                    Layout.fillWidth: true; implicitHeight: workspaceLabel.implicitHeight + 66; radius: 12; color: "#101e27"; border.color: "#213640"
                    Column {
                        anchors.fill: parent; anchors.margins: 14; spacing: 10
                        Text { text: "WORKSPACE"; color: "#718b9b"; font.pixelSize: 9; font.letterSpacing: 1.5 }
                        Text { id: workspaceLabel; width: parent.width; text: bridge.folder; color: "#b9ccd6"; font.pixelSize: 11; wrapMode: Text.WrapAnywhere; maximumLineCount: 3; elide: Text.ElideMiddle }
                        Text { text: bridge.access === "read-only" ? "◉  Observe only" : "◉  Workspace edits"; color: "#64d3c3"; font.pixelSize: 10 }
                    }
                }
                Text { Layout.topMargin: 14; text: "BUILT FOR YOUR DESKTOP"; color: "#536c7d"; font.pixelSize: 8; font.letterSpacing: 1.2 }
                Text { Layout.bottomMargin: 8; text: "Powered by Codex CLI"; color: "#8ca3b2"; font.pixelSize: 11 }
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
                    Rectangle {
                        width: 128; height: 30; radius: 15; color: "#10251f"; border.color: "#254c3e"
                        Row { anchors.centerIn: parent; spacing: 8
                            Rectangle { width: 6; height: 6; radius: 3; anchors.verticalCenter: parent.verticalCenter; color: bridge.codexAvailable ? "#7af0ad" : "#f0b57a" }
                            Text { text: bridge.codexAvailable ? "CLI DETECTED" : "CLI MISSING"; color: "#a3c8b7"; font.pixelSize: 9; font.letterSpacing: 1 }
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
                        Layout.preferredWidth: window.compact ? 310 : 360
                        Layout.preferredHeight: window.compact ? 310 : 360
                        Layout.minimumHeight: 220
                        active: bridge.busy || window.voiceActive
                        listening: bridge.voiceState === "recording"
                        level: bridge.audioLevel
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter; spacing: 8
                        Rectangle { width: 5; height: 5; radius: 3; color: "#43e8da" }
                        Text {
                            Layout.maximumWidth: window.compact ? 310 : 400
                            text: bridge.activity; color: "#89b9be"; font.pixelSize: 11; elide: Text.ElideRight
                        }
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
                                    enabled: !bridge.busy && bridge.voiceState !== "transcribing"
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
                                    text: bridge.voiceState === "recording" ? "Listening · max 60 seconds" : (bridge.voiceState === "transcribing" ? "Transcribing locally..." : "Voice stays local until you send")
                                    color: "#7897a7"; font.pixelSize: 9; elide: Text.ElideRight
                                }
                                HudButton {
                                    visible: window.locked; text: "Stop"; danger: true
                                    onClicked: { if (bridge.busy) bridge.stop(); else bridge.cancelVoice() }
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
                                model: bridge.messages
                                ScrollBar.vertical: ScrollBar {}
                                delegate: Rectangle {
                                    required property var modelData
                                    width: conversation.width - 8
                                    height: messageColumn.implicitHeight + 28
                                    radius: 12
                                    color: modelData.role === "user" ? "#142c36" : (modelData.role === "error" ? "#2b1d26" : "#101f2a")
                                    border.color: modelData.role === "error" ? "#633d46" : "#243b47"
                                    Column {
                                        id: messageColumn
                                        width: parent.width - 28; x: 14; y: 14; spacing: 10
                                        Text {
                                            text: modelData.role === "user" ? "YOU" : (modelData.role === "assistant" ? "JARVIS" : (modelData.role === "error" ? "ATTENTION" : "SESSION"))
                                            color: modelData.role === "error" ? "#fca5a5" : "#68cec7"
                                            font.pixelSize: 9; font.letterSpacing: 1.7
                                        }
                                        TextEdit {
                                            width: parent.width
                                            text: modelData.text; color: "#cbdde5"; font.pixelSize: 12
                                            readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap
                                            textFormat: TextEdit.PlainText
                                            Accessible.name: modelData.role + " message"
                                        }
                                    }
                                }
                            }
                        }
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#20333f" }
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
        anchors.centerIn: parent
        width: 460; padding: 26
        modal: true; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { radius: 18; color: "#111f2b"; border.color: "#345463" }
        Overlay.modal: Rectangle { color: "#b0081018" }
        onOpened: {
            effortChoice.currentIndex = ["low", "default", "high"].indexOf(bridge.effort)
            accessChoice.currentIndex = bridge.access === "read-only" ? 0 : 1
        }
        contentItem: ColumnLayout {
            spacing: 16
            Text { text: "Make it yours."; color: "#def2f4"; font.pixelSize: 26; font.weight: Font.Light }
            Text { text: "Reasoning"; color: "#8eadbd"; font.pixelSize: 12 }
            ComboBox {
                id: effortChoice; Layout.fillWidth: true
                model: ["Fast - low reasoning", "Normal - Codex default", "Deep - high reasoning"]
            }
            Text { text: "Workspace access"; color: "#8eadbd"; font.pixelSize: 12 }
            ComboBox {
                id: accessChoice; Layout.fillWidth: true
                model: ["Observe only", "Allow workspace edits"]
            }
            Text {
                Layout.fillWidth: true; wrapMode: Text.WordWrap
                text: "Workspace edits allow Codex to change files in the selected folder. Desktop MCP permissions come from your existing JARVIS setup. Actions requiring additional approval fail in this noninteractive interface."
                color: "#91aab8"; font.pixelSize: 12; lineHeight: 1.4
            }
            Text {
                Layout.fillWidth: true; wrapMode: Text.WordWrap
                text: "Microphone audio is transcribed on this computer. Review the text before sending it to Codex. First use downloads a Whisper model."
                color: "#6f909f"; font.pixelSize: 11; lineHeight: 1.4
            }
            HudButton {
                Layout.fillWidth: true; primary: true; text: "Save preferences"
                onClicked: { bridge.configure(["low", "default", "high"][effortChoice.currentIndex], accessChoice.currentIndex === 0 ? "read-only" : "workspace-write"); preferences.close() }
            }
        }
    }
}
