import {useEffect,useRef} from 'react';
import type {ReactNode} from 'react';
import {X,ArrowUpRight,FolderOpen} from 'lucide-react';
export function Badge({children,tone='neutral'}:{children:ReactNode;tone?:string}){return <span className={`badge ${tone}`}><i/>{children}</span>;}
export function Category({value}:{value:string}){return <Badge tone={value==='Perícia'?'purple':value==='Registro'?'green':value==='Preparação'?'amber':value==='Em andamento'?'blue':'neutral'}>{value}</Badge>;}
export function Empty({title,body,action}:{title:string;body:string;action?:ReactNode}){return <div className="empty-state"><div className="empty-icon"><FolderOpen size={25}/></div><h3>{title}</h3><p>{body}</p>{action}</div>;}
export function Modal({title,subtitle,onClose,children}:{title:string;subtitle?:string;onClose:()=>void;children:ReactNode}){
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{const previous=document.activeElement as HTMLElement;const el=ref.current;el?.querySelector<HTMLElement>('input,select,textarea,button')?.focus();const key=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose();if(e.key==='Tab'){const nodes=el?.querySelectorAll<HTMLElement>('button:not(:disabled),input,select,textarea,a[href]');if(!nodes?.length)return;const first=nodes[0],last=nodes[nodes.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}};document.addEventListener('keydown',key);return()=>{document.removeEventListener('keydown',key);previous?.focus();};},[]);
 return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}><div className="modal" ref={ref} role="dialog" aria-modal="true" aria-labelledby="modal-title"><div className="modal-heading"><div><h2 id="modal-title">{title}</h2>{subtitle&&<p>{subtitle}</p>}</div><button className="icon-button" aria-label="Fechar" onClick={onClose}><X size={20}/></button></div>{children}</div></div>;
}
export function TextLink({children,onClick}:{children:ReactNode;onClick:()=>void}){return <button className="text-link" onClick={onClick}>{children}<ArrowUpRight size={15}/></button>;}
