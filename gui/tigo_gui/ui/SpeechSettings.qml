import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ScrollView {
    id: page
    objectName: "speechSettings"
    clip: true; contentWidth: availableWidth
    function sync() {
        engineChoice.currentIndex = bridge.speech.engineKind === "online" ? 1 : (bridge.speech.engineKind === "system" ? 2 : 0)
        speechVoice.currentIndex = Math.max(0, speechVoice.indexOfValue(bridge.speech.voice))
        rateSlider.value = bridge.speech.rate
        pitchSlider.value = bridge.speech.pitch
        volumeSlider.value = bridge.speech.volume
    }
    function apply() { return bridge.speech.configure(speechVoice.currentValue || "", rateSlider.value, pitchSlider.value, volumeSlider.value) }
    ColumnLayout {
        width: page.availableWidth; spacing: 8
        Text { text: "Tigo speaks"; color: "#d4f2ee"; font.pixelSize: 18 }
        HudCheckBox {
            objectName: "autoSpeechToggle"
            text: "Read completed replies aloud"; checked: bridge.speech.enabled
            onClicked: bridge.speech.setEnabled(checked)
            contentItem: Text { text: parent.text; color: "#b8eee4"; leftPadding: 30; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter }
        }
        Text { objectName: "speechPrivacy"; Layout.fillWidth: true; text: bridge.speech.engineKind === "online" ? "Online neural voices by Microsoft. Spoken reply text is sent to Microsoft over the Internet. No API key is required. Select Local neural to keep speech on this computer." : "Local male and female neural voices. Models download once (67-116 MB per voice), then speech works offline on CPU without uploading your replies."; color: bridge.speech.engineKind === "online" ? "#dfb987" : "#8baeb9"; font.pixelSize: 11; wrapMode: Text.WordWrap }
        HudComboBox {
            id: engineChoice; objectName: "speechEngineChoice"
            Layout.fillWidth: true
            model: ["Local neural (offline)", "Online neural (Microsoft)", "System voices (legacy)"]
            enabled: !bridge.speech.active
            onActivated: { bridge.speech.setEngine(["neural", "online", "system"][currentIndex]); page.sync() }
        }
        Text { text: "Speaking voice"; color: "#99bdc5"; font.pixelSize: 12 }
        HudComboBox {
            id: speechVoice; objectName: "speakingVoiceChoice"
            Layout.fillWidth: true; model: bridge.speech.voices; textRole: "label"; valueRole: "id"
            onModelChanged: Qt.callLater(function() { speechVoice.currentIndex = Math.max(0, speechVoice.indexOfValue(bridge.speech.voice)) })
        }
        Text { text: "Rate"; color: "#99bdc5"; font.pixelSize: 12 }
        HudSlider { id: rateSlider; objectName: "speechRate"; Layout.fillWidth: true; from: -1; to: 1; stepSize: .05; value: bridge.speech.rate; Accessible.name: "Speech rate" }
        Text { visible: bridge.speech.engineKind === "system"; text: "Pitch"; color: "#99bdc5"; font.pixelSize: 12 }
        HudSlider { id: pitchSlider; visible: bridge.speech.engineKind === "system"; Layout.fillWidth: true; from: -1; to: 1; stepSize: .05; value: bridge.speech.pitch; Accessible.name: "Speech pitch" }
        Text { text: "Volume"; color: "#99bdc5"; font.pixelSize: 12 }
        HudSlider { id: volumeSlider; Layout.fillWidth: true; from: 0; to: 1; stepSize: .05; value: bridge.speech.volume; Accessible.name: "Speech volume" }
        Text { Layout.fillWidth: true; text: bridge.speech.engineKind !== "system" ? "Automatic male / female matches Russian or English to each reply. A specific voice keeps its language. Neural voices preserve natural pitch." : "Legacy voices depend on your OS. Russian needs a system speech voice; Linux needs Speech Dispatcher. Choose a neural mode for trained voices."; color: "#799eac"; font.pixelSize: 11; wrapMode: Text.WordWrap }
        RowLayout {
            HudButton { text: "Refresh voices"; implicitHeight: 34; font.pixelSize: 11; enabled: !bridge.speech.active; onClicked: { bridge.speech.refresh(); page.sync() } }
            HudButton { text: "Test voice"; objectName: "testSpeechButton"; implicitHeight: 34; font.pixelSize: 11; enabled: !bridge.busy && bridge.voiceState === "idle" && !bridge.fullProfile.busy; onClicked: { if (page.apply()) bridge.testSpeech() } }
            HudButton { text: "Stop speech"; implicitHeight: 34; font.pixelSize: 11; danger: true; enabled: bridge.speech.active; onClicked: bridge.speech.stop() }
        }
        Text { objectName: "speechStatus"; Layout.fillWidth: true; text: bridge.speech.status; color: bridge.speech.state === "error" ? "#ffa2af" : "#82d7c9"; font.pixelSize: 12; wrapMode: Text.WordWrap }
        Text { Layout.fillWidth: true; text: "Code blocks and raw URLs stay in chat. Read reads a selected reply even with automatic speech off. The wake microphone pauses until speech ends; recording interrupts speech before opening the mic."; color: "#799eac"; font.pixelSize: 11; wrapMode: Text.WordWrap }
    }
}
