import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createApp } from './app.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const {app,store}=createApp({dataDir:process.env.DATA_DIR||path.join(root,'data')});
let vite;
if(process.env.NODE_ENV==='production'){
  const {default:express}=await import('express');app.use(express.static(path.join(root,'dist')));app.get('/{*path}',(_req,res)=>res.sendFile(path.join(root,'dist/index.html')));
}else{
  const {createServer}=await import('vite');vite=await createServer({root,server:{middlewareMode:true},appType:'spa'});app.use(vite.middlewares);
}
const port=Number(process.env.PORT)||3000;
const server=app.listen(port,process.env.HOST||'127.0.0.1');
server.on('listening',()=>console.log(`Território iniciado · porta ${port} · ${store.all('cases').length} cadastros`));
server.on('error',async err=>{console.error(err.code==='EADDRINUSE'?`Porta ${port} em uso. Verifique o serviço existente ou escolha outra PORT.`:err.message);await vite?.close();store.db.close();process.exit(1);});
let closing=false;
for(const signal of ['SIGINT','SIGTERM'])process.once(signal,async()=>{if(closing)return;closing=true;await vite?.close();server.close(()=>{store.db.close();process.exit(0);});server.closeAllConnections();});
