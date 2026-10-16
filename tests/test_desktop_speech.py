"""Speech preparation stays bounded, local and separate from model input."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gui'))
from tigo_gui.speech_text import spoken_text,MAX_SPEECH_CHARS


class TestSpeechText(unittest.TestCase):
    def test_product_name_is_pronounced_in_russian_without_touching_english(self):
        self.assertEqual(spoken_text('Tigo готов к работе.'), 'Тиго готов к работе.')
        self.assertEqual(spoken_text('Tigo is ready.'), 'Tigo is ready.')

    def test_markdown_is_readable_and_code_links_and_controls_are_removed(self):
        value=spoken_text('# Ready\n\n**Mentor**, see [the result](https://example.com).\n```sh\nsecret command\n```\n- Done.\nhttps://example.com/private\x00')
        self.assertIn('Mentor',value)
        self.assertIn('the result',value)
        self.assertNotIn('secret command',value)
        self.assertNotIn('https://',value)
        self.assertNotIn('**',value)
        self.assertNotIn('\x00',value)

    def test_unclosed_code_is_not_spoken_and_long_russian_has_a_notice(self):
        self.assertEqual(spoken_text('```python\nonly_code()'),'')
        value=spoken_text('Наставник, ответ готов. '*1000)
        self.assertLessEqual(len(value),MAX_SPEECH_CHARS)
        self.assertTrue(value.endswith('Продолжение — в чате.'))
