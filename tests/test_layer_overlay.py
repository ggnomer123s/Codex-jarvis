"""Wayland input bounds and opt-in live protocol/geometry checks (no GUI input)."""
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'gui'))
from tigo_gui.layer_overlay import clickable_rect


class TestLayerInputBounds(unittest.TestCase):
    def test_fractional_button_is_outward_rounded_and_clipped_to_surface(self):
        self.assertEqual(clickable_rect((278.2, 13.8, 115.2, 37.1), 416, 64), (278, 13, 116, 38))
        self.assertEqual(clickable_rect((-3.5, -1.5, 10, 8), 100, 60), (0, 0, 7, 7))
        self.assertEqual(clickable_rect((390.1, 50.1, 50, 50), 416, 64), (390, 50, 26, 14))

    def test_empty_unallocated_invalid_or_off_surface_buttons_cannot_capture_input(self):
        for bounds in (None, (0, 0, 0, 30), (0, 0, 20, -1),
                       (500, 100, 20, 20), (float('nan'), 0, 20, 20)):
            with self.subTest(bounds=bounds):
                self.assertIsNone(clickable_rect(bounds, 416, 64))


def protocol_state(text):
    """Read only the tested client's layer and input-region requests."""
    regions, surfaces, inputs, layers, zones, keyboards = {}, {}, {}, {}, {}, {}
    for line in text.splitlines():
        m = re.search(r'get_layer_surface\(new id zwlr_layer_surface_v1[#@](\d+), wl_surface[#@](\d+),.*"(tigo-screen-[^"]+)"', line)
        if m:
            layer, surface, namespace = m.groups()
            surfaces[surface], layers[layer] = namespace, surface
        m = re.search(r'create_region\(new id wl_region[#@](\d+)\)', line)
        if m:
            regions[m[1]] = []
        m = re.search(r'wl_region[#@](\d+)\.add\(([^)]+)\)', line)
        if m:
            regions[m[1]].append(tuple(int(v.strip()) for v in m[2].split(',')))
        m = re.search(r'wl_surface[#@](\d+)\.set_input_region\(wl_region[#@](\d+)\)', line)
        if m:
            inputs[m[1]] = list(regions[m[2]])
        m = re.search(r'zwlr_layer_surface_v1[#@](\d+)\.set_exclusive_zone\((-?\d+)\)', line)
        if m:
            zones[layers[m[1]]] = int(m[2])
        m = re.search(r'zwlr_layer_surface_v1[#@](\d+)\.set_keyboard_interactivity\((\d+)\)', line)
        if m:
            keyboards[layers[m[1]]] = int(m[2])
    return [(name, inputs.get(surface), zones.get(surface), keyboards.get(surface))
            for surface, name in surfaces.items()]


@unittest.skipUnless(os.environ.get('TIGO_TEST_WAYLAND_OVERLAY') == '1',
                     'Explicit live Wayland helper check; displays the indicator')
class TestLiveWaylandOverlay(unittest.TestCase):
    def inventory(self, kind):
        return json.loads(subprocess.check_output(['hyprctl', '-j', kind], text=True, timeout=3))

    def layers(self):
        return [(monitor, surface) for monitor, data in self.inventory('layers').items()
                for surfaces in data['levels'].values() for surface in surfaces
                if surface.get('namespace', '').startswith('tigo-screen-')]

    def wait(self, condition):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if condition():
                return
            time.sleep(.05)
        self.fail('The live helper did not reach the expected geometry/input state.')

    def test_output_edges_clickthrough_localized_button_remap_and_eof_cleanup(self):
        if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') or not shutil.which('hyprctl'):
            self.skipTest('A live Hyprland session with hyprctl is required.')
        if self.layers():
            self.skipTest('Quit the real Tigo indicator before the live helper check.')
        with tempfile.TemporaryDirectory(prefix='tigo layer protocol ') as folder:
            trace = Path(folder)/'client.log'
            with trace.open('w') as log:
                process = subprocess.Popen(['/usr/bin/python3', str(ROOT/'gui/tigo_gui/layer_overlay.py')],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True,
                                           env={**os.environ, 'WAYLAND_DEBUG':'client'})
                ready = queue.Queue()
                threading.Thread(target=lambda: ready.put(process.stdout.readline()), daemon=True).start()
                try:
                    self.assertEqual(ready.get(timeout=5).strip(), '{"ready":true}')
                    def send(active, ru=False):
                        process.stdin.write(json.dumps({'active':active, 'ru':ru, 'shortcut':True})+'\n')
                        process.stdin.flush()
                    def state():
                        return protocol_state(trace.read_text(errors='replace'))
                    def button():
                        return [regions for name, regions, _, _ in state() if name=='tigo-screen-banner']
                    send(True)
                    self.wait(lambda:button() and all(r and r[0][2]>10 for r in button()))
                    english = button()
                    monitors = self.inventory('monitors')
                    for monitor in monitors:
                        name, x, y = monitor['name'], monitor['x'], monitor['y']
                        # GDK output geometry is logical and rotation-aware; use
                        # the compositor's own reported output size on scale 1.
                        if monitor['scale'] != 1 or monitor.get('transform', 0) != 0:
                            continue
                        w, h = monitor['width'], monitor['height']
                        edges = [(s['x'], s['y'], s['w'], s['h']) for output, s in self.layers()
                                 if output==name and s['namespace']=='tigo-screen-edge']
                        self.assertCountEqual(edges, [(x,y,w,4), (x,y+h-4,w,4), (x,y,4,h), (x+w-4,y,4,h)])
                    for name, regions, zone, keyboard in state():
                        self.assertEqual(zone, -1)
                        self.assertEqual(keyboard, 0)
                        if name=='tigo-screen-edge':
                            self.assertEqual(regions, [])
                    send(True, ru=True)
                    self.wait(lambda:button() and button()!=english and all(r and r[0][2]>10 for r in button()))
                    send(False)
                    self.wait(lambda:not self.layers())
                    send(True, ru=True)
                    self.wait(lambda:bool(self.layers()))
                finally:
                    process.stdin.close()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
                    process.stdout.close()
                self.assertEqual(process.returncode, 0, trace.read_text(errors='replace')[-1500:])
                self.wait(lambda:not self.layers())
