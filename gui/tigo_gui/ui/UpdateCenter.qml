import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Popup {
    id: panel
    objectName: "updateCenter"
    property bool hasDraft: false
    property bool taskLocked: false
    anchors.centerIn: parent
    width: Math.min(parent.width - 48, 760)
    height: Math.min(parent.height - 64, 710)
    padding: 28
    modal: true; focus: true
    closePolicy: bridge.updates.installing ? Popup.NoAutoClose : Popup.CloseOnEscape | Popup.CloseOnPressOutside
    background: Rectangle { color: "#101d28"; radius: 20; border.color: "#35505e" }
    Overlay.modal: Rectangle { color: "#bd060d13" }
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: bridge.reducedMotion ? 0 : 180 }
            NumberAnimation { property: "scale"; from: 0.985; to: 1; duration: bridge.reducedMotion ? 0 : 220; easing.type: Easing.OutCubic }
        }
    }
    exit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: bridge.reducedMotion ? 0 : 120 } }
    contentItem: ColumnLayout {
        spacing: 16
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 5
                Text { text: "Keep Tigo current."; color: "#e4f2f6"; font.pixelSize: 27; font.weight: Font.Light }
                Text { text: "Updates, release notes and installation status."; color: "#87a4b4"; font.pixelSize: 12 }
            }
            Item { Layout.fillWidth: true }
            HudButton { objectName: "closeUpdatesButton"; text: "Close"; implicitHeight: 32; enabled: !bridge.updates.installing; onClicked: panel.close() }
        }
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            Repeater {
                model: [{label: "RUNNING VERSION", value: bridge.updates.currentVersion},
                        {label: "AVAILABLE ON MAIN", value: bridge.updates.latestVersion || "Not checked"}]
                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true; implicitHeight: 81; radius: 12; color: "#142733"; border.color: "#29434f"
                    Column { anchors.fill: parent; anchors.margins: 16; spacing: 8
                        Text { text: modelData.label; color: "#7797a8"; font.pixelSize: 9; font.letterSpacing: 1.2 }
                        Text { text: modelData.value; color: "#a2e9df"; font.pixelSize: 20 }
                    }
                }
            }
        }
        Text { objectName: "updateStatus"; Layout.fillWidth: true; text: bridge.updates.message; color: bridge.updates.state === "error" ? "#f3aaa9" : "#a4c5cf"; wrapMode: Text.WordWrap; font.pixelSize: 12 }
        Rectangle {
            id: progressRail
            visible: bridge.updates.busy; Layout.fillWidth: true; implicitHeight: 3; radius: 1.5; color: "#203a45"; clip: true
            Rectangle {
                width: progressRail.width * 0.25; height: parent.height; radius: 1.5; color: "#6bdecf"
                NumberAnimation on x { running: panel.visible && bridge.updates.busy && !bridge.reducedMotion; loops: Animation.Infinite; from: -progressRail.width * 0.25; to: progressRail.width; duration: 1350; easing.type: Easing.InOutSine }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Text { text: bridge.updates.commits ? bridge.updates.commits + " new commits · " + bridge.updates.revision : "WHAT'S NEW"; color: "#7ca3b1"; font.pixelSize: 10; font.letterSpacing: 0.6 }
            Item { Layout.fillWidth: true }
            HudButton { text: "View commits"; implicitHeight: 28; font.pixelSize: 10; enabled: bridge.updates.revision.length > 0; onClicked: bridge.updates.openHistory() }
        }
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            TextArea {
                objectName: "updateNotes"
                text: bridge.updates.notes || "Check for updates to see the latest release notes.\n\nChecks do not install anything or change your working files."
                textFormat: TextEdit.PlainText
                readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap
                color: "#bfd2dc"; font.pixelSize: 12; padding: 16
                background: Rectangle { color: "#0b1721"; radius: 12; border.color: "#223b48" }
            }
        }
        Text { Layout.fillWidth: true; visible: bridge.updates.lastResult.length > 0; text: "Last installation: " + bridge.updates.lastResult; color: "#a4c7b6"; wrapMode: Text.WordWrap; font.pixelSize: 11 }
        Text {
            Layout.fillWidth: true
            text: panel.hasDraft ? "Save or clear your draft before updating." : "Installation closes Tigo and opens a terminal for system prompts. On Arch/CachyOS it includes the normal full system upgrade. Your settings and login are retained."
            color: panel.hasDraft ? "#e8bf86" : "#7996a5"; font.pixelSize: 10; wrapMode: Text.WordWrap
        }
        RowLayout {
            Layout.fillWidth: true; spacing: 10
            HudButton { objectName: "checkUpdatesButton"; Layout.fillWidth: true; text: "Check for updates"; enabled: !bridge.updates.busy; onClicked: bridge.updates.check() }
            HudButton { text: "Cancel check"; visible: bridge.updates.state === "checking" || bridge.updates.state === "preparing"; onClicked: bridge.updates.cancel() }
            HudButton { objectName: "installUpdateButton"; Layout.fillWidth: true; text: "Update and restart"; primary: true; enabled: bridge.updates.state === "available" && !panel.taskLocked && !panel.hasDraft && bridge.attachments.length === 0; onClicked: bridge.installUpdate(panel.hasDraft) }
        }
    }
}
