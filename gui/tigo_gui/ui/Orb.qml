import QtQuick

// Cache the artwork/mask and dial separately from the moving filaments.
// Only the light procedural overlay is repainted on animation frames.
Item {
    id: orb
    objectName: "activityCore"
    property bool active: false
    property bool listening: false
    property real targetLevel: 0
    property string stage: "idle"
    property bool animate: true
    property real level: 0
    property real phase: 0
    property real elapsed: 0
    property real stateAge: 0
    readonly property real radius: Math.min(width, height) * 0.355
    readonly property real breath: Math.sin(elapsed * (mode === "failed" ? 1.4 : 1.05))
    readonly property real swell: 1 + breath * 0.018 + level * 0.055
    readonly property string mode: {
        if (listening || stage === "recording") return "listening"
        if (["loading", "starting", "connecting"].indexOf(stage) >= 0) return "connecting"
        if (stage === "planning") return "thinking"
        if (["transcribing", "acting", "verifying", "complete", "failed", "stopping", "stopped", "speaking"].indexOf(stage) >= 0) return stage
        return active ? "thinking" : "idle"
    }
    readonly property string stateLabel: {
        switch (mode) {
        case "listening": return "LISTENING"
        case "connecting": return "PREPARING"
        case "transcribing": return "DECODING VOICE"
        case "speaking": return "SPEAKING"
        case "thinking": return "THINKING"
        case "acting": return "IN MOTION"
        case "verifying": return "VERIFYING"
        case "complete": return "COMPLETE"
        case "failed": return "NEEDS ATTENTION"
        case "stopping": return "STOPPING"
        case "stopped": return "STOPPED"
        default: return "READY"
        }
    }
    property real motionRate: {
        switch (mode) {
        case "speaking": return 18
        case "thinking": return 26
        case "acting": return 68
        case "verifying": return 34
        case "listening": return 14 + level * 24
        case "transcribing": return 24
        case "connecting": return 18
        case "complete": return 10
        case "failed": return 7
        case "stopping": return 5
        case "stopped": return 0
        default: return 5
        }
    }
    property color accent: {
        switch (mode) {
        case "speaking": return "#91e9ff"
        case "thinking": return "#b8a7ff"
        case "acting": return "#61d9ff"
        case "verifying": return "#ffd493"
        case "listening": return "#69f9d9"
        case "transcribing": return "#9cbdff"
        case "complete": return "#8af1bb"
        case "failed": return "#ff8ba9"
        case "stopped": case "stopping": return "#91a4b7"
        case "connecting": return "#91c4e0"
        default: return "#62e9df"
        }
    }
    readonly property bool animationRunning: clock.running
    implicitWidth: 380
    implicitHeight: 380

    Behavior on accent { enabled: orb.animate; ColorAnimation { duration: 380 } }
    Behavior on motionRate { enabled: orb.animate; NumberAnimation { duration: 420; easing.type: Easing.InOutQuad } }
    onModeChanged: { stateAge = 0; artwork.requestPaint() }
    onAccentChanged: { dial.requestPaint(); artwork.requestPaint() }
    onAnimateChanged: artwork.requestPaint()
    onTargetLevelChanged: { if (!clock.running) artwork.requestPaint() }

    // Fractional rotations must not wrap at 360: that used to snap the image
    // and filament bands back to unrelated orientations every full turn.
    function advance(seconds) {
        // Discard long stalls/resume gaps rather than teleporting the core.
        let dt = Math.max(0, Math.min(0.05, seconds))
        elapsed += dt
        stateAge += dt
        phase += motionRate * dt
        let target = listening || mode === "listening" ? Math.max(0, Math.min(1, targetLevel)) : 0
        let tau = target > level ? 0.045 : 0.17
        level += (target - level) * (1 - Math.exp(-dt / tau))
        artwork.requestPaint()
    }

    FrameAnimation {
        id: clock
        objectName: "coreFrameClock"
        running: orb.visible && orb.animate && orb.width > 0 && orb.height > 0 && orb.mode !== "stopped"
        onTriggered: orb.advance(frameTime)
    }

    Canvas {
        id: coreTexture
        objectName: "coreTexture"
        // A small, retained texture: loading, scaling and the radial mask run
        // only on load/resize. Rotation and breathing are scene-graph transforms.
        width: orb.radius * 2.28; height: width
        x: orb.width / 2 - width / 2; y: orb.height * 0.44 - height / 2
        rotation: orb.phase * 0.18
        scale: orb.swell
        opacity: orb.mode === "stopped" ? 0.38 : (orb.mode === "failed" ? 0.48 : 0.82)
        property url coreSource: Qt.resolvedUrl("energy-core.png")
        Component.onCompleted: loadImage(coreSource)
        onImageLoaded: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            let ctx = getContext("2d")
            ctx.reset()
            if (!isImageLoaded(coreSource) || orb.radius <= 0) return
            ctx.translate(width / 2, height / 2)
            let r = orb.radius, size = r * 2.48
            ctx.drawImage(coreSource, -size / 2, -size / 2, size, size)
            ctx.globalCompositeOperation = "destination-in"
            let mask = ctx.createRadialGradient(0, 0, r * 0.65, 0, 0, r * 1.12)
            mask.addColorStop(0, "#ffffff"); mask.addColorStop(1, "rgba(255,255,255,0)")
            ctx.fillStyle = mask
            ctx.fillRect(-width / 2, -height / 2, width, height)
        }
    }

    Canvas {
        id: dial
        objectName: "coreDial"
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            let ctx = getContext("2d")
            ctx.reset()
            let r = orb.radius
            if (r <= 0) return
            ctx.translate(width / 2, height * 0.44)
            ctx.strokeStyle = orb.accent; ctx.lineWidth = 1
            ctx.globalAlpha = 0.13
            ctx.beginPath(); ctx.arc(0, 0, r * 1.17, 0, Math.PI * 2); ctx.stroke()
            // Group equal-alpha ticks into two paths instead of 60 strokes.
            for (let group = 0; group < 2; group++) {
                ctx.globalAlpha = group === 0 ? 0.42 : 0.17
                ctx.beginPath()
                for (let i = 0; i < 60; i++) {
                    if ((i % 5 === 0) !== (group === 0)) continue
                    let a = i * Math.PI / 30
                    let outer = group === 0 ? 1.205 : 1.19
                    ctx.moveTo(Math.cos(a) * r * 1.16, Math.sin(a) * r * 1.16)
                    ctx.lineTo(Math.cos(a) * r * outer, Math.sin(a) * r * outer)
                }
                ctx.stroke()
            }
        }
    }

    Canvas {
        id: artwork
        objectName: "activityArtwork"
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            let ctx = getContext("2d")
            ctx.reset()
            let cx = width / 2, cy = height * 0.44
            let r = orb.radius
            if (r <= 0) return
            let t = orb.elapsed, angle = orb.phase * Math.PI / 180
            let mode = orb.mode, audio = orb.level, color = orb.accent
            let breath = orb.breath, swell = orb.swell
            ctx.translate(cx, cy)

            function strokeCircle(radius, alpha, thickness) {
                ctx.globalAlpha = alpha
                ctx.strokeStyle = color; ctx.lineWidth = thickness
                ctx.beginPath(); ctx.arc(0, 0, radius, 0, Math.PI * 2); ctx.stroke()
            }
            function dot(x, y, size, alpha) {
                ctx.globalAlpha = alpha; ctx.fillStyle = color
                ctx.beginPath(); ctx.arc(x, y, size, 0, Math.PI * 2); ctx.fill()
            }

            // Project four different, gently deforming filament loops. Their
            // shape, not just their speed/color, follows the runtime activity.
            for (let band = 0; band < 4; band++) {
                ctx.save()
                ctx.rotate(band * Math.PI / 4 + angle * (band % 2 ? -0.32 : 0.24))
                let tilt = mode === "thinking" ? 0.36 + 0.17 * Math.sin(t * 0.7 + band) : 0.48
                let gradient = ctx.createLinearGradient(-r, -r * tilt, r, r * tilt)
                gradient.addColorStop(0, "#327699")
                gradient.addColorStop(0.5, color)
                gradient.addColorStop(1, "#d1fff5")
                ctx.strokeStyle = gradient; ctx.lineWidth = band % 2 ? 1 : 1.5
                ctx.globalAlpha = mode === "stopped" ? 0.16 : 0.48
                ctx.beginPath()
                for (let j = 0; j <= 96; j++) {
                    let a = j * Math.PI * 2 / 96
                    let deformation = mode === "listening" ? audio * 0.11 : 0.025
                    let radius = r * (0.86 + deformation * Math.sin(a * 6 + t * 2 + band)) * swell
                    let x = Math.cos(a) * radius
                    let y = Math.sin(a) * radius * tilt + Math.sin(a * 3 + t + band) * r * 0.035
                    if (j === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
                }
                ctx.closePath(); ctx.stroke(); ctx.restore()
            }

            // Sparse particles follow bounded orbits, with faster action trails.
            for (let i = 0; i < 24; i++) {
                let a = i * 2.39996 + angle * (i % 2 ? -1 : 1)
                let radius = r * (0.82 + (i % 5) * 0.065) * swell
                let x = Math.cos(a) * radius, y = Math.sin(a) * radius
                dot(x, y, i % 4 === 0 ? 1.8 : 0.85, i % 4 === 0 ? 0.85 : 0.38)
                if (mode === "acting" && i % 4 === 0) {
                    ctx.globalAlpha = 0.55; ctx.strokeStyle = color; ctx.lineWidth = 1.6
                    ctx.beginPath(); ctx.arc(0, 0, radius, a - 0.32, a - 0.04); ctx.stroke()
                }
            }

            if (mode === "listening" || mode === "transcribing") {
                // Audio-reactive amplitude, not a fabricated live waveform.
                ctx.globalAlpha = 0.9; ctx.strokeStyle = color; ctx.lineWidth = 1.8
                ctx.beginPath()
                for (let i = 0; i <= 64; i++) {
                    let u = i / 64, x = (u - 0.5) * r * 1.22
                    let envelope = Math.sin(u * Math.PI)
                    let amplitude = mode === "listening" ? 0.012 + audio * 0.19 : 0.075
                    let y = Math.sin(u * 28 - t * 5) * Math.cos(u * 11 + t * 2) * r * amplitude * envelope
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
                }
                ctx.stroke()
            }
            if (mode === "speaking") {
                // A stylized output pulse, not a measured speaker waveform.
                strokeCircle(r * (1.02 + 0.035 * Math.sin(t * 7)), 0.55, 1.6)
                strokeCircle(r * (1.08 + 0.02 * Math.sin(t * 7 - 1)), 0.25, 1)
            }
            if (mode === "verifying") {
                ctx.save()
                ctx.beginPath(); ctx.arc(0, 0, r * 0.84, 0, Math.PI * 2); ctx.clip()
                let y = Math.sin(t * 1.8) * r * 0.8
                let scan = ctx.createLinearGradient(0, y - r * 0.28, 0, y)
                scan.addColorStop(0, "rgba(255,212,147,0)"); scan.addColorStop(1, "rgba(255,212,147,0.21)")
                ctx.globalAlpha = 1; ctx.fillStyle = scan
                ctx.fillRect(-r, y - r * 0.28, r * 2, r * 0.28)
                ctx.strokeStyle = color; ctx.lineWidth = 1
                ctx.beginPath(); ctx.moveTo(-r, y); ctx.lineTo(r, y); ctx.stroke()
                ctx.restore()
            }
            if (mode === "connecting" || mode === "transcribing") {
                ctx.globalAlpha = 0.9; ctx.strokeStyle = color; ctx.lineWidth = 2
                ctx.beginPath(); ctx.arc(0, 0, r * 1.075, angle, angle + Math.PI * 0.65); ctx.stroke()
            }
            if (mode === "complete") {
                // Completion waves settle after two seconds, leaving a calm halo.
                for (let i = 0; i < 3; i++) {
                    let progress = Math.min(1, Math.max(0, (orb.stateAge - i * 0.28) / 1.3))
                    if (progress > 0 && progress < 1) strokeCircle(r * (0.7 + progress * 0.46), (1 - progress) * 0.65, 1.6)
                }
                strokeCircle(r * 1.075, 0.28, 1.3)
            }
            if (mode === "failed" || mode === "stopping") {
                for (let i = 0; i < 4; i++) {
                    ctx.globalAlpha = 0.35 + (breath + 1) * 0.12
                    ctx.strokeStyle = color; ctx.lineWidth = 2
                    ctx.beginPath(); ctx.arc(0, 0, r * 1.06, i * Math.PI / 2 + 0.15, i * Math.PI / 2 + 1.05); ctx.stroke()
                }
            }
            ctx.globalAlpha = 1
        }
    }

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom; anchors.bottomMargin: height * 0.5 + 4
        spacing: 8
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 4; height: 4; radius: 2; color: orb.accent
        }
        Text {
            objectName: "activityCoreLabel"
            text: orb.stateLabel; color: orb.accent
            font.pixelSize: 9; font.letterSpacing: 2.6
        }
    }
}
