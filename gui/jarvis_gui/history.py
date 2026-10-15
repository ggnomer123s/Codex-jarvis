"""Private local conversation history, scoped to the current Codex home."""
import hashlib
import json
from pathlib import Path
import sqlite3
import time


class History:
    def __init__(self, path, home):
        self.path = Path(path)
        if self.path.is_symlink():
            raise ValueError('Refusing a symlinked conversation database.')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.scope = hashlib.sha256(str(Path(home).resolve()).encode()).hexdigest()
        self.db = sqlite3.connect(self.path, timeout=.2)
        self.path.chmod(0o600)
        self.db.row_factory = sqlite3.Row
        self.db.create_function('casefold', 1, lambda x: str(x).casefold(), deterministic=True)
        self.db.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY, scope TEXT NOT NULL, title TEXT NOT NULL,
            pinned INTEGER NOT NULL DEFAULT 0, updated REAL NOT NULL,
            folder TEXT NOT NULL, model TEXT NOT NULL, access TEXT NOT NULL,
            thread TEXT NOT NULL, status TEXT NOT NULL, messages TEXT NOT NULL,
            search TEXT NOT NULL)''')
        self.db.execute('CREATE INDEX IF NOT EXISTS conversation_scope ON conversations(scope, pinned, updated)')
        self.db.commit()

    def save(self, key, folder, model, access, thread, status, messages):
        if not messages or not key:
            return
        payload = json.dumps(messages, ensure_ascii=False)
        if len(payload.encode()) > 8_000_000:
            raise ValueError('Conversation history is larger than 8 MB; start a new conversation.')
        title = next((x['text'].strip().split('\n')[0][:100] for x in messages if x['role'] == 'user' and x['text'].strip()), 'Conversation')
        search = '\n'.join(x['text'] for x in messages).casefold()
        self.db.execute('''INSERT INTO conversations
            (id,scope,title,updated,folder,model,access,thread,status,messages,search)
            VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
            updated=excluded.updated,folder=excluded.folder,model=excluded.model,
            access=excluded.access,thread=excluded.thread,status=excluded.status,
            messages=excluded.messages,search=excluded.search WHERE conversations.scope=excluded.scope''',
            (key,self.scope,title,time.time(),folder,model,access,thread,status,payload,search))
        self.db.commit()

    def list(self, query=''):
        rows = self.db.execute('''SELECT id,title,pinned,updated,folder,model,access,status
            FROM conversations WHERE scope=? AND (instr(casefold(title),?)>0 OR instr(search,?)>0)
            ORDER BY pinned DESC,updated DESC LIMIT 100''', (self.scope,query.casefold(),query.casefold())).fetchall()
        return [dict(row, pinned=bool(row['pinned'])) for row in rows]

    def load(self, key):
        row = self.db.execute('SELECT * FROM conversations WHERE scope=? AND id=?', (self.scope,key)).fetchone()
        if not row:
            return None
        value = dict(row)
        messages = json.loads(value['messages'])
        if not isinstance(messages,list) or any(not isinstance(x,dict) or x.get('role') not in ('user','assistant','system','error') or not isinstance(x.get('text'),str) for x in messages):
            raise ValueError('Invalid conversation history.')
        value['messages'] = messages
        return value

    def update(self, key, *, title=None, pinned=None):
        if title is not None:
            self.db.execute('UPDATE conversations SET title=? WHERE scope=? AND id=?', (title.strip()[:120],self.scope,key))
        if pinned is not None:
            self.db.execute('UPDATE conversations SET pinned=? WHERE scope=? AND id=?', (bool(pinned),self.scope,key))
        self.db.commit()

    def delete(self, key):
        self.db.execute('DELETE FROM conversations WHERE scope=? AND id=?',(self.scope,key))
        self.db.commit()

    def references(self, path):
        # Include every account scope before removing an owned clipboard image.
        needle = json.dumps(path, ensure_ascii=False)[1:-1]
        return self.db.execute('SELECT 1 FROM conversations WHERE instr(messages,?)>0 LIMIT 1', (needle,)).fetchone() is not None

    def close(self):
        self.db.close()
