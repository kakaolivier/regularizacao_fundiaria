"""SQLite storage compatible with the original Node application's tables and JSON."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

TABLES = {'cases', 'sources', 'events', 'documents', 'tasks', 'geometries', 'meta'}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


class Store:
    def __init__(self, directory, initialize=False):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / 'territorio.sqlite', timeout=30, isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        try:
            if initialize:
                self.db.execute('PRAGMA journal_mode=WAL')
                for table in TABLES:
                    parent = '' if table in ('cases', 'meta') else ', case_id TEXT NOT NULL REFERENCES cases(id)'
                    self.db.execute(f'CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY, data TEXT NOT NULL{parent})')
                    if parent:
                        self.db.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_case ON {table}(case_id)')
                self.import_initial_seed()
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def get(self, table, identifier):
        assert table in TABLES
        row = self.db.execute(f'SELECT data FROM {table} WHERE id=?', (identifier,)).fetchone()
        return json.loads(row[0]) if row else None

    def all(self, table, case_id=None):
        assert table in TABLES
        if case_id is None:
            rows = self.db.execute(f'SELECT data FROM {table} ORDER BY rowid')
        else:
            rows = self.db.execute(f'SELECT data FROM {table} WHERE case_id=? ORDER BY rowid', (case_id,))
        return [json.loads(row[0]) for row in rows]

    def put(self, table, data, case_id=None):
        assert table in TABLES
        payload = json.dumps(data, ensure_ascii=False, allow_nan=False)
        if table in ('cases', 'meta'):
            self.db.execute(f'INSERT INTO {table}(id,data) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data', (data['id'], payload))
        else:
            self.db.execute(f'INSERT INTO {table}(id,case_id,data) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data,case_id=excluded.case_id', (data['id'], case_id, payload))
        return data

    def event(self, case_id, **data):
        item = {'id': str(uuid4()), 'caseId': case_id, 'createdAt': now(), 'date': now(), 'author': 'Equipe local', **data}
        return self.put('events', item, case_id)

    def import_initial_seed(self):
        seed_path = self.directory / 'seed.json'
        if self.get('meta', 'import') or not seed_path.is_file():
            return
        with seed_path.open(encoding='utf-8') as file:
            seed = json.load(file)
        with self.transaction():
            if self.get('meta', 'import'):
                return
            mapping = {}
            for item in seed['cases']:
                if self.get('cases', item['id']):
                    raise ValueError('A importação inicial contém um cadastro já existente. Faça a reconciliação antes de importar.')
                self.put('cases', item)
                for identifier in item['sourceIds']:
                    if identifier in mapping:
                        raise ValueError('Uma origem foi vinculada a mais de um cadastro.')
                    mapping[identifier] = item['id']
            for source in seed['sources']:
                case_id = mapping[source['id']]
                self.put('sources', source, case_id)
                for milestone in source.get('events', []):
                    self.event(case_id, **{**milestone, 'id': source['id'] + '-' + milestone['title'], 'kind': 'milestone', 'author': 'Planilha de origem', 'sourceId': source['id'], 'source': f"{source['sheet']} · linha {source['row']}", 'body': 'Data estruturada informada na planilha. Não implica validação jurídica.'})
                if source.get('notes'):
                    self.event(case_id, id=source['id'] + '-notes', kind='source', date=None, title='Situação registrada na planilha', body=source['notes'], author='Planilha de origem', sourceId=source['id'], source=f"{source['sheet']} · linha {source['row']}")
            self.put('meta', {**{k: v for k, v in seed.items() if k not in ('cases', 'sources')}, 'id': 'import'})
