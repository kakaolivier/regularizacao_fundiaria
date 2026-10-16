export async function api<T>(url:string,options:RequestInit={}):Promise<T>{
  const res=await fetch('/api'+url,{...options,headers:{...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...options.headers}});
  if(!res.ok){let msg='Não foi possível conectar ao servidor.';try{msg=(await res.json()).error||msg;}catch{}throw new Error(msg);}
  return res.json();
}
export const send=(method:string,body:unknown):RequestInit=>({method,body:JSON.stringify(body)});
export const fmt=(n:number)=>new Intl.NumberFormat('pt-BR',{maximumFractionDigits:0}).format(n);
export const money=(n:number)=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(n);
export const date=(s:string)=>new Date(s.length===10?s+'T12:00:00':s).toLocaleDateString('pt-BR');
export const normalize=(s:string)=>s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
export const cityLabel=(s:string)=>s.replace(/ De /g,' de ').replace(/ Da /g,' da ');
export function downloadJSON(data:unknown,name:string){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/geo+json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
