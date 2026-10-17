import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ColumnLayout {
    spacing: 8
    function sync() {
        autoSend.checked = bridge.voiceAutoSend
        pauseChoice.currentIndex = Math.max(0, pauseChoice.indexOfValue(bridge.voiceSilenceMs))
    }
    Component.onCompleted: sync()
    Connections { target: bridge; function onChanged() { sync() } }
    HudCheckBox {
        id: autoSend; objectName: "voiceAutoSend"
        text: "Send voice requests automatically after a speech pause"
        Layout.fillWidth: true
        onClicked: { bridge.saveVoiceAutomation(checked, bridge.voiceSilenceMs); sync() }
        contentItem: Text { text: parent.text; color: "#b8eee4"; leftPadding: 30; font.pixelSize: 12; wrapMode: Text.WordWrap; verticalAlignment: Text.AlignVCenter }
    }
    RowLayout {
        visible: autoSend.checked
        Text { text: "End-of-speech pause"; color: "#8eadbd"; font.pixelSize: 11 }
        HudComboBox {
            id: pauseChoice; objectName: "voiceSilenceChoice"; Layout.fillWidth: true
            textRole: "label"; valueRole: "ms"
            model: [{label: "1.2 seconds", ms: 1200}, {label: "1.6 seconds", ms: 1600},
                    {label: "2.4 seconds", ms: 2400}, {label: "3.2 seconds", ms: 3200}]
            onActivated: bridge.saveVoiceAutomation(autoSend.checked, currentValue)
        }
    }
    Text {
        Layout.fillWidth: true; color: autoSend.checked ? "#dfb987" : "#6f909f"; font.pixelSize: 10; wrapMode: Text.WordWrap
        text: autoSend.checked
            ? "Enabled for all voice requests: local speech detection finishes recording, then recognized text goes to Codex without pressing Send. Existing/edited drafts and attachments keep the result for review. Escape cancels. Background voices can be recognized too."
            : "Off: review the transcript and press Send. Enable to record and submit hands-free after a pause. This choice saves immediately."
    }
}
