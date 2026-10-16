import express from 'express';
import multer from 'multer';
import fs from 'node:fs';
import path from 'node:path';
import { randomUUID, createHash } from 'node:crypto';
import { z } from 'zod';
import area from '@turf/area';
import booleanValid from '@turf/boolean-valid';
import kinks from '@turf/kinks';
import { createStore } from './store.mjs';

const text = z.string().trim().min(1).max(2000);
const short = z.string().trim().min(1).max(200);
const displayCase = (c, sources) => ({...c, expertStage:sources.some(s=>s.kind==='laudo')&&sources.some(s=>s.kind==='pericia')?'Conferir divergência entre abas':c.expertStage});
const cnj = s => /^\d{20}$/.test(s.replace(/[.\-\s]/g,'')) ? s.replace(/[.\-\s]/g,'') : null;
export function validateGeometry(feature) {
  if(!feature || feature.type!=='Feature' || !['Polygon','MultiPolygon'].includes(feature.geometry?.type)) throw new Error('Importe um polígono ou multipolígono GeoJSON em WGS84 (EPSG:4326).');
  if(JSON.stringify(feature).length>500000) throw new Error('Geometria muito grande. Simplifique para até 500 KB.');
  const polys=feature.geometry.type==='Polygon'?[feature.geometry.coordinates]:feature.geometry.coordinates;
  if(!Array.isArray(polys)||!polys.length) throw new Error('Polígono vazio.');
  for(const polygon of polys){
    if(!Array.isArray(polygon)||!polygon.length) throw new Error('Polígono vazio.');
    for(const ring of polygon){
      if(!Array.isArray(ring)||ring.length<4) throw new Error('Cada anel precisa de três vértices e fechamento.');
      for(const p of ring) if(!Array.isArray(p)||p.length!==2||!p.every(Number.isFinite)||Math.abs(p[0])>180||Math.abs(p[1])>90) throw new Error('Coordenadas inválidas. Use longitude e latitude WGS84.');
      if(ring[0][0]!==ring.at(-1)[0]||ring[0][1]!==ring.at(-1)[1]) throw new Error('O polígono deve estar fechado.');
    }
  }
  const safe={type:'Feature',properties:{},geometry:feature.geometry};
  if(!booleanValid(safe)||kinks(safe).features.length) throw new Error('Polígono inválido ou com cruzamento de linhas.');
  const m2=area(safe);if(!Number.isFinite(m2)||m2<=0) throw new Error('O polígono precisa ter área positiva.');
  return {feature:safe,areaM2:m2};
}
export function createApp({dataDir,seedPath}) {
  const app=express(); const store=createStore(dataDir,seedPath); const {get,put,all,event,transaction}=store;
  const uploadDir=path.join(dataDir,'uploads'); fs.mkdirSync(uploadDir,{recursive:true});
  app.disable('x-powered-by');
  app.use((req,res,next)=>{res.set('X-Content-Type-Options','nosniff');res.set('Referrer-Policy','same-origin'); if(req.path.startsWith('/api'))res.set('Cache-Control','no-store'); const origin=req.get('origin');if(!['GET','HEAD','OPTIONS'].includes(req.method)&&origin){try{if(new URL(origin).host!==req.get('host'))return res.status(403).json({error:'Origem não autorizada.'});}catch{return res.status(403).json({error:'Origem inválida.'});}}next();});
  app.use(express.json({limit:'1mb'}));
  app.get('/api/health',(_req,res)=>res.json({ok:true,cases:all('cases').length,mode:'local'}));
  app.get('/api/bootstrap',(_req,res)=>{
    const cases=all('cases'); const geometries=all('geometries'); const tasks=all('tasks'); const sourceIndex=new Map(all('sources').map(s=>[s.id,s]));
    res.json({cases:cases.map(c=>({...displayCase(c,(c.sourceIds||[]).map(id=>sourceIndex.get(id)).filter(Boolean)),searchText:(c.sourceIds||[]).map(id=>{const s=sourceIndex.get(id);return s?[s.title,s.owner,s.process,s.section,s.gisId,s.registry].join(' '):'';}).join(' '),geometryCount:geometries.filter(g=>g.caseId===c.id).length})),tasks,geometries,meta:get('meta','import')||{workbooks:[],summary:{},supplementary:[]}});
  });
  app.post('/api/cases',(req,res)=>{
    const c=z.object({title:short,city:short,owner:short,number:z.string().trim().max(120).default(''),section:z.string().trim().max(200).default(''),method:z.enum(['Judicial','Extrajudicial','A definir'])}).parse(req.body);
    const normalized=cnj(c.number); if(normalized&&all('cases').some(x=>cnj(x.number)===normalized))return res.status(409).json({error:'Já existe um cadastro com esse número de processo.'});
    const item={...c,id:randomUUID(),stage:'Cadastro inicial',category:'Preparação',expertStage:'',hasExpert:false,hasAward:false,hasRegistry:false,sourceCount:0,sourceIds:[],origins:[],needsReconciliation:!normalized,createdAt:new Date().toISOString()};
    transaction(()=>{put('cases',item);event(item.id,{kind:'activity',title:'Processo cadastrado',body:'Cadastro criado neste ambiente.'});});res.status(201).json(item);
  });
  app.use('/api/cases/:id',(req,res,next)=>{if(!get('cases',req.params.id))return res.status(404).json({error:'Processo não encontrado.'});next();});
  app.get('/api/cases/:id',(req,res)=>{const id=req.params.id;res.json({...displayCase(get('cases',id),all('sources',id)),sources:all('sources',id),events:all('events',id),documents:all('documents',id).map(({storage,...d})=>d),tasks:all('tasks',id),geometries:all('geometries',id)});});
  app.patch('/api/cases/:id',(req,res)=>{
    const change=z.object({stage:short,category:z.enum(['Preparação','Em andamento','Perícia','Registro','Arquivado','Desistência']),author:short}).parse(req.body);
    const item=get('cases',req.params.id);const before=item.stage;
    transaction(()=>{put('cases',{...item,stage:change.stage,category:change.category});event(item.id,{kind:'decision',title:'Etapa atualizada',body:`${before} → ${change.stage}`,author:change.author});});res.json({ok:true});
  });
  app.post('/api/cases/:id/events',(req,res)=>{
    const data=z.object({title:short,body:text,author:short,kind:z.enum(['activity','decision','contact'])}).parse(req.body);res.status(201).json(event(req.params.id,data));
  });
  app.post('/api/cases/:id/tasks',(req,res)=>{
    const data=z.object({title:short,assignee:short,due:z.iso.date()}).parse(req.body);const task={...data,id:randomUUID(),caseId:req.params.id,done:false,createdAt:new Date().toISOString()};transaction(()=>{put('tasks',task,task.caseId);event(task.caseId,{kind:'activity',title:'Tarefa criada',body:`${task.title} · ${task.assignee} · prazo ${task.due}`});});res.status(201).json(task);
  });
  app.patch('/api/cases/:id/tasks/:taskId',(req,res)=>{
    const t=get('tasks',req.params.taskId);if(!t||t.caseId!==req.params.id)return res.status(404).json({error:'Tarefa não encontrada.'});
    const {done}=z.object({done:z.boolean()}).parse(req.body);transaction(()=>{put('tasks',{...t,done},t.caseId);event(t.caseId,{kind:'activity',title:done?'Tarefa concluída':'Tarefa reaberta',body:t.title});});res.json({ok:true});
  });
  app.post('/api/cases/:id/geometries',(req,res)=>{
    const data=z.object({name:short,kind:z.enum(['Limite do imóvel','Área de interesse']),feature:z.any(),sourceId:z.string().max(100).optional(),id:z.string().optional(),version:z.number().int().optional()}).parse(req.body);
    if(data.sourceId&&!all('sources',req.params.id).some(s=>s.id===data.sourceId))return res.status(400).json({error:'Referência não pertence a este processo.'});
    let validated;try{validated=validateGeometry(data.feature);}catch(e){return res.status(400).json({error:e.message});}
    const existing=data.id?get('geometries',data.id):null;
    if(data.id&&(!existing||existing.caseId!==req.params.id))return res.status(404).json({error:'Área não encontrada.'});
    if(existing&&data.version!==existing.version)return res.status(409).json({error:'A área foi alterada. Reabra o mapa antes de salvar.'});
    const item={...data,...validated,id:existing?.id||randomUUID(),caseId:req.params.id,version:(existing?.version||0)+1,updatedAt:new Date().toISOString(),history:existing?[...(existing.history||[]),{feature:existing.feature,version:existing.version,date:existing.updatedAt}]:[]};
    transaction(()=>{put('geometries',item,item.caseId);event(item.caseId,{kind:'geometry',title:existing?'Geometria revisada':'Área vetorizada',body:`${item.name} · ${item.kind} · versão ${item.version} · ${item.areaM2.toFixed(2)} m² (estimativa geográfica).`});});res.status(201).json(item);
  });
  const upload=multer({storage:multer.memoryStorage(),limits:{fileSize:25*1024*1024,files:1,fields:5}});
  app.post('/api/cases/:id/documents',upload.single('file'),(req,res)=>{
    if(!req.file)return res.status(400).json({error:'Selecione um arquivo.'});
    const data=z.object({category:z.enum(['Matrícula','Planta / memorial','Laudo pericial','Parecer jurídico','Decisão judicial','Acordo','Outros']),geometryId:z.string().optional(),replaces:z.string().optional()}).parse(req.body);
    if(data.geometryId&&!all('geometries',req.params.id).some(g=>g.id===data.geometryId))return res.status(400).json({error:'Área não pertence ao processo.'});
    const previous=data.replaces?get('documents',data.replaces):null;
    if(data.replaces&&(!previous||previous.caseId!==req.params.id))return res.status(400).json({error:'Documento anterior não encontrado neste processo.'});
    if(previous&&all('documents',req.params.id).some(d=>d.replaces===previous.id))return res.status(409).json({error:'Este documento já tem uma versão mais recente.'});
    const ext=path.extname(req.file.originalname).toLowerCase();const bytes=req.file.buffer;
    const valid=ext==='.pdf'?bytes.subarray(0,5).toString()==='%PDF-':ext==='.png'?bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])):['.jpg','.jpeg'].includes(ext)?bytes[0]===255&&bytes[1]===216:['.docx','.xlsx'].includes(ext)?bytes[0]===80&&bytes[1]===75:ext==='.txt'?!bytes.includes(0):false;
    if(!valid)return res.status(400).json({error:'Arquivo inválido. Aceitos: PDF, PNG, JPG, DOCX, XLSX e TXT (até 25 MB).'});
    const id=randomUUID();const filename=path.basename(Buffer.from(req.file.originalname,'latin1').toString('utf8')).replace(/[\x00-\x1f]/g,'');
    const doc={...data,id,caseId:req.params.id,name:filename,size:req.file.size,storage:id+ext,sha256:createHash('sha256').update(bytes).digest('hex'),version:previous?previous.version+1:1,createdAt:new Date().toISOString()};
    fs.writeFileSync(path.join(uploadDir,doc.storage),bytes,{flag:'wx',mode:0o600});
    try{transaction(()=>{put('documents',doc,doc.caseId);event(doc.caseId,{kind:'document',title:previous?'Nova versão de documento':'Documento anexado',body:`${doc.name} · ${doc.category} · versão ${doc.version}`});});}catch(e){fs.unlinkSync(path.join(uploadDir,doc.storage));throw e;}
    const {storage,...safe}=doc;res.status(201).json(safe);
  });
  app.get('/api/cases/:id/documents/:docId/download',(req,res)=>{const d=get('documents',req.params.docId);if(!d||d.caseId!==req.params.id)return res.status(404).json({error:'Documento não encontrado.'});res.download(path.join(uploadDir,d.storage),d.name);});
  app.use('/api',(_req,res)=>res.status(404).json({error:'Rota não encontrada.'}));
  app.use((err,_req,res,_next)=>{if(err instanceof z.ZodError)return res.status(400).json({error:'Revise os campos obrigatórios e o formato das datas.'});if(err instanceof multer.MulterError)return res.status(400).json({error:'Não foi possível anexar. Limite de 25 MB por arquivo.'});if(err.status===400)return res.status(400).json({error:'Solicitação inválida.'});console.error(err.message);res.status(500).json({error:'Não foi possível concluir a operação.'});});
  return {app,store};
}
