"""Provisional revisions, overlap and safe incremental prose boundaries."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gui'))
from tigo_gui.live_text import LiveTranscript, SpeechSentences


class TestLiveText(unittest.TestCase):
    def test_partial_revision_replaces_current_window_and_merges_overlap(self):
        text=LiveTranscript()
        self.assertEqual(text.update(0,'open the'),'open the')
        self.assertEqual(text.update(0,'open the window'),'open the window')
        self.assertEqual(text.update(1,'the window please'),'open the window please')
        self.assertEqual(text.update(1,'the window now'),'open the window now')

    def test_sentence_arrives_before_final_and_tail_is_not_lost(self):
        text=SpeechSentences()
        self.assertEqual(text.feed('First sen'),[])
        self.assertEqual(text.feed('tence. Next'),['First sentence.'])
        self.assertEqual(text.feed(' part',final=True),['Next part'])
        self.assertEqual(text.feed('',final=True),[])

    def test_fenced_code_and_partial_links_are_never_spoken(self):
        text=SpeechSentences()
        self.assertEqual(text.feed('Hello. \n```py\nsecret. \n'),['Hello.'])
        self.assertEqual(text.feed('more code\n```\nVisit [my site]('),[])
        self.assertEqual(text.feed('https://example.com). Ready. '),['Visit my site. Ready.'])
        self.assertEqual(text.feed('```\nunclosed code',final=True),[])
