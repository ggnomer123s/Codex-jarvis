import QtQuick
import QtQuick.Controls.Basic

Button {
    id: control
    property bool primary: false
    property bool danger: false
    property string glyph: ""
    property bool motionEnabled: typeof bridge === "undefined" || !bridge.reducedMotion
    implicitHeight: 44
    implicitWidth: label.implicitWidth + 32
    hoverEnabled: true
    opacity: enabled ? 1 : 0.4
    scale: down ? 0.975 : 1
    Behavior on scale { enabled: control.motionEnabled; NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
    Behavior on opacity { enabled: control.motionEnabled; NumberAnimation { duration: 120 } }
    font.pixelSize: 13
    Accessible.name: text
    background: Rectangle {
        radius: 10
        color: control.primary ? (control.hovered ? "#78f5e8" : "#43e8da")
                               : (control.hovered ? "#1b303a" : "#101c25")
        border.color: control.danger ? "#914650" : (control.primary ? "#43e8da" : "#263945")
        Behavior on color { enabled: control.motionEnabled; ColorAnimation { duration: 140 } }
        Behavior on border.color { enabled: control.motionEnabled; ColorAnimation { duration: 160 } }
    }
    contentItem: Text {
        id: label
        text: (control.glyph ? control.glyph + "  " : "") + control.text
        color: control.primary ? "#071a20" : (control.danger ? "#ff9b9b" : "#d8e7ed")
        font.pixelSize: control.font.pixelSize
        font.family: control.font.family
        font.weight: control.primary ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
