"""Território: Python application factory, HTML interface and JSON API."""
import csv
import io
import json
import os
import re
import secrets
import unicodedata
import time
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask, Response, flash, g, jsonify, redirect, render_template, request, send_file, send_from_directory, session, url_for
from werkzeug.exceptions import HTTPException
from .store import Store
from . import services as svc
from . import regularizacao as reg

ROOT = Path(__file__).resolve().parent.parent


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', str(value).lower()) if unicodedata.category(c) != 'Mn')


def filter_cases(cases, args, expert=False):
    query = normalize(args.get('q', ''))
    return [c for c in cases if (not expert or c.get('hasExpert')) and (not query or query in normalize(' '.join(str(c.get(k, '')) for k in ('title', 'number', 'owner', 'city', 'section', 'searchText')) + ' ' + re.sub(r'\D', '', c.get('number', '')))) and (not args.get('city') or c['city'] == args['city']) and (not args.get('category') or c['category'] == args['category']) and (not args.get('method') or c['method'] == args['method']) and (not args.get('reconcile') or c.get('needsReconciliation'))]


def create_app(data_dir=None, testing=False):
    app = Flask(__name__)
    directory = Path(data_dir or os.environ.get('DATA_DIR') or ROOT / 'data').resolve()
    initial = Store(directory, initialize=True)
    initial.close()
    key_path = directory / '.session-key'
    try:
        with key_path.open('xb') as f:
            f.write(secrets.token_bytes(32))
    except FileExistsError:
        pass
    app.config.update(DATA_DIR=directory, SECRET_KEY=key_path.read_bytes(), TESTING=testing, MAX_CONTENT_LENGTH=26 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict', TRUSTED_HOSTS=['localhost', '127.0.0.1', '[::1]'])

    def store():
        if 'store' not in g:
            g.store = Store(directory)
        return g.store

    @app.teardown_appcontext
    def close(_error):
        value = g.pop('store', None)
        if value:
            value.close()

    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    @app.before_request
    def protect_writes():
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('Origin')
            if origin and urlsplit(origin).netloc != request.host:
                raise svc.Problem('Origem não autorizada.', 403)
            if not request.path.startswith('/api/'):
                submitted = request.form.get('_csrf', '')
                if not session.get('csrf') or not secrets.compare_digest(submitted, session['csrf']):
                    raise svc.Problem('A sessão do formulário expirou. Recarregue a página e tente novamente.', 403)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['X-Frame-Options'] = 'DENY'
        if not request.path.startswith(('/static/', '/maps/')):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(svc.Problem)
    def problem(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.message), error.status
        return render_template('error.html', message=error.message, data=svc.bootstrap(store()), nav=''), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        message = 'Limite de 25 MB por arquivo.' if error.code == 413 else 'Página ou solicitação indisponível.'
        if request.path.startswith('/api/'):
            return jsonify(error=message), error.code
        return render_template('error.html', message=message, data=svc.bootstrap(store()), nav=''), error.code

    @app.context_processor
    def constants():
        return {'csrf_token': csrf_token, 'categories': svc.CATEGORIES, 'methods': svc.METHODS, 'document_categories': svc.DOCUMENT_CATEGORIES, 'financial_names': svc.FINANCIAL_NAMES, 'today': date.today().isoformat(), 'record_fields': reg.FIELDS, 'record_groups': reg.GROUPS, 'meaningful': reg.meaningful, 'page_names': {'overview': 'Visão geral', 'processes': 'Processos', 'records': 'Imóveis e trechos', 'map': 'Mapa territorial', 'expert': 'Perícias e avaliações', 'tasks': 'Tarefas e prazos', 'sources': 'Base de dados', 'planner': 'Planejamento'}}

    @app.template_filter('brnumber')
    def brnumber(value, places=0):
        return f'{float(value):,.{places}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @app.template_filter('money')
    def money(value):
        return 'R$ ' + brnumber(value, 2)

    @app.template_filter('controlvalue')
    def controlvalue(value, kind):
        if kind == 'date' and reg.iso_date(value):
            return reg.iso_date(value).strftime('%d/%m/%Y')
        if kind == 'money' and re.fullmatch(r'\d+(?:\.\d+)?', value):
            return money(value)
        return value or 'Não informado'

    @app.template_filter('brdate')
    def brdate(value):
        if not value:
            return 'Sem data individual'
        return datetime.fromisoformat(value[:10]).strftime('%d/%m/%Y')

    def render(name, nav, **extra):
        data = svc.bootstrap(store())
        return render_template(name, data=data, nav=nav, **extra)

    @app.get('/')
    def overview():
        data = svc.bootstrap(store())
        cities = Counter(c['city'] for c in data['cases']).most_common(6)
        return render_template('overview.html', data=data, nav='overview', cities=cities)

    @app.get('/pericias')
    @app.get('/processos')
    def processes():
        data = svc.bootstrap(store())
        expert = request.path == '/pericias'
        rows = filter_cases(data['cases'], request.args, expert)
        pages = max(1, (len(rows) + 11) // 12)
        try:
            page = max(1, min(pages, int(request.args.get('page', 1))))
        except ValueError:
            page = 1
        args = request.args.to_dict()
        args.pop('page', None)
        args.pop('expert', None)
        return render_template('processes.html', data=data, nav='expert' if expert else 'processes', rows=rows[(page - 1) * 12:page * 12], total=len(rows), page=page, pages=pages, cities=sorted({c['city'] for c in data['cases']}), filter_args=args, expert=expert)

    @app.get('/processos/exportar.csv')
    def export_csv():
        rows = filter_cases(svc.bootstrap(store())['cases'], request.args, request.args.get('expert') == '1')
        out = io.StringIO(newline='')
        writer = csv.writer(out, delimiter=';')
        def cell(value):
            value = str(value)
            return "'" + value if value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value
        writer.writerow(['Imóvel', 'Processo', 'Município', 'Proprietário', 'Modalidade', 'Etapa', 'Fase pericial'])
        for c in rows:
            writer.writerow([cell(c.get(key, '')) for key in ('title', 'number', 'city', 'owner', 'method', 'stage', 'expertStage')])
        return Response('\ufeff' + out.getvalue(), content_type='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename=territorio-processos.csv'})

    @app.get('/processos/<case_id>')
    def case_detail(case_id):
        item = svc.detail(store(), case_id)
        item['events'].sort(key=lambda e: e.get('date') or '', reverse=True)
        tab = request.args.get('tab', 'resumo')
        if tab not in ('resumo', 'historico', 'documentos', 'mapa', 'origem'):
            tab = 'resumo'
        return render('detail.html', 'processes', case=item, tab=tab)

    @app.get('/mapa')
    def map_page():
        return render('map.html', 'map')

    @app.get('/tarefas')
    def tasks_page():
        return render('tasks.html', 'tasks')

    @app.get('/fontes')
    def sources_page():
        return render('sources.html', 'sources')

    @app.get('/imoveis')
    def records_page():
        rows = [reg.record_view(r) for r in store().all('records')]
        cities = sorted({r['city'] for r in rows})
        stages = sorted({r['stage'] for r in rows})
        query = normalize(request.args.get('q', ''))
        rows = [r for r in rows if (not query or query in normalize(' '.join(r['values'].values()) + ' ' + re.sub(r'\D', '', r['number'])))
                and (not request.args.get('city') or r['city'] == request.args['city'])
                and (not request.args.get('stage') or r['stage'] == request.args['stage'])
                and (not request.args.get('pending') or r['warnings'])
                and (not request.args.get('mandate') or bool(reg.iso_date(r['values'].get('AO', ''))) == (request.args['mandate'] == 'yes'))]
        total = len(rows)
        pages = max(1, (total + 19) // 20)
        try:
            page = max(1, min(pages, int(request.args.get('page', 1))))
        except ValueError:
            page = 1
        filters = request.args.to_dict()
        filters.pop('page', None)
        return render('records.html', 'records', rows=rows[(page-1)*20:page*20], total=total, pages=pages, page=page, cities=cities, stages=stages, filter_args=filters)

    @app.route('/imoveis/<identifier>', methods=['GET', 'POST'])
    def record_detail(identifier):
        record = store().get('records', identifier)
        if not record:
            raise svc.Problem('Imóvel / trecho não encontrado.', 404)
        if request.method == 'POST':
            reg.update_record(store(), identifier, request.form)
            flash('Atualização salva. Valores anteriores e motivo registrados no histórico.')
            return redirect(url_for('record_detail', identifier=identifier, group=request.form.get('group')), 303)
        group = request.args.get('group', 'CADASTRO')
        if group not in reg.GROUPS:
            group = 'CADASTRO'
        events = [e for e in store().all('events', record['caseId']) if e.get('recordId') == identifier]
        events.sort(key=lambda e: e.get('createdAt', ''), reverse=True)
        return render('record_detail.html', 'records', record=reg.record_view(record), group=group, events=events,
                      sources=[store().get('sources', s) for s in record['sourceIds']])

    @app.route('/importar', methods=['GET', 'POST'])
    def import_control():
        if request.method == 'GET':
            return render('import_control.html', 'sources', preview=None, plan=None)
        upload = request.files.get('workbook')
        if not upload or not upload.filename or not upload.filename.lower().endswith('.xlsx'):
            raise svc.Problem('Selecione o arquivo CONTROLE_REGULARIZACAO.xlsx.')
        raw = upload.read(25 * 1024 * 1024 + 1)
        if len(raw) > 25 * 1024 * 1024:
            raise svc.Problem('Limite de 25 MB por planilha.', 413)
        previews = directory / 'import-previews'
        previews.mkdir(exist_ok=True)
        # Expired previews are temporary; committed source snapshots remain in SQLite.
        for path in previews.glob('*.json'):
            if time.time() - path.stat().st_mtime > 86400:
                path.unlink(missing_ok=True)
        token = secrets.token_hex(24)
        temporary = previews / (token + '.xlsx')
        try:
            temporary.write_bytes(raw)
            preview = reg.read_control(temporary, upload.filename.replace('\\', '/').split('/')[-1])
        finally:
            temporary.unlink(missing_ok=True)
        plan = reg.plan_import(store(), preview)
        preview['fingerprint'] = plan['fingerprint']
        (previews / (token + '.json')).write_text(json.dumps(preview, ensure_ascii=False), encoding='utf-8')
        session['import_preview'] = token
        return redirect(url_for('import_preview', token=token), 303)

    def read_preview(token):
        if not re.fullmatch(r'[a-f0-9]{48}', token) or session.get('import_preview') != token:
            raise svc.Problem('Prévia indisponível nesta sessão. Selecione a planilha novamente.', 404)
        path = directory / 'import-previews' / (token + '.json')
        if not path.is_file() or time.time() - path.stat().st_mtime > 86400:
            raise svc.Problem('A prévia expirou. Selecione a planilha novamente.', 410)
        return json.loads(path.read_text(encoding='utf-8'))

    @app.get('/importar/<token>')
    def import_preview(token):
        preview = read_preview(token)
        plan = reg.plan_import(store(), preview)
        rows = [i for i in plan['items'] if not request.args.get('status') or i['status'] == request.args['status']]
        pages = max(1, (len(rows) + 19) // 20)
        try:
            page = max(1, min(pages, int(request.args.get('page', 1))))
        except ValueError:
            page = 1
        return render('import_control.html', 'sources', preview=preview, plan=plan, token=token,
                      changed=plan['fingerprint'] != preview['fingerprint'], preview_rows=rows[(page-1)*20:page*20],
                      preview_total=len(rows), page=page, pages=pages)

    @app.post('/importar/<token>/confirmar')
    def confirm_import(token):
        preview = read_preview(token)
        report = reg.apply_import(store(), preview, preview['fingerprint'], request.form.get('author', ''))
        (directory / 'import-previews' / (token + '.json')).unlink(missing_ok=True)
        session.pop('import_preview', None)
        flash(f"Importação concluída: {report['counts'].get('new', 0)} imóveis novos, {report['counts'].get('updated', 0)} atualizados e {report['counts'].get('blocked', 0)} linhas separadas para conferência.")
        return redirect(url_for('sources_page'), 303)

    @app.get('/planejamento')
    def planner_page():
        return render('planner.html', 'planner')

    @app.get('/maps/<path:filename>')
    def maps(filename):
        return send_from_directory(ROOT / 'public' / 'maps', filename)

    @app.post('/processos/novo')
    def new_case_form():
        item = svc.create_case(store(), request.form)
        flash('Processo cadastrado.')
        return redirect(url_for('case_detail', case_id=item['id']), 303)

    @app.post('/processos/<case_id>/<action>')
    def case_form(case_id, action):
        tab = 'resumo'
        if action == 'andamento':
            svc.add_event(store(), case_id, request.form)
            tab = 'historico'
        elif action == 'etapa':
            svc.update_stage(store(), case_id, request.form)
        elif action == 'tarefa':
            svc.add_task(store(), case_id, request.form)
        elif action == 'documento':
            svc.add_document(store(), case_id, request.form, request.files.get('file'))
            tab = 'documentos'
        else:
            raise svc.Problem('Operação não encontrada.', 404)
        flash('Alteração salva com sucesso.')
        return redirect(url_for('case_detail', case_id=case_id, tab=tab), 303)

    @app.post('/tarefas/nova')
    def new_task_form():
        svc.add_task(store(), svc.text(request.form, 'caseId'), request.form)
        flash('Tarefa criada.')
        return redirect(url_for('tasks_page'), 303)

    @app.post('/processos/<case_id>/tarefas/<task_id>')
    def task_form(case_id, task_id):
        svc.toggle_task(store(), case_id, task_id, request.form.get('done') == 'true')
        flash('Tarefa atualizada.')
        return redirect(url_for('tasks_page') if request.form.get('board') else url_for('case_detail', case_id=case_id), 303)

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise svc.Problem('Envie um objeto JSON válido.')
        return data

    @app.get('/api/health')
    def health():
        return jsonify(ok=True, cases=len(store().all('cases')), mode='local', runtime='python')

    @app.get('/api/bootstrap')
    def api_bootstrap():
        return jsonify(svc.bootstrap(store()))

    @app.post('/api/cases')
    def api_create():
        return jsonify(svc.create_case(store(), body())), 201

    @app.route('/api/cases/<case_id>', methods=['GET', 'PATCH'])
    def api_detail(case_id):
        return jsonify(svc.detail(store(), case_id) if request.method == 'GET' else svc.update_stage(store(), case_id, body()))

    @app.post('/api/cases/<case_id>/events')
    def api_event(case_id):
        return jsonify(svc.add_event(store(), case_id, body())), 201

    @app.post('/api/cases/<case_id>/tasks')
    def api_task(case_id):
        return jsonify(svc.add_task(store(), case_id, body())), 201

    @app.patch('/api/cases/<case_id>/tasks/<task_id>')
    def api_toggle(case_id, task_id):
        return jsonify(svc.toggle_task(store(), case_id, task_id, body().get('done')))

    @app.post('/api/cases/<case_id>/geometries')
    def api_geometry(case_id):
        return jsonify(svc.save_geometry(store(), case_id, body())), 201

    @app.post('/api/cases/<case_id>/documents')
    def api_document(case_id):
        return jsonify(svc.add_document(store(), case_id, request.form, request.files.get('file'))), 201

    @app.get('/api/cases/<case_id>/documents/<doc_id>/download')
    def download(case_id, doc_id):
        svc.require_case(store(), case_id)
        document = store().get('documents', doc_id)
        if not document or document['caseId'] != case_id:
            raise svc.Problem('Documento não encontrado.', 404)
        path = (directory / 'uploads' / document['storage']).resolve()
        if path.parent != (directory / 'uploads').resolve() or not path.is_file():
            raise svc.Problem('Arquivo não encontrado na pasta de anexos.', 404)
        return send_file(path, as_attachment=True, download_name=document['name'], mimetype='application/octet-stream')

    return app
