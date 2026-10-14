import QtQuick

Item {
    id: orb
    property bool active: false
    property bool listening: false
    property real level: 0
    property real targetLevel: 0
    property string stage: "idle"
    property real ripple: 0
    property real phase: 0
    property bool animate: true
    property color accent: stage === "failed" ? "#f598a0" : (stage === "verifying" ? "#8dbdff" : (stage === "complete" ? "#8af1bb" : (listening ? "#8bf6eb" : "#43e8da")))
    implicitWidth: 380
    implicitHeight: 380

    Timer {
        interval: 33; repeat: true; running: orb.visible && orb.animate
        onTriggered: {
            orb.phase = (orb.phase + (orb.active ? 0.75 : 0.25)) % 360
            let next = orb.level + (orb.targetLevel - orb.level) * (orb.targetLevel > orb.level ? 0.65 : 0.22)
            if (next - orb.level > 0.12) orb.ripple = 1
            orb.level = next
            orb.ripple *= 0.88
        }
    }
    onPhaseChanged: rings.requestPaint()
    onLevelChanged: rings.requestPaint()
    Repeater {
        model: 9
        Rectangle {
            required property int index
            anchors.centerIn: parent
            width: orb.width * (0.39 + index * 0.063) + orb.level * 18
            height: width; radius: width / 2
            color: Qt.rgba(0.15, 0.9, 0.83, 0.010 + (8 - index) * 0.0015)
        }
    }
    Canvas {
        id: rings
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            let ctx = getContext("2d")
            ctx.reset()
            let cx = width / 2, cy = height / 2, r = Math.min(width, height) * 0.40
            ctx.translate(cx, cy)
            function circle(radius, color, thickness) {
                ctx.beginPath(); ctx.arc(0, 0, radius, 0, Math.PI * 2)
                ctx.strokeStyle = color; ctx.lineWidth = thickness; ctx.stroke()
            }
            circle(r * 1.13, "#1a353e", 1)
            circle(r * 0.94, "#1a4149", 1)
            circle(r * 0.73, "#255d62", 1)
            circle(r * 0.69, "#122f39", 1)
            if (orb.ripple > 0.02) circle(r * (0.74 + (1 - orb.ripple) * 0.35), Qt.rgba(0.5, 0.95, 0.86, orb.ripple * 0.5), 2)
            for (let i = 0; i < 100; i++) {
                let a = i * Math.PI * 2 / 100
                let longTick = i % 5 === 0
                ctx.beginPath()
                ctx.moveTo(Math.cos(a) * r * 1.06, Math.sin(a) * r * 1.06)
                ctx.lineTo(Math.cos(a) * r * (longTick ? 1.11 : 1.085), Math.sin(a) * r * (longTick ? 1.11 : 1.085))
                ctx.strokeStyle = longTick ? "#4c8b8e" : "#244750"; ctx.lineWidth = 1; ctx.stroke()
            }
            ctx.save(); ctx.rotate(orb.phase * Math.PI / 180)
            for (let i = 0; i < 3; i++) {
                ctx.beginPath(); ctx.arc(0, 0, r, i * 2.094, i * 2.094 + 1.37)
                ctx.strokeStyle = orb.accent; ctx.lineWidth = 3; ctx.stroke()
                ctx.beginPath(); ctx.arc(0, 0, r * 0.89, i * 2.094 + 0.2, i * 2.094 + 0.6)
                ctx.strokeStyle = "#338388"; ctx.lineWidth = 5; ctx.stroke()
            }
            ctx.restore(); ctx.save(); ctx.rotate(-orb.phase * Math.PI / 180)
            for (let i = 0; i < 32; i++) {
                let a = i * Math.PI * 2 / 32
                ctx.beginPath(); ctx.arc(0, 0, r * 0.80 + orb.level * 9, a, a + 0.10)
                ctx.strokeStyle = i % 4 === 0 ? "#81f7e8" : "#27616a"; ctx.lineWidth = 2; ctx.stroke()
            }
            ctx.restore()
            circle(r * 0.56 + orb.level * 5, "#3bacac", 1)
            for (let i = 0; i < 4; i++) {
                let a = i * Math.PI / 2 + Math.PI / 4
                let x = Math.cos(a) * r * 1.13, y = Math.sin(a) * r * 1.13
                ctx.fillStyle = "#8af6e8"; ctx.fillRect(x - 2, y - 2, 4, 4)
            }
        }
    }
    Column {
        anchors.centerIn: parent
        spacing: 8
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "J"; color: "#d9fffa"; font.pixelSize: orb.width * 0.19; font.weight: Font.Light
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: orb.stage === "idle" ? "STANDBY" : orb.stage.toUpperCase()
            color: orb.accent; font.pixelSize: 10; font.letterSpacing: 3
        }
    }
}
