import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {once} from 'node:events';
import {createApp} from '../server/app.mjs';
const polygon={type:'Feature',properties:{},geometry:{type:'Polygon',coordinates:[[[-49.25,-16.82],[-49.249,-16.82],[-49.249,-16.819],[-49.25,-16.819],[-49.25,-16.82]]]}};
const record={title:'Área de teste',city:'Goiânia',owner:'Proprietário de teste',number:'1234567-89.2025.8.09.0001',method:'Judicial'};
async function setup(t, seed){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'territorio-test-'));
 if(seed)fs.writeFileSync(path.join(dir,'seed.json'),JSON.stringify(seed));
 const {app,store}=createApp({dataDir:dir});const server=app.listen(0,'127.0.0.1');await once(server,'listening');
 const base=`http://127.0.0.1:${server.address().port}/api`;
 const req=async(url,method='GET',body,headers={})=>{const r=await fetch(base+url,{method,headers:{...(body instanceof FormData?{}:{'Content-Type':'application/json'}),...headers},...(body===undefined?{}:{body:body instanceof FormData?body:JSON.stringify(body)})});return {status:r.status,data:await r.json()};};
 t.after(async()=>{await new Promise(r=>server.close(r));store.db.close();fs.rmSync(dir,{recursive:true,force:true});});
 return {dir,req,store,base};
}
test('case lifecycle, canonical duplicate detection, provenance, tasks and persistence',async t=>{
 const {req,dir,store}=await setup(t);
 let r=await req('/cases','POST',record);assert.equal(r.status,201);const id=r.data.id;
 assert.equal((await req('/cases','POST',{...record,number:'12345678920258090001'})).status,409);
 assert.equal((await req('/cases','POST',{title:''})).status,400);
 assert.equal((await req('/cases/absent/events','POST',{title:'x'})).status,404);
 await req(`/cases/${id}/events`,'POST',{title:'Parecer recebido',body:'Encaminhar avaliação técnica.',author:'Equipe técnica',kind:'decision'});
 await req(`/cases/${id}`,'PATCH',{stage:'Análise jurídica',category:'Em andamento',author:'Equipe jurídica'});
 const task=(await req(`/cases/${id}/tasks`,'POST',{title:'Conferir matrícula',assignee:'Maria',due:'2026-12-31'})).data;
 assert.equal((await req(`/cases/${id}/tasks`,'POST',{title:'x',assignee:'y',due:'2026-99-99'})).status,400);
 await req(`/cases/${id}/tasks/${task.id}`,'PATCH',{done:true});
 const detail=(await req(`/cases/${id}`)).data;assert.equal(detail.stage,'Análise jurídica');assert.equal(detail.tasks[0].done,true);assert.ok(detail.events.some(e=>e.title==='Parecer recebido'));
 const {app:app2,store:store2}=createApp({dataDir:dir});assert.equal(store2.get('cases',id).stage,'Análise jurídica');assert.equal(store2.all('tasks',id)[0].done,true);store2.db.close();
 assert.equal(store.all('cases').length,1);
});
test('geometries reject malformed and crossing polygons, preserve versions and scope',async t=>{
 const {req}=await setup(t);const id=(await req('/cases','POST',record)).data.id;const other=(await req('/cases','POST',{...record,number:''})).data.id;
 const body={name:'Faixa 01',kind:'Área de interesse',feature:polygon};const saved=await req(`/cases/${id}/geometries`,'POST',body);assert.equal(saved.status,201);assert.ok(saved.data.areaM2>11000&&saved.data.areaM2<12500);
 assert.equal((await req(`/cases/${other}/geometries`,'POST',{...body,id:saved.data.id,version:1})).status,404);
 const modified=await req(`/cases/${id}/geometries`,'POST',{...body,id:saved.data.id,version:1});assert.equal(modified.data.version,2);assert.equal(modified.data.history.length,1);
 assert.equal((await req(`/cases/${id}/geometries`,'POST',{...body,id:saved.data.id,version:1})).status,409);
 assert.equal((await req(`/cases/${id}/geometries`,'POST',{...body,sourceId:'wrong-case'})).status,400);
 for(const coords of [[[[0,0],[1,1],[1,0],[0,1],[0,0]]],[[[300,0],[1,0],[1,1],[300,0]]],[[[0,0],[1,0],[1,1]]],[[[0,0],[0,0],[0,0],[0,0]]]]){
  assert.equal((await req(`/cases/${id}/geometries`,'POST',{...body,feature:{type:'Feature',geometry:{type:'Polygon',coordinates:coords}}})).status,400);
 }
});
test('document bytes survive download; versions cannot cross cases; invalid files rejected',async t=>{
 const {req,base}=await setup(t);const id=(await req('/cases','POST',record)).data.id;const other=(await req('/cases','POST',{...record,number:''})).data.id;
 const content='%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF';
 const form=(filename='parecer.pdf',bytes=content,extra={})=>{const f=new FormData();f.append('file',new Blob([bytes]),filename);f.append('category','Parecer jurídico');for(const [k,v]of Object.entries(extra))f.append(k,v);return f;};
 const first=await req(`/cases/${id}/documents`,'POST',form());assert.equal(first.status,201);assert.equal(first.data.version,1);assert.equal(first.data.storage,undefined);
 const file=await fetch(`${base}/cases/${id}/documents/${first.data.id}/download`);assert.equal(await file.text(),content);assert.match(file.headers.get('content-disposition'),/attachment/);
 const second=await req(`/cases/${id}/documents`,'POST',form('parecer.pdf',content,{replaces:first.data.id}));assert.equal(second.data.version,2);
 assert.equal((await req(`/cases/${id}/documents`,'POST',form('parecer.pdf',content,{replaces:first.data.id}))).status,409);
 assert.equal((await req(`/cases/${other}/documents`,'POST',form('parecer.pdf',content,{replaces:second.data.id}))).status,400);
 assert.equal((await fetch(`${base}/cases/${other}/documents/${first.data.id}/download`)).status,404);
 assert.equal((await req(`/cases/${id}/documents`,'POST',form('script.html','<script>x</script>'))).status,400);
 assert.equal((await req(`/cases/${id}/documents`,'POST',form('fake.pdf','not PDF'))).status,400);
 assert.equal((await req('/cases','POST',record,{Origin:'https://unrelated.example'})).status,403);
});
test('seed import is atomic and idempotent; source dates and unstructured notes stay distinct',async t=>{
 const fixture={cases:[{...record,id:'seed-case',sourceIds:['s1','s2','s3']}],sources:[{id:'s1',sheet:'Aba',row:6,owner:'Parte secundária',registry:'Matrícula secundária',notes:'Relato sem data',events:[{date:'2025-01-03',title:'Petição inicial'}],fields:[{label:'Valor original',value:'N/A'}]},{id:'s2',sheet:'Laudos',row:12,kind:'laudo',notes:'',events:[]},{id:'s3',sheet:'Pendentes',row:9,kind:'pericia',notes:'',events:[]}],summary:{records:3},workbooks:[],supplementary:[]};
 const {req,dir,store}=await setup(t,fixture);assert.equal(store.all('cases').length,1);
 const d=(await req('/cases/seed-case')).data;assert.equal(d.events.length,2);assert.equal(d.events.find(e=>e.kind==='source').date,null);assert.equal(d.events.find(e=>e.kind==='milestone').date,'2025-01-03');assert.equal(d.sources[0].fields[0].value,'N/A');assert.equal(d.expertStage,'Conferir divergência entre abas');const boot=(await req('/bootstrap')).data;assert.match(boot.cases[0].searchText,/Parte secundária/);assert.equal(boot.cases[0].expertStage,'Conferir divergência entre abas');
 const {store:again}=createApp({dataDir:dir});assert.equal(again.all('cases').length,1);assert.equal(again.all('events').length,2);again.db.close();
});
