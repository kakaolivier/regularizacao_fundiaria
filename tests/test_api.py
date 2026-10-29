import io
import json
import math
import sqlite3
import tempfile
import unittest
from pathlib import Path
from territorio import create_app
from territorio.store import Store

CASE = {'title': 'Imóvel de teste', 'city': 'Goiânia', 'owner': 'Pessoa fictícia', 'number': '1234567-89.2025.8.09.0001', 'method': 'Judicial'}
POLYGON = {'type':'Feature','properties':{},'geometry':{'type':'Polygon','coordinates':[[[-49.25,-16.82],[-49.249,-16.82],[-49.249,-16.819],[-49.25,-16.819],[-49.25,-16.82]]]}}


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.app = create_app(self.path, testing=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def create(self, **changes):
        response = self.client.post('/api/cases', json={**CASE, **changes})
        self.assertEqual(response.status_code, 201)
        return response.json['id']

    def test_crud_validation_duplicate_normalization_and_related_rows_survive_stage_update(self):
        identifier = self.create()
        root = f'/api/cases/{identifier}'
        self.assertEqual(self.client.post('/api/cases', json={**CASE,'number':'12345678920258090001'}).status_code,409)
        self.assertEqual(self.client.post('/api/cases',json={}).status_code,400)
        self.assertEqual(self.client.post('/api/cases/missing/events',json={}).status_code,404)
        self.client.post(root+'/events',json={'title':'Parecer','body':'Análise registrada','kind':'decision','author':'Equipe de teste'})
        task=self.client.post(root+'/tasks',json={'title':'Conferir matrícula','assignee':'Maria','due':'2026-12-31'})
        self.assertEqual(task.status_code,201)
        self.assertEqual(self.client.post(root+'/tasks',json={'title':'x','assignee':'y','due':'2026-99-99'}).status_code,400)
        self.assertEqual(self.client.patch(root+'/tasks/'+task.json['id'],json={'done':'false'}).status_code,400)
        self.assertEqual(self.client.patch(root+'/tasks/'+task.json['id'],json={'done':True}).status_code,200)
        # Legacy Node used REPLACE; Python must update without deleting referenced parents.
        self.assertEqual(self.client.patch(root,json={'stage':'Análise jurídica','category':'Em andamento','author':'Equipe'}).status_code,200)
        detail=self.client.get(root).json
        self.assertEqual(detail['stage'],'Análise jurídica')
        self.assertTrue(detail['tasks'][0]['done'])
        self.assertTrue(any(e['title']=='Parecer' for e in detail['events']))
        reopened=create_app(self.path,testing=True).test_client().get(root).json
        self.assertEqual(reopened['tasks'],detail['tasks'])
        self.assertEqual(reopened['events'],detail['events'])

    def test_geometry_validation_versions_holes_multipolygon_and_ownership(self):
        identifier=self.create(); other=self.create(number='')
        root=f'/api/cases/{identifier}/geometries'
        body={'name':'Faixa','kind':'Área de interesse','feature':POLYGON}
        response=self.client.post(root,json=body)
        self.assertEqual(response.status_code,201)
        item=response.json
        self.assertGreater(item['areaM2'],11000);self.assertLess(item['areaM2'],12500)
        self.assertEqual(self.client.post(f'/api/cases/{other}/geometries',json={**body,'id':item['id'],'version':1}).status_code,404)
        revised=self.client.post(root,json={**body,'id':item['id'],'version':1}).json
        self.assertEqual(revised['version'],2);self.assertEqual(revised['history'][0]['feature'],POLYGON)
        self.assertEqual(self.client.post(root,json={**body,'id':item['id'],'version':1}).status_code,409)
        self.assertEqual(self.client.post(root,json={**body,'sourceId':'invalid'}).status_code,400)
        for coords in [[[[0,0],[1,1],[1,0],[0,1],[0,0]]],[[[300,0],[1,0],[1,1],[300,0]]],[[[0,0],[1,0],[1,1]]],[[[0,0],[0,0],[0,0],[0,0]]],[[[False,0],[1,0],[1,1],[False,0]]],[[[0,0],[1,float('nan')],[1,1],[0,0]]]]:
            with self.subTest(coords=coords):
                invalid={**POLYGON,'geometry':{'type':'Polygon','coordinates':coords}}
                self.assertEqual(self.client.post(root,json={**body,'feature':invalid}).status_code,400)
        outer=[[0,0],[1,0],[1,1],[0,1],[0,0]]
        hole=[[.2,.2],[.8,.2],[.8,.8],[.2,.8],[.2,.2]]
        with_hole=self.client.post(root,json={**body,'feature':{'type':'Feature','geometry':{'type':'Polygon','coordinates':[outer,hole]}}})
        self.assertEqual(with_hole.status_code,201)
        overlap=self.client.post(root,json={**body,'feature':{'type':'Feature','geometry':{'type':'MultiPolygon','coordinates':[[outer],[outer]]}}})
        self.assertEqual(overlap.status_code,400)
        disconnected=self.client.post(root,json={**body,'feature':{'type':'Feature','geometry':{'type':'MultiPolygon','coordinates':[[outer],[[[2,0],[3,0],[3,1],[2,1],[2,0]]]]}}})
        self.assertEqual(disconnected.status_code,201)

    def test_documents_exact_bytes_accents_versions_and_rejections(self):
        identifier=self.create();other=self.create(number='');root=f'/api/cases/{identifier}/documents'
        contents=b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF'
        def upload(name='matrícula.pdf',content=contents,**extra):
            return {'category':'Matrícula','file':(io.BytesIO(content),name),**extra}
        first=self.client.post(root,data=upload())
        self.assertEqual(first.status_code,201);self.assertEqual(first.json['name'],'matrícula.pdf');self.assertNotIn('storage',first.json)
        download=self.client.get(root+'/'+first.json['id']+'/download')
        self.assertEqual(download.data,contents);self.assertIn('attachment',download.headers['Content-Disposition']);download.close()
        second=self.client.post(root,data=upload(replaces=first.json['id']))
        self.assertEqual(second.json['version'],2)
        self.assertEqual(self.client.post(root,data=upload(replaces=first.json['id'])).status_code,409)
        self.assertEqual(self.client.post(f'/api/cases/{other}/documents',data=upload(replaces=second.json['id'])).status_code,400)
        self.assertEqual(self.client.get(f'/api/cases/{other}/documents/{first.json["id"]}/download').status_code,404)
        self.assertEqual(self.client.post(root,data=upload('script.html',b'<script>bad</script>')).status_code,400)
        self.assertEqual(self.client.post(root,data=upload('fake.pdf',b'not-pdf')).status_code,400)
        self.assertEqual(len(list((self.path/'uploads').iterdir())),2)

    def test_html_routes_search_csv_xss_origin_and_csrf(self):
        identifier=self.create(title='<script>alert(1)</script>',owner='=HYPERLINK("x")')
        for route in ['/','/processos','/pericias','/mapa','/tarefas','/fontes','/planejamento']+[f'/processos/{identifier}?tab='+tab for tab in ['resumo','historico','documentos','mapa','origem']]:
            with self.subTest(route=route):self.assertEqual(self.client.get(route).status_code,200)
        page=self.client.get(f'/processos/{identifier}').get_data(as_text=True)
        self.assertNotIn('<script>alert(1)</script>',page);self.assertIn('&lt;script&gt;',page)
        self.assertIn('Nenhum processo encontrado',self.client.get('/processos?q=ausente').get_data(as_text=True))
        exported=self.client.get('/processos/exportar.csv').get_data(as_text=True)
        self.assertIn("'=HYPERLINK",exported)
        self.assertEqual(self.client.post('/api/cases',json=CASE,headers={'Origin':'https://unrelated.example'}).status_code,403)
        self.assertEqual(self.client.post('/processos/novo',data=CASE).status_code,403)
        with self.client.session_transaction() as session: token=session['csrf']
        self.assertEqual(self.client.post('/processos/novo',data={**CASE,'number':'','_csrf':token}).status_code,303)
        self.assertEqual(self.client.get('/api/cases/missing').status_code,404)

    def test_legacy_database_schema_documents_and_idempotent_seed(self):
        # Recreate the exact column order used by server/store.mjs in the previous release.
        legacy=self.path/'legacy';legacy.mkdir()
        connection=sqlite3.connect(legacy/'territorio.sqlite')
        connection.executescript('CREATE TABLE cases(id TEXT PRIMARY KEY,data TEXT NOT NULL);CREATE TABLE tasks(id TEXT PRIMARY KEY,case_id TEXT NOT NULL REFERENCES cases(id),data TEXT NOT NULL);CREATE TABLE documents(id TEXT PRIMARY KEY,case_id TEXT NOT NULL REFERENCES cases(id),data TEXT NOT NULL);CREATE TABLE meta(id TEXT PRIMARY KEY,data TEXT NOT NULL);')
        item={**CASE,'id':'legacy','stage':'Registrado','category':'Registro','sourceIds':[],'sourceCount':0,'hasExpert':False,'hasRegistry':True,'hasAward':False,'expertStage':'','section':'','needsReconciliation':False}
        connection.execute('INSERT INTO cases VALUES(?,?)',('legacy',json.dumps(item)))
        task={'id':'t','caseId':'legacy','title':'Ação antiga','assignee':'Equipe','due':'2026-12-31','done':False}
        connection.execute('INSERT INTO tasks VALUES(?,?,?)',('t','legacy',json.dumps(task)))
        document={'id':'d','caseId':'legacy','name':'antigo.txt','storage':'original.txt','size':6,'category':'Outros','version':1,'createdAt':'2026-10-15T12:00:00Z'}
        connection.execute('INSERT INTO documents VALUES(?,?,?)',('d','legacy',json.dumps(document)))
        connection.execute('INSERT INTO meta VALUES(?,?)',('import',json.dumps({'id':'import','summary':{'records':0},'workbooks':[]})))
        connection.commit();connection.close();(legacy/'uploads').mkdir();(legacy/'uploads/original.txt').write_bytes(b'legado')
        (legacy/'seed.json').write_text('{}',encoding='utf-8') # Must not re-import when metadata exists.
        client=create_app(legacy,testing=True).test_client()
        response=client.get('/api/cases/legacy');self.assertEqual(response.json['tasks'][0],task)
        self.assertEqual(client.patch('/api/cases/legacy',json={'stage':'Revisão','category':'Em andamento','author':'Equipe'}).status_code,200)
        file=client.get('/api/cases/legacy/documents/d/download');self.assertEqual(file.data,b'legado');file.close()
        self.assertEqual(client.get('/api/cases/legacy').json['documents'][0]['version'],1)
        self.assertEqual(create_app(legacy,testing=True).test_client().get('/api/health').json['cases'],1)

    def test_initial_seed_all_sources_conflict_unstructured_notes_and_rollback(self):
        path=self.path/'seeded';path.mkdir()
        item={**CASE,'id':'seed-case','sourceIds':['s1','s2'],'stage':'Pericial','expertStage':'Laudo pendente'}
        sources=[{'id':'s1','sheet':'Laudos','row':12,'kind':'laudo','owner':'Parte secundária','notes':'Relato sem data','events':[{'date':'2025-01-03','title':'Petição inicial'}]}, {'id':'s2','sheet':'Pendentes','row':9,'kind':'pericia','notes':'','events':[]}]
        (path/'seed.json').write_text(json.dumps({'cases':[item],'sources':sources,'summary':{'records':2},'workbooks':[]}),encoding='utf-8')
        client=create_app(path,testing=True).test_client()
        detail=client.get('/api/cases/seed-case').json
        self.assertEqual(len(detail['events']),2);self.assertEqual(detail['expertStage'],'Conferir divergência entre abas')
        self.assertIsNone(next(e for e in detail['events'] if e['kind']=='source')['date'])
        self.assertIn('Parte secundária',client.get('/api/bootstrap').json['cases'][0]['searchText'])
        repeated=create_app(path,testing=True).test_client().get('/api/cases/seed-case').json
        self.assertEqual(repeated['events'],detail['events'])
        broken=self.path/'broken';broken.mkdir()
        (broken/'seed.json').write_text(json.dumps({'cases':[item],'sources':sources+[{'id':'unmapped'}]}),encoding='utf-8')
        with self.assertRaises(KeyError):create_app(broken,testing=True)
        db=sqlite3.connect(broken/'territorio.sqlite');self.assertEqual(db.execute('select count(*) from cases').fetchone()[0],0);db.close()


if __name__=='__main__':unittest.main()
