import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: control
    implicitHeight: 44
    font.pixelSize: 12
    hoverEnabled: true
    leftPadding: 14; rightPadding: 34
    background: Rectangle {
        radius: 9; color: "#0a1720"
        border.color: control.activeFocus || control.hovered ? "#3b877d" : "#2b4654"
    }
    contentItem: TextField {
        text: control.editable ? control.editText : control.displayText
        readOnly: !control.editable
        selectByMouse: control.editable
        color: "#d6edf0"; font: control.font; padding: 0
        verticalAlignment: Text.AlignVCenter
        background: null
        onTextEdited: if (control.editable) control.editText = text
        onAccepted: if (control.editable) control.accepted()
    }
    indicator: Text {
        x: control.width - 24; y: (control.height - height) / 2
        text: "⌄"; color: "#76c6be"; font.pixelSize: 18
    }
    delegate: ItemDelegate {
        required property var modelData
        required property int index
        width: control.width
        text: control.textRole ? modelData[control.textRole] : modelData
        highlighted: control.highlightedIndex === index
        contentItem: Text { text: parent.text; color: "#d3e9eb"; font.pixelSize: 12; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { color: parent.highlighted ? "#23443f" : "#10212c" }
    }
    popup: Popup {
        y: control.height + 4; width: control.width
        padding: 4; implicitHeight: Math.min(contentItem.implicitHeight + 8, 260)
        background: Rectangle { radius: 9; color: "#10212c"; border.color: "#365761" }
        contentItem: ListView {
            clip: true; implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }
}
