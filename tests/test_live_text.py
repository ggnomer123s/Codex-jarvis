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
        self.assertEqual(text.feed('https://example.com). Ready. '),['Visit my site.', 'Ready.'])
        self.assertEqual(text.feed('```\nunclosed code',final=True),[])

    def test_greeting_stays_in_sentences_even_with_wrapped_word_deltas(self):
        text=SpeechSentences()
        phrase='\u041f\u0440\u0438\u0432\u0435\u0442,\n\u043d\u0430\u0441\u0442\u0430\u0432\u043d\u0438\u043a. \u042f \u043d\u0430 \u0441\u0432\u044f\u0437\u0438, \u0433\u043e\u0442\u043e\u0432 \u043a \u0434\u0435\u043b\u0443. \u041a\u0430\u043a \u0442\u044b?'
        spoken=[]
        for char in phrase: spoken.extend(text.feed(char))
        self.assertEqual(len(spoken),2)
        spoken.extend(text.feed('',final=True))
        self.assertEqual(spoken,[phrase.split('. ')[0].replace('\n',' ')+'.',phrase.split('. ')[1]+'.',phrase.split('. ')[2]])
        self.assertEqual(SpeechSentences().feed('First. Second. Last?',final=True),['First.','Second.','Last?'])
