import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ScrollView {
    id: page
    objectName: "speechSettings"
    clip: true; contentWidth: availableWidth
    function sync() {
        engineChoice.currentIndex = bridge.speech.engineKind === "neural" ? 0 : 1
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
        Text { Layout.fillWidth: true; text: "Local neural voices, without API keys or uploading your replies. A voice downloads once (about 67 MB), then works offline on CPU."; color: "#8baeb9"; font.pixelSize: 11; wrapMode: Text.WordWrap }
        HudComboBox {
            id: engineChoice; objectName: "speechEngineChoice"
            Layout.fillWidth: true
            model: ["Neural (recommended)", "System voices (legacy)"]
            enabled: !bridge.speech.active
            onActivated: { bridge.speech.setEngine(currentIndex === 0 ? "neural" : "system"); page.sync() }
        }
        Text { text: "Speaking voice"; color: "#99bdc5"; font.pixelSize: 12 }
        HudComboBox {
            id: speechVoice; objectName: "speakingVoiceChoice"
            Layout.fillWidth: true; model: bridge.speech.voices; textRole: "label"; valueRole: "id"
            onModelChanged: Qt.callLater(function() { speechVoice.currentIndex = Math.max(0, speechVoice.indexOfValue(bridge.speech.voice)) })
        }
        Text { text: "Rate"; color: "#99bdc5"; font.pixelSize: 12 }
        HudSlider { id: rateSlider; objectName: "speechRate"; Layout.fillWidth: true; from: -1; to: 1; stepSize: .05; value: bridge.speech.rate; Accessible.name: "Speech rate" }
        Text { text: bridge.speech.engineKind === "neural" ? "Pitch (natural voice)" : "Pitch"; color: "#99bdc5"; font.pixelSize: 12 }
        HudSlider { id: pitchSlider; enabled: bridge.speech.engineKind !== "neural"; Layout.fillWidth: true; from: -1; to: 1; stepSize: .05; value: bridge.speech.pitch; Accessible.name: "Speech pitch" }
        Text { text: "Volume"; color: "#99bdc5"; font.pixelSize: 12 }
        HudSlider { id: volumeSlider; Layout.fillWidth: true; from: 0; to: 1; stepSize: .05; value: bridge.speech.volume; Accessible.name: "Speech volume" }
        Text { Layout.fillWidth: true; text: bridge.speech.engineKind === "neural" ? "Automatic selects a male Russian or English neural voice. Natural pitch is preserved. First use needs Internet for the model; subsequent speech stays on this computer. This is not an actor's cloned voice." : "Legacy voices depend on your OS. Russian needs a system speech voice; Linux needs Speech Dispatcher. Neural mode is recommended for better sound."; color: "#799eac"; font.pixelSize: 11; wrapMode: Text.WordWrap }
        RowLayout {
            HudButton { text: "Refresh voices"; implicitHeight: 34; font.pixelSize: 11; enabled: !bridge.speech.active; onClicked: { bridge.speech.refresh(); page.sync() } }
            HudButton { text: "Test voice"; objectName: "testSpeechButton"; implicitHeight: 34; font.pixelSize: 11; enabled: !bridge.busy && bridge.voiceState === "idle" && !bridge.fullProfile.busy; onClicked: { if (page.apply()) bridge.testSpeech() } }
            HudButton { text: "Stop speech"; implicitHeight: 34; font.pixelSize: 11; danger: true; enabled: bridge.speech.active; onClicked: bridge.speech.stop() }
        }
        Text { objectName: "speechStatus"; Layout.fillWidth: true; text: bridge.speech.status; color: bridge.speech.state === "error" ? "#ffa2af" : "#82d7c9"; font.pixelSize: 12; wrapMode: Text.WordWrap }
        Text { Layout.fillWidth: true; text: "Code blocks and raw URLs stay in chat. Read reads a selected reply even with automatic speech off. The wake microphone pauses until speech ends; recording interrupts speech before opening the mic."; color: "#799eac"; font.pixelSize: 11; wrapMode: Text.WordWrap }
    }
}
