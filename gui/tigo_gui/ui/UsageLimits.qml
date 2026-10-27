import QtQuick
import QtQuick.Layouts

Rectangle {
    id: panel
    objectName: "usageLimitsPanel"
    property bool active: true
    visible: bridge.codexAccount.visible
    implicitHeight: content.implicitHeight + 20
    radius: 12; color: "#0c1d25"; border.color: "#284951"
    Component.onCompleted: if (active && visible) Qt.callLater(bridge.refreshUsage)
    onActiveChanged: if (active && visible) Qt.callLater(bridge.refreshUsage)
    onVisibleChanged: if (active && visible) Qt.callLater(bridge.refreshUsage)
    ColumnLayout {
        id: content
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
        anchors.margins: 10; spacing: 7
        RowLayout {
            Layout.fillWidth: true
            Text { text: "CODEX LIMITS"; color: "#91c9c4"; font.pixelSize: 10; font.letterSpacing: 1.1 }
            Text { Layout.fillWidth: true; text: bridge.codexAccount.updatedLabel; color: bridge.codexAccount.stale ? "#deb98a" : "#6f989f"; font.pixelSize: 9; elide: Text.ElideRight }
            HudButton {
                objectName: "refreshUsageButton"; text: bridge.codexAccount.loading ? "Reading..." : "Refresh"
                implicitHeight: 25; font.pixelSize: 9
                enabled: !bridge.codexAccount.loading && !bridge.codexAccount.needsSignIn && !bridge.fullProfile.busy && !bridge.updates.installing
                onClicked: bridge.refreshUsage()
            }
            HudButton {
                objectName: "hideUsageButton"; text: "×"; implicitHeight: 25; implicitWidth: 25; font.pixelSize: 14
                Accessible.name: "Hide Codex usage limits"
                onClicked: bridge.codexAccount.setVisible(false)
            }
        }
        Text { Layout.fillWidth: true; text: bridge.codexAccount.scope; color: "#7195a0"; font.pixelSize: 9; elide: Text.ElideRight }
        RowLayout {
            Layout.fillWidth: true; spacing: 16
            Repeater {
                model: bridge.codexAccount.windows
                ColumnLayout {
                    required property var modelData
                    Layout.fillWidth: true; Layout.preferredWidth: 1; spacing: 4
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: modelData.label; color: "#9db9c2"; font.pixelSize: 11 }
                        Text { text: modelData.summary; color: !modelData.known ? "#78919c" : (modelData.remaining <= 10 ? "#f29bad" : "#91e4ce"); font.pixelSize: 11 }
                    }
                    Rectangle {
                        Layout.fillWidth: true; implicitHeight: 4; radius: 2; color: "#21343e"
                        Rectangle {
                            height: parent.height; width: parent.width * modelData.remaining / 100; radius: 2
                            visible: modelData.known; color: modelData.remaining <= 10 ? "#e7899c" : "#68cab3"
                        }
                    }
                    Text { Layout.fillWidth: true; text: modelData.reset; color: "#7195a0"; font.pixelSize: 9; wrapMode: Text.WordWrap }
                }
            }
        }
        Text { Layout.fillWidth: true; text: bridge.codexAccount.status; color: "#7297a2"; font.pixelSize: 9; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight }
    }
}
