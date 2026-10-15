import QtQuick
import QtQuick.Controls.Basic

Slider {
    id: control
    implicitHeight: 30
    hoverEnabled: true
    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: control.availableWidth; height: 4; radius: 2; color: "#294351"
        Rectangle { width: control.visualPosition * parent.width; height: parent.height; radius: 2; color: "#39cfbf" }
    }
    handle: Rectangle {
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        implicitWidth: 18; implicitHeight: 18; radius: 9
        color: control.pressed ? "#b9fff0" : "#47e1cd"
        border.width: control.activeFocus || control.hovered ? 2 : 1
        border.color: "#b4fff0"
    }
}
