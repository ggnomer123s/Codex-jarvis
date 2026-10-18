"""Wayland layer-shell indicator, run by the system Python with GTK bindings.

Only four thin edge surfaces and a banner are created. No fullscreen input
surface, keyboard grab, session lock, screenshot or physical-input hook.
Parent-owned stdin controls visibility; EOF removes every surface.
"""
import json
import math
import os
import sys


def clickable_rect(bounds, width, height):
    """Outward-rounded button bounds clipped to surface-local logical pixels.

    None means an empty input region, never the GDK default of full input.
    Monitor offsets and device pixel scale do not belong in this coordinate space.
    """
    if bounds is None or not all(math.isfinite(v) for v in (*bounds, width, height)):
        return None
    x, y, w, h = bounds
    if w <= 0 or h <= 0:
        return None
    left, top = max(0, math.floor(x)), max(0, math.floor(y))
    right, bottom = min(width, math.ceil(x + w)), min(height, math.ceil(y + h))
    if right <= left or bottom <= top:
        return None
    return left, top, int(right - left), int(bottom - top)


def main():
    os.environ['GDK_BACKEND'] = 'wayland'
    # Upstream's Python example requires loading layer-shell before GTK links
    # libwayland-client, so its protocol hooks are installed in the right order.
    from ctypes import CDLL
    CDLL('libgtk4-layer-shell.so.0')
    import cairo
    import gi
    gi.require_foreign('cairo')
    gi.require_version('Gdk', '4.0')
    gi.require_version('Gtk', '4.0')
    gi.require_version('Gtk4LayerShell', '1.0')
    from gi.repository import Gdk, GLib, Gtk, Gtk4LayerShell as Layer

    Gtk.init()
    if not Layer.is_supported():
        raise RuntimeError('This compositor does not support GTK4 layer-shell.')
    display = Gdk.Display.get_default()
    css = Gtk.CssProvider()
    css.load_from_data(b'''
window { background: transparent; }
.edge { background: linear-gradient(90deg, #30d4cf, #78b8ff, #ad8dff); }
.banner { background: #10212f; border: 1px solid #54cbd2; border-radius: 16px;
          padding: 12px 18px; color: #e3f5ff; }
.heading { font-weight: 700; font-size: 15px; color: #89f2e9; }
.hint { font-size: 12px; color: #c4d9e6; }
button { background: #19505d; color: #e7ffff; border: 1px solid #53cbd1;
         border-radius: 10px; padding: 9px 15px; }
''')
    Gtk.StyleContext.add_provider_for_display(display, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    windows, hints = [], []
    visible = False

    def surface(monitor, edges, child, name, button=None):
        win = Gtk.Window(title='Tigo screen activity')
        win.set_decorated(False)
        Layer.init_for_window(win)
        Layer.set_namespace(win, 'tigo-screen-' + name)
        Layer.set_layer(win, Layer.Layer.OVERLAY)
        Layer.set_monitor(win, monitor)
        Layer.set_keyboard_mode(win, Layer.KeyboardMode.NONE)
        # 0 avoids panels' reserved work area; -1 reaches the actual output
        # edges, including when a fullscreen window covers the panels.
        Layer.set_exclusive_zone(win, -1)
        for edge in edges:
            Layer.set_anchor(win, edge, True)
        win.set_child(child)
        pending = [None, 0]

        def input_region(*_):
            if pending[0] is not None:
                pending[0].disconnect(pending[1])
                pending[:] = [None, 0]
            native = win.get_surface()
            if native is not None:
                region = cairo.Region()  # Edges and banner text pass clicks through.
                if button is not None and button.get_width() > 1 and button.get_height() > 1:
                    ok, rect = button.compute_bounds(win)
                    bounds = (rect.get_x(), rect.get_y(), rect.get_width(), rect.get_height()) if ok else None
                    target = clickable_rect(bounds, native.get_width(), native.get_height())
                    if target is not None:
                        region.union(cairo.RectangleInt(*target))
                native.set_input_region(region)
                win.queue_draw()  # Commit the region computed after allocation.

        def schedule_input(*_):
            clock = win.get_frame_clock()
            if pending[0] is None and clock is not None:
                # Idle can run before GTK's first allocation (a 1x1 button).
                # One after-paint callback sees final widget coordinates without
                # a continuous tick/polling loop or a guessed settle timeout.
                pending[:] = [clock, clock.connect('after-paint', input_region)]

        def realized(*_):
            win.get_surface().connect('layout', schedule_input)
            input_region()

        def unmapped(*_):
            if pending[0] is not None:
                pending[0].disconnect(pending[1])
                pending[:] = [None, 0]

        win.connect('realize', realized)
        win.connect('map', schedule_input)
        win.connect('unmap', unmapped)
        windows.append(win)
        return win

    def takeover(*_):
        apply({**last, 'active': False})
        print('{"takeover":true}', flush=True)

    def rebuild(*_):
        for win in windows:
            win.destroy()
        windows.clear()
        hints.clear()
        monitors = display.get_monitors()
        for index in range(monitors.get_n_items()):
            monitor = monitors.get_item(index)
            for side in (Layer.Edge.TOP, Layer.Edge.BOTTOM, Layer.Edge.LEFT, Layer.Edge.RIGHT):
                horizontal = side in (Layer.Edge.TOP, Layer.Edge.BOTTOM)
                box = Gtk.Box()
                box.add_css_class('edge')
                box.set_size_request(-1 if horizontal else 4, 4 if horizontal else -1)
                anchors = [side, Layer.Edge.LEFT, Layer.Edge.RIGHT] if horizontal else [side, Layer.Edge.TOP, Layer.Edge.BOTTOM]
                surface(monitor, anchors, box, 'edge')
            banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
            banner.add_css_class('banner')
            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            heading = Gtk.Label(label='Tigo uses the screen')
            heading.set_xalign(0)
            heading.add_css_class('heading')
            hint = Gtk.Label(label='Use Return control to stop the current task')
            hint.set_xalign(0)
            hint.add_css_class('hint')
            labels.append(heading)
            labels.append(hint)
            button = Gtk.Button(label='Return control')
            button.set_focusable(False)
            button.connect('clicked', takeover)
            banner.append(labels)
            banner.append(button)
            win = surface(monitor, [Layer.Edge.TOP], banner, 'banner', button=button)
            Layer.set_margin(win, Layer.Edge.TOP, 16)
            hints.append((heading, hint, button))
        apply(last)

    last = {'active': False}

    def apply(data):
        nonlocal visible, last
        last = data
        visible = data.get('active') is True
        ru = data.get('ru') is True
        shortcut = data.get('shortcut') is True
        for heading, hint, button in hints:
            # Escapes keep source scripts ASCII for the repository's policy.
            heading.set_text('\u0422\u0438\u0433\u043e \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442 \u0441 \u044d\u043a\u0440\u0430\u043d\u043e\u043c' if ru else 'Tigo uses the screen')
            hint.set_text(('Ctrl+Alt+Shift+F10 \u2014 \u0432\u0435\u0440\u043d\u0443\u0442\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435' if ru else 'Ctrl+Alt+Shift+F10 to stop the current task') if shortcut else ('\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443, \u0447\u0442\u043e\u0431\u044b \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443' if ru else 'Use Return control to stop the current task'))
            button.set_label('\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435' if ru else 'Return control')
        for win in windows:
            win.set_visible(visible)

    loop = GLib.MainLoop()
    buffer = bytearray()

    def incoming(fd, condition):
        chunk = os.read(fd, 4096)
        if not chunk:
            loop.quit()
            return False
        buffer.extend(chunk)
        if len(buffer) > 8192:
            loop.quit()
            return False
        while b'\n' in buffer:
            line, _, rest = buffer.partition(b'\n')
            buffer[:] = rest
            data = json.loads(line)
            if not isinstance(data, dict):
                loop.quit()
                return False
            apply(data)
        return True

    rebuild()
    display.get_monitors().connect('items-changed', rebuild)
    GLib.io_add_watch(sys.stdin.fileno(), GLib.IO_IN | GLib.IO_HUP, incoming)
    print('{"ready":true}', flush=True)
    loop.run()
    for win in windows:
        win.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
