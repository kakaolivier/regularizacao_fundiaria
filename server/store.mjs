import { DatabaseSync } from 'node:sqlite';
import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
export function createStore(dir, seedPath = path.join(dir, 'seed.json')) {
  fs.mkdirSync(dir, { recursive: true });
  const db = new DatabaseSync(path.join(dir, 'territorio.sqlite'));
  db.exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS geometries(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS meta(id TEXT PRIMARY KEY, data TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS source_case ON sources(case_id);
    CREATE INDEX IF NOT EXISTS event_case ON events(case_id);
    CREATE INDEX IF NOT EXISTS task_case ON tasks(case_id);
    CREATE INDEX IF NOT EXISTS doc_case ON documents(case_id);
    CREATE INDEX IF NOT EXISTS geo_case ON geometries(case_id);`);
  const tables = new Set(['cases','sources','events','documents','tasks','geometries','meta']);
  const check = t => { if (!tables.has(t)) throw new Error('Unknown table'); };
  const put = (t, data, caseId) => { check(t); if (t==='cases'||t==='meta') db.prepare(`INSERT OR REPLACE INTO ${t}(id,data) VALUES(?,?)`).run(data.id,JSON.stringify(data)); else db.prepare(`INSERT OR REPLACE INTO ${t}(id,case_id,data) VALUES(?,?,?)`).run(data.id,caseId,JSON.stringify(data)); return data; };
  const get = (t,id) => {check(t); const row=db.prepare(`SELECT data FROM ${t} WHERE id=?`).get(id);return row?JSON.parse(row.data):null;};
  const all = (t,caseId) => {check(t);return (caseId ? db.prepare(`SELECT data FROM ${t} WHERE case_id=?`).all(caseId) : db.prepare(`SELECT data FROM ${t}`).all()).map(r=>JSON.parse(r.data));};
  const transaction = fn => { db.exec('BEGIN'); try { const r=fn();db.exec('COMMIT');return r; }catch(e){db.exec('ROLLBACK');throw e;} };
  const event = (caseId,data) => put('events',{id:randomUUID(),caseId,createdAt:new Date().toISOString(),date:new Date().toISOString(),author:'Equipe local',...data},caseId);
  if (!get('meta','import') && fs.existsSync(seedPath)) {
    const seed=JSON.parse(fs.readFileSync(seedPath,'utf8'));
    transaction(()=>{
      const mapping=new Map();
      for(const c of seed.cases){ put('cases',c); c.sourceIds.forEach(id=>mapping.set(id,c.id)); }
      for(const s of seed.sources){
        const caseId=mapping.get(s.id); put('sources',s,caseId);
        for(const e of s.events) event(caseId,{...e,id:`${s.id}-${e.title}`,kind:'milestone',author:'Planilha de origem',sourceId:s.id,source:`${s.sheet} · linha ${s.row}`,body:'Data estruturada informada na planilha. Não implica validação jurídica.'});
        if(s.notes) event(caseId,{id:`${s.id}-notes`,kind:'source',date:null,title:'Situação registrada na planilha',body:s.notes,author:'Planilha de origem',sourceId:s.id,source:`${s.sheet} · linha ${s.row}`});
      }
      put('meta',{id:'import',...seed, cases:undefined,sources:undefined});
    });
  }
  return {db,put,get,all,transaction,event};
}
