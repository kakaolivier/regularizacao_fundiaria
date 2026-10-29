"""Optional Python Playwright end-to-end check; never touches the user's data."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--python',default=sys.executable);parser.add_argument('--chromium',default=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'));args=parser.parse_args()
with tempfile.TemporaryDirectory(prefix='territorio-browser-') as directory:
    with open(Path(directory)/'server.log','w+') as log:
        server=subprocess.Popen([args.python,str(ROOT/'app.py'),'--port','3199','--data-dir',directory],cwd=ROOT,stdout=log,stderr=log)
        try:
            for attempt in range(100):
                try:
                    with urlopen('http://127.0.0.1:3199/api/health',timeout=1) as response:
                        assert json.load(response)['runtime']=='python'
                    break
                except OSError:
                    if server.poll() is not None:log.seek(0);raise RuntimeError(log.read())
                    time.sleep(.1)
            else:raise RuntimeError('Servidor não respondeu')
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':1000})
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                # App, fonts, mapping libraries and municipal layer must work with all Internet blocked.
                page.route('**/*',lambda route:route.continue_() if route.request.url.startswith('http://127.0.0.1:3199') else route.abort())
                try:
                    page.goto('http://127.0.0.1:3199');expect(page.get_by_role('heading',name='Visão geral',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Novo processo',exact=True).click()
                    dialog=page.get_by_role('dialog')
                    dialog.get_by_label('Denominação do imóvel ou obra',exact=True).fill('EEE TESTE PYTHON')
                    dialog.get_by_label('Município',exact=True).fill('Goiânia')
                    dialog.get_by_label('Proprietário / parte adversa',exact=True).fill('Pessoa fictícia')
                    dialog.get_by_label('Número oficial',exact=True).fill('7654321-98.2026.8.09.0001')
                    dialog.get_by_role('button',name='Criar processo',exact=True).click()
                    expect(page.get_by_role('heading',name='EEE TESTE PYTHON',exact=True)).to_be_visible()
                    case_id=page.url.split('/processos/')[1].split('?')[0]
                    page.get_by_role('button',name='Registrar andamento',exact=True).click()
                    dialog.get_by_label('Registrado por',exact=True).fill('Equipe de teste')
                    dialog.get_by_label('Título',exact=True).fill('Parecer técnico recebido')
                    dialog.get_by_label('Descrição',exact=True).fill('Conferência concluída. Encaminhar ao jurídico.')
                    dialog.get_by_label('Tipo de registro',exact=True).select_option('decision')
                    dialog.get_by_role('button',name='Salvar andamento',exact=True).click()
                    expect(page.get_by_role('heading',name='Parecer técnico recebido',exact=True)).to_be_visible()
                    page.get_by_role('link',name='Resumo',exact=True).click()
                    page.get_by_role('button',name='Atualizar etapa',exact=True).click()
                    dialog.get_by_label('Etapa atual',exact=True).fill('Análise jurídica')
                    dialog.get_by_label('Responsável pelo registro',exact=True).fill('Equipe de teste')
                    dialog.get_by_role('button',name='Salvar alteração',exact=True).click()
                    expect(page.get_by_text('Análise jurídica',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Criar tarefa',exact=True).click()
                    dialog.get_by_label('O que precisa ser feito?',exact=True).fill('Conferir matrícula atualizada')
                    dialog.get_by_label('Responsável',exact=True).fill('Equipe técnica')
                    dialog.get_by_label('Prazo',exact=True).fill('2026-12-31')
                    dialog.get_by_role('button',name='Criar tarefa',exact=True).click()
                    page.get_by_role('button',name='Concluir tarefa Conferir matrícula atualizada',exact=True).click()
                    expect(page.get_by_role('button',name='Reabrir tarefa Conferir matrícula atualizada',exact=True)).to_be_visible()
                    page.get_by_role('link',name='Documentos 0',exact=True).click()
                    page.get_by_role('button',name='Anexar documento',exact=True).click()
                    dialog.locator('input[type=file]').set_input_files({'name':'matrícula-teste.txt','mimeType':'text/plain','buffer':'Documento de teste Python.'.encode()})
                    dialog.get_by_label('Categoria',exact=True).select_option('Parecer jurídico')
                    dialog.get_by_role('button',name='Anexar documento',exact=True).click()
                    expect(page.get_by_role('heading',name='matrícula-teste.txt',exact=True)).to_be_visible()
                    with page.expect_download() as download:
                        page.get_by_role('link',name='Baixar arquivo',exact=True).click()
                    assert Path(download.value.path()).read_text()=='Documento de teste Python.'
                    page.get_by_role('link',name='Mapa e áreas 0',exact=True).click()
                    expect(page.get_by_role('button',name='Desenhar área',exact=True)).to_be_visible()
                    feature={'type':'Feature','properties':{},'geometry':{'type':'Polygon','coordinates':[[[-49.25,-16.82],[-49.249,-16.82],[-49.249,-16.819],[-49.25,-16.819],[-49.25,-16.82]]]}}
                    page.locator('[data-geo-file]').set_input_files({'name':'faixa.geojson','mimeType':'application/geo+json','buffer':json.dumps(feature).encode()})
                    page.get_by_label('Nome da área',exact=True).fill('Faixa de servidão teste')
                    page.get_by_role('button',name='Salvar área',exact=True).click()
                    expect(page.get_by_text('Faixa de servidão teste',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Editar Faixa de servidão teste',exact=True).click()
                    page.get_by_label('Nome da área',exact=True).fill('Faixa de servidão revisada')
                    page.get_by_role('button',name='Salvar área',exact=True).click()
                    expect(page.get_by_text('Faixa de servidão revisada',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Desenhar área',exact=True).click()
                    box=page.locator('.map-canvas').bounding_box()
                    for x,y in [(.23,.32),(.38,.32),(.38,.48),(.23,.48),(.23,.32)]:page.mouse.click(box['x']+box['width']*x,box['y']+box['height']*y)
                    page.get_by_label('Nome da área',exact=True).fill('Limite desenhado')
                    page.get_by_label('Tipo',exact=True).select_option('Limite do imóvel')
                    page.get_by_role('button',name='Salvar área',exact=True).click()
                    expect(page.locator('[data-geometries]').get_by_text('Limite desenhado',exact=True)).to_be_visible()
                    page.reload();expect(page.locator('[data-geometries]').get_by_text('Limite desenhado',exact=True)).to_be_visible()
                    actual=page.request.get(f'http://127.0.0.1:3199/api/cases/{case_id}').json()
                    assert len(actual['documents'])==1 and actual['tasks'][0]['done'] and len(actual['geometries'])==2
                    assert next(g for g in actual['geometries'] if g['name']=='Faixa de servidão revisada')['version']==2
                    page.get_by_role('link',name='Todos os processos',exact=False).click()
                    page.get_by_label('Pesquisar nesta lista',exact=True).fill('inexistente')
                    page.locator('.list-toolbar').get_by_role('button',name='Buscar',exact=True).click()
                    expect(page.get_by_role('heading',name='Nenhum processo encontrado',exact=True)).to_be_visible()
                    page.get_by_role('link',name='Limpar filtros',exact=True).click()
                    with page.expect_download() as download:page.get_by_role('link',name='Exportar lista',exact=True).click()
                    assert 'EEE TESTE PYTHON' in Path(download.value.path()).read_text(encoding='utf-8-sig')
                    page.set_viewport_size({'width':390,'height':844})
                    page.get_by_role('button',name='Abrir menu',exact=True).click()
                    page.get_by_role('link',name='Visão geral',exact=True).click()
                    expect(page.get_by_role('heading',name='Visão geral',exact=True)).to_be_visible()
                    assert page.evaluate('document.body.scrollWidth <= innerWidth'),'Mobile viewport overflow'
                    page.get_by_role('button',name='Novo processo',exact=True).click();expect(dialog).to_be_visible();page.keyboard.press('Escape');expect(dialog).not_to_be_visible()
                    assert not errors,errors
                    Path('test-results').mkdir(exist_ok=True)
                    page.screenshot(path='test-results/python-mobile.png',full_page=True)
                    page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path='test-results/python-overview.png',full_page=True)
                    print('PASS: Python server + desktop/mobile UI; create, history, stage, tasks, documents/download, GeoJSON, versions, polygon drawing, reload, CSV, filters, and no external network.')
                except BaseException:
                    Path('test-results').mkdir(exist_ok=True);page.screenshot(path='test-results/python-failure.png',full_page=True)
                    raise
                finally:browser.close()
        finally:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()
