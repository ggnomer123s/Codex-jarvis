import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Popup {
    id: preview
    objectName: "attachmentPreview"
    property var fileInfo: ({})
    function show(value) { fileInfo = value; open() }
    anchors.centerIn: parent
    width: Math.min(700, parent.width - 60); height: Math.min(650, parent.height - 60)
    padding: 20; modal: true; focus: true
    background: Rectangle { radius: 16; color: "#111f2b"; border.color: "#345463" }
    Overlay.modal: Rectangle { color: "#b0081018" }
    ColumnLayout {
        anchors.fill: parent; spacing: 12
        Text { Layout.fillWidth: true; text: preview.fileInfo.name || "Attachment"; color: "#daf1f0"; font.pixelSize: 18; elide: Text.ElideMiddle }
        Text { Layout.fillWidth: true; text: (preview.fileInfo.path || "") + "\n" + Math.ceil((preview.fileInfo.size || 0) / 1024) + " KB"; color: "#799daa"; font.pixelSize: 11; wrapMode: Text.WrapAnywhere }
        Image {
            visible: preview.fileInfo.kind === "image"
            Layout.fillWidth: true; Layout.fillHeight: true
            source: preview.opened && visible ? preview.fileInfo.url || "" : ""
            sourceSize.width: 1000; sourceSize.height: 800; fillMode: Image.PreserveAspectFit
        }
        ScrollView {
            visible: preview.fileInfo.kind !== "image"
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            TextArea { text: preview.fileInfo.preview || "File reference"; readOnly: true; selectByMouse: true; textFormat: TextEdit.PlainText; wrapMode: TextEdit.Wrap; color: "#cbdde5"; font.pixelSize: 13; background: null }
        }
        Text { Layout.fillWidth: true; text: "Review before sending. Images are included in the request; other selected files may be read by Codex. Text previews show the first 8 KB."; color: "#94b4bd"; font.pixelSize: 11; wrapMode: Text.WordWrap }
        HudButton { Layout.alignment: Qt.AlignRight; text: "Close"; onClicked: preview.close() }
    }
}
