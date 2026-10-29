"""Business rules shared by the HTML pages and the compatibility JSON API."""
import hashlib
import json
import math
import re
from datetime import date
from pathlib import Path
from uuid import uuid4
from shapely.geometry import shape
from .store import now

CATEGORIES = ['Preparação', 'Em andamento', 'Perícia', 'Registro', 'Arquivado', 'Desistência']
METHODS = ['A definir', 'Judicial', 'Extrajudicial']
DOCUMENT_CATEGORIES = ['Matrícula', 'Planta / memorial', 'Laudo pericial', 'Parecer jurídico', 'Decisão judicial', 'Acordo', 'Outros']
FINANCIAL_NAMES = {'deposit': 'Indenização depositada', 'depositUpdated': 'Depósito atualizado · estimativa', 'proposal': 'Proposta do expropriado', 'award': 'Primeiro laudo pericial', 'secondAward': 'Segundo laudo pericial', 'awardUpdated': 'Laudo atualizado · estimativa', 'legalFees': 'Honorários sucumbenciais · estimativa', 'estimatedRemaining': 'A desembolsar · estimativa', 'estimatedTotal': 'Depósito + custo pericial · estimativa', 'expertCost': 'Custo pericial · estimativa', 'expertFees': 'Honorários periciais', 'sentence': 'Sentença / acordo', 'agreement': 'Valor do acordo', 'bond': 'Caução', 'totalDeposit': 'Total depositado', 'recoverIndemnity': 'A reaver · indenização', 'recoverBond': 'A reaver · caução', 'reimbursed': 'Valor reembolsado'}


class Problem(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


def text(data, key, limit=200, required=True):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value.strip()) > limit or (required and not value.strip()):
        raise Problem(f'Revise o campo {key}: texto obrigatório, até {limit} caracteres.' if required else f'Valor inválido para {key}.')
    return value.strip()


def choice(data, key, allowed):
    value = text(data, key)
    if value not in allowed:
        raise Problem(f'Opção inválida para {key}.')
    return value


def cnj(value):
    stripped = re.sub(r'[.\-\s]', '', value)
    return stripped if re.fullmatch(r'[0-9]{20}', stripped) else None


def require_case(store, case_id):
    item = store.get('cases', case_id)
    if not item:
        raise Problem('Processo não encontrado.', 404)
    return item


def display_case(item, sources):
    kinds = {s.get('kind') for s in sources}
    return {**item, 'expertStage': 'Conferir divergência entre abas' if {'laudo', 'pericia'} <= kinds else item.get('expertStage', '')}


def bootstrap(store):
    sources = {s['id']: s for s in store.all('sources')}
    geometries = store.all('geometries')
    cases = []
    for item in store.all('cases'):
        related = [sources[key] for key in item.get('sourceIds', []) if key in sources]
        cases.append({**display_case(item, related), 'searchText': ' '.join(str(s.get(k, '')) for s in related for k in ('title', 'owner', 'process', 'section', 'gisId', 'registry')), 'geometryCount': sum(g['caseId'] == item['id'] for g in geometries)})
    return {'cases': cases, 'geometries': geometries, 'tasks': store.all('tasks'), 'meta': store.get('meta', 'import') or {'workbooks': [], 'summary': {}, 'supplementary': []}}


def detail(store, case_id):
    item = require_case(store, case_id)
    sources = store.all('sources', case_id)
    return {**display_case(item, sources), 'sources': sources, 'events': store.all('events', case_id), 'tasks': store.all('tasks', case_id), 'geometries': store.all('geometries', case_id), 'documents': [{k: v for k, v in d.items() if k != 'storage'} for d in store.all('documents', case_id)]}


def create_case(store, data):
    item = {key: text(data, key) for key in ('title', 'city', 'owner')}
    item.update(number=text(data, 'number', 120, False), section=text(data, 'section', 200, False), method=choice(data, 'method', METHODS))
    normalized = cnj(item['number'])
    item.update(id=str(uuid4()), stage='Cadastro inicial', category='Preparação', expertStage='', hasExpert=False, hasAward=False, hasRegistry=False, sourceCount=0, sourceIds=[], origins=[], needsReconciliation=not bool(normalized), createdAt=now())
    with store.transaction():
        if normalized and any(cnj(c.get('number', '')) == normalized for c in store.all('cases')):
            raise Problem('Já existe um cadastro com esse número de processo.', 409)
        store.put('cases', item)
        store.event(item['id'], kind='activity', title='Processo cadastrado', body='Cadastro criado neste ambiente.')
    return item


def update_stage(store, case_id, data):
    stage = text(data, 'stage')
    category = choice(data, 'category', CATEGORIES)
    author = text(data, 'author')
    with store.transaction():
        item = require_case(store, case_id)
        before = item['stage']
        store.put('cases', {**item, 'stage': stage, 'category': category})
        store.event(case_id, kind='decision', title='Etapa atualizada', body=f'{before} → {stage}', author=author)
    return {'ok': True}


def add_event(store, case_id, data):
    require_case(store, case_id)
    return store.event(case_id, title=text(data, 'title'), body=text(data, 'body', 2000), author=text(data, 'author'), kind=choice(data, 'kind', ['activity', 'decision', 'contact']))


def add_task(store, case_id, data):
    require_case(store, case_id)
    due = text(data, 'due', 10)
    try:
        if date.fromisoformat(due).isoformat() != due:
            raise ValueError()
    except ValueError:
        raise Problem('Informe uma data de prazo válida (AAAA-MM-DD).') from None
    item = {'id': str(uuid4()), 'caseId': case_id, 'title': text(data, 'title'), 'assignee': text(data, 'assignee'), 'due': due, 'done': False, 'createdAt': now()}
    with store.transaction():
        store.put('tasks', item, case_id)
        store.event(case_id, kind='activity', title='Tarefa criada', body=f"{item['title']} · {item['assignee']} · prazo {due}")
    return item


def toggle_task(store, case_id, task_id, done):
    require_case(store, case_id)
    if type(done) is not bool:
        raise Problem('Informe se a tarefa está concluída.')
    with store.transaction():
        task = store.get('tasks', task_id)
        if not task or task['caseId'] != case_id:
            raise Problem('Tarefa não encontrada.', 404)
        store.put('tasks', {**task, 'done': done}, case_id)
        store.event(case_id, kind='activity', title='Tarefa concluída' if done else 'Tarefa reaberta', body=task['title'])
    return {'ok': True}


def _ring_area(ring):
    # Same spherical surface integral as Turf: WGS84 lon/lat, radius 6,371,008.8 m.
    total = 0.0
    for i in range(len(ring) - 1):
        previous = ring[(i - 1) % (len(ring) - 1)]
        following = ring[(i + 1) % (len(ring) - 1)]
        total += math.radians(following[0] - previous[0]) * math.sin(math.radians(ring[i][1]))
    return abs(total * 6371008.8 ** 2 / 2)


def validate_geometry(feature):
    if not isinstance(feature, dict) or feature.get('type') != 'Feature' or not isinstance(feature.get('geometry'), dict):
        raise Problem('Importe uma Feature GeoJSON Polygon ou MultiPolygon em WGS84.')
    if 'crs' in feature or 'crs' in feature['geometry']:
        raise Problem('Use longitude/latitude WGS84 (EPSG:4326), sem projeção alternativa.')
    if len(json.dumps(feature).encode('utf-8')) > 500000:
        raise Problem('Limite de 500 KB por geometria.')
    geometry = feature['geometry']
    if geometry.get('type') not in ('Polygon', 'MultiPolygon'):
        raise Problem('A geometria precisa ser Polygon ou MultiPolygon.')
    polygons = [geometry.get('coordinates')] if geometry['type'] == 'Polygon' else geometry.get('coordinates')
    if not isinstance(polygons, list) or not polygons:
        raise Problem('Polígono vazio.')
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            raise Problem('Polígono vazio.')
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4:
                raise Problem('Cada anel precisa de três vértices e fechamento.')
            for position in ring:
                if not isinstance(position, list) or len(position) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in position) or abs(position[0]) > 180 or abs(position[1]) > 90:
                    raise Problem('Coordenadas inválidas. Use longitude e latitude WGS84.')
            if ring[0] != ring[-1]:
                raise Problem('O polígono deve estar fechado.')
    safe = {'type': 'Feature', 'properties': {}, 'geometry': {'type': geometry['type'], 'coordinates': geometry['coordinates']}}
    polygon = shape(safe['geometry'])
    if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
        raise Problem('Polígono inválido, com cruzamento de linhas ou área nula.')
    area = sum(_ring_area(p[0]) - sum(_ring_area(hole) for hole in p[1:]) for p in polygons)
    if not math.isfinite(area) or area <= 0:
        raise Problem('A geometria precisa ter área positiva.')
    return {'feature': safe, 'areaM2': area}


def save_geometry(store, case_id, data):
    require_case(store, case_id)
    name = text(data, 'name')
    kind = choice(data, 'kind', ['Limite do imóvel', 'Área de interesse'])
    validated = validate_geometry(data.get('feature'))
    source_id = text(data, 'sourceId', 100, False)
    if source_id and not any(s['id'] == source_id for s in store.all('sources', case_id)):
        raise Problem('A referência não pertence a este processo.')
    identifier = text(data, 'id', 100, False)
    with store.transaction():
        previous = store.get('geometries', identifier) if identifier else None
        if identifier and (not previous or previous['caseId'] != case_id):
            raise Problem('Área não encontrada.', 404)
        if previous and (type(data.get('version')) is not int or data['version'] != previous['version']):
            raise Problem('A área foi alterada. Reabra o mapa antes de salvar.', 409)
        history = previous.get('history', []) + [{'feature': previous['feature'], 'version': previous['version'], 'date': previous['updatedAt']}] if previous else []
        item = {'id': identifier or str(uuid4()), 'caseId': case_id, 'name': name, 'kind': kind, 'sourceId': source_id, **validated, 'version': previous['version'] + 1 if previous else 1, 'updatedAt': now(), 'history': history}
        store.put('geometries', item, case_id)
        store.event(case_id, kind='geometry', title='Geometria revisada' if previous else 'Área vetorizada', body=f"{name} · {kind} · versão {item['version']} · {item['areaM2']:.2f} m² (estimativa geográfica).")
    return item


def add_document(store, case_id, data, file):
    require_case(store, case_id)
    if file is None or not file.filename:
        raise Problem('Selecione um arquivo.')
    category = choice(data, 'category', DOCUMENT_CATEGORIES)
    geometry_id = text(data, 'geometryId', 100, False)
    replaces = text(data, 'replaces', 100, False)
    if geometry_id and not any(g['id'] == geometry_id for g in store.all('geometries', case_id)):
        raise Problem('Área não pertence ao processo.')
    filename = re.sub(r'[\x00-\x1f]', '', file.filename.replace('\\', '/').split('/')[-1])
    extension = Path(filename).suffix.lower()
    blob = file.read(25 * 1024 * 1024 + 1)
    if len(blob) > 25 * 1024 * 1024:
        raise Problem('Limite de 25 MB por arquivo.', 413)
    valid = (extension == '.pdf' and blob.startswith(b'%PDF-')) or (extension == '.png' and blob.startswith(b'\x89PNG\r\n\x1a\n')) or (extension in ('.jpg', '.jpeg') and blob.startswith(b'\xff\xd8')) or (extension in ('.docx', '.xlsx') and blob.startswith(b'PK')) or (extension == '.txt' and bool(blob) and b'\0' not in blob)
    if not valid:
        raise Problem('Arquivo inválido. Aceitos: PDF, PNG, JPG, DOCX, XLSX e TXT.')
    identifier = str(uuid4())
    upload_dir = store.directory / 'uploads'
    upload_dir.mkdir(exist_ok=True)
    destination = upload_dir / (identifier + extension)
    try:
        with store.transaction():
            previous = store.get('documents', replaces) if replaces else None
            if replaces and (not previous or previous['caseId'] != case_id):
                raise Problem('Documento anterior não encontrado neste processo.')
            if previous and any(d.get('replaces') == replaces for d in store.all('documents', case_id)):
                raise Problem('Este documento já tem uma versão mais recente.', 409)
            item = {'id': identifier, 'caseId': case_id, 'name': filename, 'category': category, 'geometryId': geometry_id, 'replaces': replaces, 'size': len(blob), 'storage': destination.name, 'sha256': hashlib.sha256(blob).hexdigest(), 'version': previous['version'] + 1 if previous else 1, 'createdAt': now()}
            with destination.open('xb') as target:
                target.write(blob)
            store.put('documents', item, case_id)
            store.event(case_id, kind='document', title='Nova versão de documento' if previous else 'Documento anexado', body=f"{filename} · {category} · versão {item['version']}")
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {k: v for k, v in item.items() if k != 'storage'}
