"""Ownership diagnostics describe observed state without granting permission."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from tigo_gui.desktop_control import control_summary


class TestControlSummary(unittest.TestCase):
    def test_user_hold_and_idle_timer_are_separate_from_full_access(self):
        text = control_summary({'structuredContent': {'state':'user', 'wait_seconds':7.5,
                                'idle_timeout_seconds':10, 'policy':'strict'}})
        self.assertIn('7.5 s', text)
        self.assertIn('restarts the timer', text)
        self.assertIn('strict', text)
        self.assertIn('does not override', text)

    def test_json_snapshot_ready_and_unavailable_have_distinct_meanings(self):
        result = {'content':[{'type':'text','text':json.dumps({'state':'ready'})}]}
        self.assertIn('still pass backend checks', control_summary(result))
        self.assertIn('unavailable', control_summary({'structuredContent':{'state':'unavailable'}}))

    def test_errors_unknown_states_and_unbounded_text_do_not_claim_access(self):
        for result in ({'isError':True}, {'structuredContent':{'state':'invented'}},
                       {'content':[{'type':'text','text':'x'*16385}]}, None):
            with self.subTest(result_type=type(result).__name__):
                with self.assertRaises(ValueError): control_summary(result)

    def test_invalid_times_are_not_presented_as_real_waits(self):
        for wait in (True, float('nan'), float('inf'), -1, '0', 100000, 10**500):
            value = control_summary({'structuredContent':{'state':'user','wait_seconds':wait}})
            self.assertNotIn('Remaining idle wait', value)
