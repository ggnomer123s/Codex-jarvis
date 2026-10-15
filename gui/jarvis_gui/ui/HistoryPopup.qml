import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Popup {
    id: history
    objectName: "historyPopup"
    anchors.centerIn: parent
    width: Math.min(760, parent.width - 60); height: Math.min(720, parent.height - 60)
    padding: 22; modal: true; focus: true
    background: Rectangle { radius: 16; color: "#111f2b"; border.color: "#345463" }
    Overlay.modal: Rectangle { color: "#b0081018" }
    onOpened: { bridge.searchHistory(search.text); search.forceActiveFocus() }
    ColumnLayout {
        anchors.fill: parent; spacing: 12
        RowLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: "Conversations"; color: "#def2f4"; font.pixelSize: 24 }
            HudButton { text: "New"; implicitHeight: 32; enabled: !bridge.busy && bridge.voiceState === "idle" && !bridge.fullProfile.busy; onClicked: { bridge.newSession(); history.close() } }
            HudButton { text: "Close"; implicitHeight: 32; onClicked: history.close() }
        }
        TextField {
            id: search; objectName: "historySearch"; Layout.fillWidth: true
            placeholderText: "Search titles and messages"; placeholderTextColor: "#7795a5"; implicitHeight: 38; font.pixelSize: 13; color: "#d8edef"; selectByMouse: true
            background: Rectangle { radius: 8; color: "#0b1720"; border.color: "#315361" }
            onTextEdited: searchDelay.restart()
        }
        Timer { id: searchDelay; interval: 180; onTriggered: bridge.searchHistory(search.text) }
        Text { Layout.fillWidth: true; text: "Saved on this computer. Pinned conversations appear first. Up to 100 matching conversations are shown."; color: "#86a6b3"; font.pixelSize: 11; wrapMode: Text.WordWrap }
        ListView {
            id: entries; objectName: "historyList"
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 8
            model: bridge.historyEntries
            ScrollBar.vertical: ScrollBar {}
            delegate: Rectangle {
                required property var modelData
                width: entries.width - 12; height: 116; radius: 10; color: "#102630"; border.color: "#2a4956"
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 10; spacing: 6
                    Text { Layout.fillWidth: true; text: (modelData.pinned ? "★  " : "") + modelData.title; color: "#d1edeb"; font.pixelSize: 14; elide: Text.ElideRight }
                    Text { Layout.fillWidth: true; text: new Date(modelData.updated * 1000).toLocaleString() + "  ·  " + (modelData.model || "Codex default") + "  ·  " + modelData.access; color: "#87a8b4"; font.pixelSize: 10; elide: Text.ElideRight }
                    Text { Layout.fillWidth: true; text: modelData.folder; color: "#668b9a"; font.pixelSize: 10; elide: Text.ElideMiddle }
                    RowLayout {
                        HudButton { text: "Open"; implicitHeight: 28; font.pixelSize: 11; enabled: !bridge.busy && bridge.voiceState === "idle" && !bridge.fullProfile.busy; onClicked: { if (bridge.openConversation(modelData.id)) history.close() } }
                        HudButton { text: modelData.pinned ? "Unpin" : "Pin"; implicitHeight: 28; font.pixelSize: 11; onClicked: bridge.pinConversation(modelData.id, !modelData.pinned) }
                        HudButton { text: "Rename"; implicitHeight: 28; font.pixelSize: 11; onClicked: { renamePopup.key = modelData.id; renameField.text = modelData.title; renamePopup.open() } }
                        HudButton { text: "Delete"; implicitHeight: 28; font.pixelSize: 11; danger: true; enabled: !bridge.busy && bridge.voiceState === "idle" && !bridge.fullProfile.busy; onClicked: { deletePopup.key = modelData.id; deletePopup.open() } }
                    }
                }
            }
            Text { anchors.centerIn: parent; visible: entries.count === 0; text: "No matching conversations yet"; color: "#7c9eab"; font.pixelSize: 14 }
        }
        Text { visible: bridge.notice.length > 0; Layout.fillWidth: true; text: bridge.notice; color: "#f0bd89"; font.pixelSize: 11; wrapMode: Text.WordWrap }
    }
    Popup {
        id: renamePopup; property string key: ""
        anchors.centerIn: parent; width: 440; padding: 20; modal: true; focus: true
        background: Rectangle { color: "#142d38"; radius: 12; border.color: "#39717a" }
        ColumnLayout {
            anchors.fill: parent
            Text { text: "Conversation title"; color: "#d5efed"; font.pixelSize: 16 }
            TextField { id: renameField; Layout.fillWidth: true; maximumLength: 120; color: "#ddf5f2"; selectByMouse: true; background: Rectangle { color: "#0a1821"; radius: 6 } }
            RowLayout {
                HudButton { text: "Save"; onClicked: { bridge.renameConversation(renamePopup.key, renameField.text); renamePopup.close() } }
                HudButton { text: "Cancel"; onClicked: renamePopup.close() }
            }
        }
        implicitHeight: 170
    }
    Popup {
        id: deletePopup; property string key: ""
        anchors.centerIn: parent; width: 440; padding: 20; modal: true; focus: true
        background: Rectangle { color: "#2a2029"; radius: 12; border.color: "#805362" }
        ColumnLayout {
            anchors.fill: parent
            Text { Layout.fillWidth: true; text: "Delete this local conversation?"; color: "#f2dadd"; font.pixelSize: 16 }
            Text { Layout.fillWidth: true; text: "This removes the JARVIS history entry. Codex files and completed actions remain."; color: "#b798a3"; font.pixelSize: 12; wrapMode: Text.WordWrap }
            RowLayout {
                HudButton { text: "Delete"; danger: true; onClicked: { bridge.deleteConversation(deletePopup.key); deletePopup.close() } }
                HudButton { text: "Cancel"; onClicked: deletePopup.close() }
            }
        }
        implicitHeight: 180
    }
}
