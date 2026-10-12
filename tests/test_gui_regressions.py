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


if __name__ == "__main__":
    unittest.main()
