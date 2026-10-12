"""Regression tests for managed rules and X11 keyboard targeting.

No GUI, network, Codex, or PyPI dependencies required.
"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestManagedAgents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module("jarvis_sync_agents_test", ROOT / "scripts" / "sync_agents.py")

    def test_upgrades_old_block_and_preserves_unmanaged_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / "AGENTS.md"
            agents.write_text("My custom preference\n\n<!-- JARVIS-CODEX RULES START -->\nold text\n<!-- JARVIS-CODEX RULES END -->\n\nOther custom instructions\n")
            self.assertTrue(self.module.sync(agents, ROOT / "config" / "jarvis-agents.md"))
            text = agents.read_text()
            self.assertIn("My custom preference", text)
            self.assertIn("Other custom instructions", text)
            self.assertIn("Keyboard shortcuts are supported", text)
            self.assertNotIn("old text", text)
            self.assertFalse(self.module.sync(agents, ROOT / "config" / "jarvis-agents.md"))
            self.assertEqual(len(list(root.glob("AGENTS.md.backup.*"))), 1)

    def test_broken_markers_refuse_to_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / "AGENTS.md"
            original = "<!-- JARVIS-CODEX RULES START -->\nUnterminated"
            agents.write_text(original)
            with self.assertRaises(ValueError):
                self.module.sync(agents, ROOT / "config" / "jarvis-agents.md")
            self.assertEqual(agents.read_text(), original)


class TestX11Shortcuts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use an MCP stub: tests verify our wrapper, not the upstream framework.
        fast = types.ModuleType("mcp.server.fastmcp")

        class FastMCP:
            def __init__(self, name):
                self.name = name

            def tool(self):
                return lambda fn: fn

        class Image:
            def __init__(self, data, format):
                self.data, self.format = data, format

        fast.FastMCP = FastMCP
        fast.Image = Image
        with mock.patch.dict(sys.modules, {
            "mcp": types.ModuleType("mcp"),
            "mcp.server": types.ModuleType("mcp.server"),
            "mcp.server.fastmcp": fast,
        }):
            cls.backend = load_module("jarvis_x11_test", ROOT / "scripts" / "x11_mcp.py")

    def test_shortcut_targets_verified_window(self):
        mod = self.backend
        calls = []
        def fake_run(*args, **kwargs):
            calls.append(args)
            if args[:2] == ("xdotool", "getactivewindow"):
                return str(int("0x1234", 16)) + "\n"
            return ""
        with mock.patch.object(mod, "_require_input"), mock.patch.object(mod, "_run", side_effect=fake_run):
            mod.key("ctrl+shift+t", window_id="0x1234")
        self.assertIn(("wmctrl", "-ia", "0x1234"), calls)
        self.assertIn(("xdotool", "key", "--clearmodifiers", "ctrl+shift+t"), calls)
        self.assertLess(calls.index(("wmctrl", "-ia", "0x1234")),
                        calls.index(("xdotool", "key", "--clearmodifiers", "ctrl+shift+t")))

    def test_refuse_typing_if_focus_did_not_change(self):
        mod = self.backend
        calls = []
        def fake_run(*args, **kwargs):
            calls.append(args)
            if args[:2] == ("xdotool", "getactivewindow"):
                return "123\n"
            return ""
        with mock.patch.object(mod, "_require_input"), mock.patch.object(mod, "_run", side_effect=fake_run), mock.patch.object(mod.time, "sleep"):
            with self.assertRaises(RuntimeError):
                mod.key("ctrl+s", window_id="0x1234")
        self.assertNotIn(("xdotool", "key", "--clearmodifiers", "ctrl+s"), calls)

    def test_invalid_window_id(self):
        with self.assertRaises(ValueError):
            self.backend._validate_window_id("0x1;rm -rf /")

    def test_negative_multimonitor_coordinate(self):
        mod = self.backend
        with mock.patch.object(mod, "_require_input"), mock.patch.object(mod, "_run") as cmd:
            mod.click(-400, 200)
        cmd.assert_called_once_with("xdotool", "mousemove", "-400", "200", "click", "1")

    def test_window_scoped_capture(self):
        mod = self.backend
        with mock.patch.object(mod, "_run", return_value=b"PNG") as call:
            image = mod.screenshot("0x1234")
        self.assertEqual(image.data, b"PNG")
        call.assert_called_once_with("maim", "-u", "-i", "0x1234", "-f", "png", text=False)


    def test_x11_region_screenshot_with_negative_origin(self):
        mod = self.backend
        with mock.patch.object(mod, "_run", return_value=b"PNG") as call:
            image = mod.screenshot_region(-120, 40, 300, 200)
        self.assertEqual(image.data, b"PNG")
        call.assert_called_once_with(
            "maim", "-u", "-g", "300x200-120+40", "-f", "png", text=False
        )

    def test_x11_region_screenshot_rejects_unbounded_capture(self):
        with self.assertRaises(ValueError):
            self.backend.screenshot_region(10, 10, 0, 300)
        with self.assertRaises(ValueError):
            self.backend.screenshot_region(10, 10, 5000, 300)
        with self.assertRaises(ValueError):
            self.backend.screenshot_region(32767, 0, 100, 100)

    def test_user_selected_area_uses_maim_selection_not_mouse_injection(self):
        mod = self.backend
        with mock.patch.dict(mod.os.environ, {"DISPLAY": ":1"}):
            with mock.patch.object(mod, "_run", return_value=b"PNG") as call:
                image = mod.user_select_screenshot()
        self.assertEqual(image.data, b"PNG")
        call.assert_called_once_with(
            "maim", "-u", "-s", "-f", "png", text=False, timeout=45
        )

    def test_drag_mouse_release_after_success(self):
        mod = self.backend
        with mock.patch.object(mod, "_require_input"), mock.patch.object(
            mod, "_run"
        ) as call, mock.patch.object(mod.time, "sleep"):
            mod.drag(-50, 40, 200, 120, steps=4)
        args = [c.args for c in call.call_args_list]
        self.assertEqual(args[0], ("xdotool", "mousemove", "-50", "40"))
        self.assertEqual(args[1], ("xdotool", "mousedown", "1"))
        self.assertEqual(args[-2], ("xdotool", "mousemove", "200", "120"))
        self.assertEqual(args[-1], ("xdotool", "mouseup", "1"))

    def test_drag_releases_mouse_if_intermediate_motion_fails(self):
        mod = self.backend
        events = []

        def fail_middle(*args, **kwargs):
            events.append(args)
            if len(events) == 3:
                raise RuntimeError("motion failed")

        with mock.patch.object(mod, "_require_input"), mock.patch.object(
            mod, "_run", side_effect=fail_middle
        ), mock.patch.object(mod.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "motion failed"):
                mod.drag(10, 10, 100, 100, steps=3)
        self.assertEqual(events[-1], ("xdotool", "mouseup", "1"))

    def test_drag_requires_input_permission_and_distinct_endpoints(self):
        mod = self.backend
        with mock.patch.object(mod, "_require_input", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                mod.drag(10, 10, 100, 100)
        with mock.patch.object(mod, "_require_input"):
            with self.assertRaises(ValueError):
                mod.drag(10, 10, 10, 10)
            with self.assertRaises(ValueError):
                mod.drag(10, 10, 20, 20, steps=41)



if __name__ == "__main__":
    unittest.main()
