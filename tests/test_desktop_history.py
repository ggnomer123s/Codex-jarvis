"""Exercise durable history, literal search, account scoping and corruption."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from tigo_gui.history import History


class TestConversationHistory(unittest.TestCase):
    def test_search_pin_rename_and_reopen_preserve_messages(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'history.sqlite3'
            history = History(path, Path(folder)/'codex')
            messages = [{'role':'user','text':'Russian: Привет. Literal 100%_needle'}, {'role':'assistant','text':'**Answer**'}]
            history.save('first',folder,'model','read-only','thread-1','complete',messages)
            history.save('second',folder,'model','read-only','thread-2','complete',[{'role':'user','text':'Other topic'}])
            history.update('first',title='Закреплённый диалог',pinned=True)
            history.close()
            history = History(path, Path(folder)/'codex')
            try:
                self.assertEqual(history.list()[0]['id'],'first')
                self.assertEqual(history.list('ЗАКРЕПЛЁННЫЙ')[0]['id'],'first')
                self.assertEqual(history.list('100%_needle')[0]['id'],'first')
                self.assertEqual(history.load('first')['messages'],messages)
                history.save('first',folder,'model','read-only','thread-1','complete',messages)
                self.assertEqual(history.load('first')['title'],'Закреплённый диалог')
                history.delete('first')
                self.assertIsNone(history.load('first'))
            finally: history.close()

    def test_other_codex_home_cannot_list_open_or_change_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'history.sqlite3'
            first, second = History(path, Path(folder)/'one'), History(path, Path(folder)/'two')
            try:
                first.save('id',folder,'','full-access','thread','complete',[{'role':'user','text':'Private'}])
                self.assertEqual(second.list(),[])
                self.assertIsNone(second.load('id'))
                second.update('id',title='Changed',pinned=True)
                second.delete('id')
                self.assertEqual(first.load('id')['title'],'Private')
            finally: first.close(); second.close()

    def test_invalid_stored_message_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            history = History(Path(folder)/'history.sqlite3',folder)
            try:
                history.save('id',folder,'','read-only','thread','complete',[{'role':'user','text':'Hello'}])
                history.db.execute('UPDATE conversations SET messages=? WHERE id=?',(json.dumps([{'role':'unexpected','text':4}]),'id'))
                history.db.commit()
                with self.assertRaises(ValueError):history.load('id')
            finally:history.close()
