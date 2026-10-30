"""Import the supplied workbook layouts without changing the originals.
Only a complete, unambiguous 20-digit CNJ identifier joins records across sources.
No geographic coordinates, dates from prose, or financial values are invented.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
EMPTY = {'', '-', 'N/A', 'NA', 'NÃO SE APLICA', 'NONE'}

def clean(v):
    if v is None: return ''
    if isinstance(v, (datetime, date)): return v.isoformat()[:10]
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    return str(v).strip()

def val(v):
    s = clean(v)
    return '' if s.upper() in EMPTY else s

def norm(v):
    return ''.join(c for c in unicodedata.normalize('NFD', clean(v).lower()) if unicodedata.category(c) != 'Mn')

def uid(v): return hashlib.sha256(v.encode()).hexdigest()[:16]

def cnj(v):
    # Nonstandard/truncated numbers stay separate, available for manual reconciliation.
    s = re.sub(r'\D', '', clean(v))
    return s if len(s) == 20 and re.fullmatch(r'[\d.\-\s]+', clean(v)) else None

def number(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool): return round(float(v), 4)
    return None

def rows_from_xml(wb, sheet, big=False):
    """Stream real cells: Rev.112 has formulas copied to Excel's last row."""
    ss = sheet._shared_strings
    rows = {}; merges = []; skipped = 0
    with wb._archive.open(sheet._worksheet_path) as stream:
        parent = None
        for ev, el in ET.iterparse(stream, events=('start', 'end')):
            if ev == 'start' and el.tag == NS+'sheetData': parent = el
            if ev != 'end': continue
            if el.tag == NS+'mergeCell': merges.append(el.attrib['ref'])
            if el.tag != NS+'row': continue
            idx = int(el.attrib['r']); record = {}
            for cell in el:
                ref = re.sub(r'\d+', '', cell.attrib.get('r',''))
                t = cell.attrib.get('t'); value = cell.find(NS+'v'); raw = value.text if value is not None else None
                if t == 's' and raw is not None: raw = ss[int(raw)]
                elif t == 'inlineStr': raw = ''.join(n.text or '' for n in cell.iter(NS+'t'))
                elif t == 'e': raw = 'Erro de fórmula: ' + (raw or 'sem resultado')
                elif raw is not None and t not in ('str', 'd'):
                    try:
                        raw = float(raw)
                        if int(cell.attrib.get('s',0)) in wb._date_formats: raw = from_excel(raw, wb.epoch)
                        elif raw.is_integer(): raw = int(raw)
                    except (ValueError, OverflowError): pass
                if raw is not None: record[ref] = raw
            if record and (not big or idx <= 5 or (clean(record.get('E')) and (clean(record.get('F')) or val(record.get('I'))))):
                rows[idx] = record
            else: skipped += 1
            el.clear()
            if parent is not None: parent.clear()
    # Expand merged cells only within the actual source range; preserve row provenance.
    from openpyxl.utils.cell import range_boundaries, get_column_letter
    for rng in merges:
        a,b,c,d = range_boundaries(rng)
        if d-b > 1000: continue
        value = rows.get(b,{}).get(get_column_letter(a))
        if value is None: continue
        for r in range(b,d+1):
            if r not in rows: continue
            for col in range(a,c+1): rows[r].setdefault(get_column_letter(col),value)
    return rows, skipped


def run(paths, output):
    sources=[]; books=[]; supplementary=[]
    for path in paths:
        wb=load_workbook(path,read_only=True,data_only=True)
        if 'BANCO_REG' in wb.sheetnames or 'DICIONARIO_DADOS' in wb.sheetnames:
            wb.close()
            raise SystemExit('Para o novo controle, abra o site e use Base de dados > Importar controle. O dicionário já está incorporado. Nenhum seed foi gravado.')
        is_expert='LAUDOS APRESENTADOS' in wb.sheetnames
        bookid='pericias' if is_expert else 'acompanhamento'
        info={'id':bookid,'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sheets':[]}
        for sheet in wb:
            name=sheet.title; rows,skipped=rows_from_xml(wb,sheet,big=name=='Processos ajuizados')
            conf=None
            if name=='Processos ajuizados': conf=(5,'E','F','G','H','I','judicial')
            elif name=='Processos a serem ajuizados': conf=(4,'G','F',None,'C','D','preparacao')
            elif name=='Caução - Reembolso': conf=(4,'B','C',None,'D','E','caucao')
            elif name.strip()=='REGISTROS': conf=(4,'D','E','F','K','M','registro')
            elif name.strip()=='Processos - ANEXO II 4º TA': conf=(4,None,'D','E','I','C','anexo')
            elif name=='LAUDOS APRESENTADOS': conf=(11,'B','C','D','F','E','laudo')
            elif name=='LAUDOS AINDA NÃO APRESENTADO': conf=(8,'A','B','C','E','D','pericia')
            count=0
            if conf:
                header,municip,title,section,owner,process,kind=conf
                headers={k:clean(v).replace('\n',' ') for k,v in rows.get(header,{}).items()}
                if kind=='caucao': headers.update({'L':'REAVER — INDENIZAÇÃO','M':'REAVER — CAUÇÃO'})
                for n,row in rows.items():
                    if n<=max(header,5 if kind in ('anexo','caucao') else header) or not (val(row.get(title)) or val(row.get(process))): continue
                    if kind in ('judicial','registro','laudo','pericia','caucao','preparacao') and not val(row.get(municip)): continue
                    if kind=='caucao' and not cnj(row.get(process)): continue
                    if kind=='anexo' and not val(row.get(process)): continue
                    limit={'judicial':'AW','caucao':'R','registro':'P','anexo':'K','laudo':'V','pericia':'O','preparacao':'L'}[kind]
                    def colnum(s):
                        v=0
                        for ch in s: v=v*26+ord(ch)-64
                        return v
                    fields=[{'column':k,'label':headers.get(k,k),'value':clean(v)} for k,v in row.items() if colnum(k)<=colnum(limit) and k in headers]
                    def g(k): return val(row.get(k))
                    numeric={}
                    mapping={'judicial':{'deposit':'V','proposal':'W','award':'X','sentence':'AB','agreement':'AD'},'laudo':{'deposit':'G','depositUpdated':'H','award':'J','secondAward':'K','awardUpdated':'L','legalFees':'M','estimatedRemaining':'O'},'pericia':{'deposit':'F','depositUpdated':'G','expertCost':'I','estimatedTotal':'J','expertFees':'M'},'caucao':{'deposit':'F','bond':'G','totalDeposit':'J','sentence':'K','recoverIndemnity':'L','recoverBond':'M','reimbursed':'N'},'preparacao':{'deposit':'H'}}.get(kind,{})
                    for key,col in mapping.items():
                        if number(row.get(col)) is not None: numeric[key]=number(row[col])
                    stage={'judicial':g('J'),'preparacao':g('I'),'registro':g('N'),'anexo':g('J'),'laudo':g('S'),'pericia':g('N'),'caucao':''}[kind]
                    notes={'judicial':g('AN'),'preparacao':g('J'),'registro':'','anexo':g('K'),'laudo':g('T'),'pericia':g('K'),'caucao':g('P')}[kind]
                    events=[]
                    dates={'judicial':{'S':'Solicitação de ajuizamento','T':'Petição inicial','AE':'Acordo assinado','AH':'Mandado cumprido','AK':'Registro de imissão provisória','AL':'Registro definitivo','AM':'Arquivamento'},'registro':{'O':'Registro de imissão de posse','P':'Registro definitivo'},'caucao':{'O':'Reembolso'}}.get(kind,{})
                    for col,label in dates.items():
                        d=row.get(col)
                        if isinstance(d,(date,datetime)): events.append({'date':clean(d),'title':label})
                    source={'id':uid(bookid+name+str(n)), 'workbook':bookid,'filename':path.name,'sheet':name,'row':n,'kind':kind,'title':g(title) or 'Imóvel não informado','city':g(municip) if municip else 'Não informado','section':g(section) if section else '', 'owner':g(owner),'process':g(process),'cnj':cnj(row.get(process)), 'stage':stage,'notes':notes,'fields':fields,'financial':numeric,'events':events,'registry':g('P') if kind=='judicial' else g('I') if kind=='registro' else g('G') if kind=='anexo' else '', 'gisId':g('C') if kind=='judicial' else '', 'area':g('N') if kind=='judicial' else g('G') if kind=='registro' else g('F') if kind=='anexo' else g('E') if kind=='preparacao' else '', 'method':g('L') if kind=='registro' else 'Judicial' if kind in ('judicial','laudo','pericia','caucao','anexo') else 'A definir', 'release':g('AI') if kind=='judicial' else ''}
                    sources.append(source); count+=1
            else:
                supplementary.append({'workbook':bookid,'sheet':name,'rows':[{'row':n,'cells':{k:clean(v) for k,v in row.items()}} for n,row in rows.items()]})
            info['sheets'].append({'name':name,'records':count,'role':'operacional' if conf else 'referência','ignoredFormulaRows':skipped if name=='Processos ajuizados' else 0})
        books.append(info); wb.close()
    grouped={}
    for s in sources:
        key='cnj-'+s['cnj'] if s['cnj'] else 'ref-'+s['id']
        grouped.setdefault(key,[]).append(s)
    cases=[]
    for key,items in grouped.items():
        ordered=sorted(items,key=lambda s: {'judicial':0,'registro':1,'laudo':2,'pericia':3,'preparacao':4,'anexo':5,'caucao':6}[s['kind']])
        main=ordered[0]; expert=next((s for s in items if s['kind'] in ('laudo','pericia')),None)
        stage=next((s['stage'] for s in ordered if s['stage'] and s['kind']!='anexo'),'Etapa não informada')
        # Pericial and registry status are independent; avoid implying one supersedes the other.
        if expert: category='Perícia'
        elif any(s['kind']=='preparacao' for s in items): category='Preparação'
        elif 'arquivado' in norm(stage): category='Arquivado'
        elif 'desistencia' in norm(stage): category='Desistência'
        elif any(s['kind']=='registro' for s in items) or 'registro' in norm(stage): category='Registro'
        else: category='Em andamento'
        cases.append({'id':key,'title':main['title'],'number':main['process'],'city':main['city'].title(),'owner':main['owner'],'section':main['section'],'method':main['method'].capitalize(),'stage':stage,'category':category,'expertStage':expert['stage'] if expert else '', 'hasExpert':bool(expert),'hasAward':any(s['kind']=='laudo' for s in items),'hasRegistry':any(s['kind']=='registro' for s in items),'sourceCount':len(items),'sourceIds':[s['id'] for s in items], 'needsReconciliation':not bool(main['cnj']),'origins':list(dict.fromkeys(s['workbook'] for s in items))})
    counts=Counter(s['kind'] for s in sources)
    result={'importedAt':datetime.now(timezone.utc).isoformat(),'workbooks':books,'cases':cases,'sources':sources,'supplementary':supplementary,'summary':{'cases':len(cases),'records':len(sources),'byKind':dict(counts),'linkedBoth':sum(len(c['origins'])==2 for c in cases),'pendingReconciliation':sum(c['needsReconciliation'] for c in cases),'hasCoordinates':False}}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result['summary'],ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('files',nargs='+',type=Path); p.add_argument('--output',type=Path,default=Path('data/seed.json')); args=p.parse_args(); run(args.files,args.output)
