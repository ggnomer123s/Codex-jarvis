"""Speech-end frame alignment, pauses and silence-only rejection."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gui'))
from tigo_gui.voice_endpoint import SpeechEndpoint

SPEECH=b'\x01\0'*320
QUIET=b'\0'*640


class TestSpeechEndpoint(unittest.TestCase):
    def detector(self,pause=1600):
        def classify(frame,rate):
            self.assertEqual((len(frame),rate),(640,16000))
            return frame[0]==1
        return SpeechEndpoint(pause,classifier=classify)

    def test_short_pause_keeps_recording_and_sustained_pause_finishes(self):
        detector=self.detector()
        self.assertFalse(detector.feed(SPEECH*20+QUIET*40))
        self.assertTrue(detector.started)
        self.assertFalse(detector.feed(SPEECH*15+QUIET*79))
        self.assertEqual(detector.feed(QUIET),'silence')
        self.assertEqual(detector.feed(SPEECH),'silence')

    def test_silence_and_isolated_noise_never_form_a_command(self):
        for data in (QUIET*400,(SPEECH*3+QUIET*17)*20):
            detector=self.detector()
            self.assertEqual(detector.feed(data),'no_speech')
            self.assertFalse(detector.started)

    def test_arbitrary_capture_chunks_keep_exact_vad_frame_size(self):
        detector=self.detector(800)
        raw=SPEECH*20+QUIET*40
        result=''
        for offset in range(0,len(raw),173):
            result=detector.feed(raw[offset:offset+173])
        self.assertEqual(result,'silence')

    def test_unsupported_pause_is_rejected(self):
        for pause in (799,4001,True,'1600'):
            with self.assertRaises(ValueError):self.detector(pause)
