"""Provisional transcription revisions and overlapping windows."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gui'))
from tigo_gui.live_text import LiveTranscript


class TestLiveText(unittest.TestCase):
    def test_partial_revision_replaces_current_window_and_merges_overlap(self):
        text=LiveTranscript()
        self.assertEqual(text.update(0,'open the'),'open the')
        self.assertEqual(text.update(0,'open the window'),'open the window')
        self.assertEqual(text.update(1,'the window please'),'open the window please')
        self.assertEqual(text.update(1,'the window now'),'open the window now')
