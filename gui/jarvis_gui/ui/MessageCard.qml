import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: card
    required property string messageRole
    required property string messageText
    required property var messageBlocks
    required property var messageAttachments
    required property int index
    property bool locked: false
    signal previewRequested(var attachment)
    implicitHeight: content.implicitHeight + 24
    height: implicitHeight
    radius: 12
    color: messageRole === "user" ? "#142c36" : (messageRole === "error" ? "#2b1d26" : "#101f2a")
    border.color: messageRole === "error" ? "#633d46" : "#243b47"
    ColumnLayout {
        id: content
        x: 12; y: 12; width: card.width - 24; spacing: 10
        RowLayout {
            Layout.fillWidth: true; spacing: 5
            Text {
                Layout.fillWidth: true
                text: card.messageRole === "user" ? "YOU" : (card.messageRole === "assistant" ? "JARVIS" : (card.messageRole === "error" ? "ATTENTION" : "SESSION"))
                color: card.messageRole === "error" ? "#fca5a5" : "#68cec7"
                font.pixelSize: 9; font.letterSpacing: 1.2
            }
            HudButton {
                objectName: "copyMessageButton"; text: "Copy"; implicitHeight: 26; font.pixelSize: 10
                onClicked: bridge.copyText(card.messageText)
            }
            HudButton {
                objectName: "readMessageButton"; text: "Read"; implicitHeight: 26; font.pixelSize: 10
                visible: card.messageRole === "assistant"; enabled: !card.locked
                onClicked: bridge.readMessage(card.index)
            }
            HudButton {
                objectName: "editMessageButton"; text: "Edit & resend"; implicitHeight: 26; font.pixelSize: 10
                visible: card.messageRole === "user"; enabled: !card.locked
                onClicked: bridge.editMessage(card.index)
            }
        }
        Repeater {
            model: card.messageBlocks
            delegate: ColumnLayout {
                required property var modelData
                Layout.fillWidth: true; spacing: 5
                Rectangle {
                    visible: modelData.kind === "code"
                    Layout.fillWidth: true; implicitHeight: 30; radius: 5; color: "#192f3b"
                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 4
                        Text { Layout.fillWidth: true; text: modelData.language || "Code"; color: "#84b9bd"; font.pixelSize: 10; elide: Text.ElideRight }
                        HudButton {
                            objectName: "copyCodeButton"; text: "Copy code"; implicitHeight: 24; font.pixelSize: 10
                            onClicked: bridge.copyText(modelData.text)
                        }
                    }
                }
                TextEdit {
                    objectName: "conversationMessageBody"
                    Layout.fillWidth: true
                    text: modelData.text; color: "#cbdde5"; font.pixelSize: bridge.conversationFontSize
                    font.family: modelData.kind === "code" ? "monospace" : "Segoe UI"
                    readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap
                    textFormat: modelData.kind === "markdown" ? TextEdit.RichText : TextEdit.PlainText
                    onLinkActivated: function(link) { bridge.openLink(link) }
                    Accessible.name: card.messageRole + " message"
                }
            }
        }
        Repeater {
            model: card.messageAttachments
            delegate: HudButton {
                required property var modelData
                Layout.fillWidth: true; text: modelData.name; glyph: "⌑"; implicitHeight: 30; font.pixelSize: 11
                onClicked: card.previewRequested(modelData)
            }
        }
    }
}
