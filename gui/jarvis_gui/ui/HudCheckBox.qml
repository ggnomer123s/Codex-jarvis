import QtQuick
import QtQuick.Controls.Basic

CheckBox {
    id: control
    implicitHeight: 30
    indicator: Rectangle {
        x: 0; y: (control.height - height) / 2
        width: 18; height: 18; radius: 5
        color: control.checked ? "#2cd9ce" : "#0b1b25"
        border.color: control.checked ? "#63f1df" : "#345463"
        Text { anchors.centerIn: parent; text: control.checked ? "✓" : ""; color: "#071a20"; font.pixelSize: 13; font.bold: true }
    }
    contentItem: Text {
        text: control.text; color: control.enabled ? "#b8eee4" : "#627c87"
        leftPadding: 30; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter
    }
}
