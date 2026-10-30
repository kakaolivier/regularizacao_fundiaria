"""End-to-end import and keyed-record editing with synthetic data only."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from openpyxl import Workbook
from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--chromium', default=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    base = 'http://127.0.0.1:3201'
    with tempfile.TemporaryDirectory(prefix='territorio-reg-browser-') as directory:
        temp = Path(directory)
        book = Workbook()
        sheet = book.active
        sheet.title = 'BANCO_REG'
        fields = json.loads((root / 'territorio/regularizacao_schema.json').read_text())['fields']
        for field in fields:
            sheet[field['column'] + '3'] = field['title']
        for row, section in enumerate(['Trecho 1', 'Trecho 2', 'Duplicado', 'Duplicado'], 4):
            values = {'D': row-3, 'E': 'APARECIDA DE GOIÂNIA', 'F': 'EEE Jardim Norte', 'G': section,
                      'H': 'Pessoa fictícia', 'J': 'JUDICIAL', 'L': '1234567-89.2025.8.09.0001',
                      'N': 'REALIZAÇÃO DE PERÍCIA', 'AE': 'PERITO NOMEADO', 'BD': 'Equipe técnica', 'BC': 'LIBERADO'}
            values['C'] = '|'.join(values[c] for c in ('L', 'F', 'G'))
            for col, value in values.items():
                sheet[f'{col}{row}'] = value
        path = temp / 'controle-teste.xlsx'
        book.save(path)
        book.close()
        with (temp / 'server.log').open('w+') as log:
            server = subprocess.Popen([str(Path(args.python).absolute()), 'app.py', '--port', '3201', '--data-dir', str(temp/'data')], cwd=root, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    try:
                        with urlopen(base + '/api/health', timeout=1) as response:
                            assert json.load(response)['ok']
                        break
                    except OSError:
                        if server.poll() is not None:
                            log.seek(0)
                            raise RuntimeError(log.read())
                        time.sleep(.1)
                else:
                    raise RuntimeError('Servidor não respondeu')
                with sync_playwright() as p:
                    browser = p.chromium.launch(executable_path=args.chromium, headless=True, args=['--no-sandbox'])
                    page = browser.new_page(viewport={'width':1440, 'height':1000})
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
                    try:
                        page.goto(base + '/fontes')
                        page.get_by_role('link', name='Importar controle', exact=True).click()
                        page.get_by_label('Planilha de controle').set_input_files(path)
                        page.get_by_role('button', name='Analisar planilha', exact=True).click()
                        expect(page.get_by_role('heading', name='Conferir importação', exact=True)).to_be_visible()
                        expect(page.locator('.import-row')).to_have_count(4)
                        assert page.request.get(base + '/api/health').json()['cases'] == 0
                        Path('test-results').mkdir(exist_ok=True)
                        page.screenshot(path='test-results/regularizacao-preview.png', full_page=True)
                        page.get_by_label('Filtrar resultado').select_option('blocked')
                        page.get_by_role('button', name='Filtrar', exact=True).click()
                        expect(page.locator('.import-row')).to_have_count(2)
                        page.get_by_label('Responsável pela importação').fill('Equipe de teste')
                        page.get_by_role('button', name='Confirmar importação', exact=True).click()
                        expect(page.get_by_role('heading', name='Uma base com contexto', exact=True)).to_be_visible()
                        assert page.request.get(base + '/api/health').json()['cases'] == 1
                        page.get_by_role('link', name='Imóveis e trechos', exact=True).click()
                        expect(page.locator('.record-table tbody tr')).to_have_count(2)
                        page.get_by_role('link', name='EEE Jardim Norte', exact=True).first.click()
                        url = page.url
                        page.get_by_role('navigation', name='Áreas do acompanhamento').get_by_role('link', name='Perícia', exact=True).click()
                        page.get_by_label('Fase pericial atual', exact=True).select_option('LAUDO APRESENTADO')
                        page.get_by_label('Registrado por', exact=True).fill('Equipe de teste')
                        page.get_by_label('Motivo / referência documental', exact=True).fill('Laudo juntado em documento de teste')
                        page.get_by_role('button', name='Salvar Perícia', exact=True).click()
                        expect(page.locator('.current-value').filter(has_text='LAUDO APRESENTADO')).to_be_visible()
                        page.locator('.event-changes summary').first.click()
                        expect(page.locator('.change-table').get_by_text('PERITO NOMEADO', exact=True)).to_be_visible()
                        cases = page.request.get(base + '/api/bootstrap').json()['cases']
                        records = page.request.get(base + '/api/cases/' + cases[0]['id']).json()['records']
                        assert len(records) == 2
                        assert records[0]['values']['AE'] == 'LAUDO APRESENTADO'
                        assert records[1]['values']['AE'] == 'PERITO NOMEADO'
                        page.screenshot(path='test-results/regularizacao-record.png', full_page=True)
                        page.set_viewport_size({'width':390,'height':844})
                        page.goto(url + '?group=REGISTRO')
                        expect(page.get_by_role('button', name='Salvar Registro', exact=True)).to_be_visible()
                        assert page.evaluate('document.body.scrollWidth <= innerWidth'), 'Mobile overflow'
                        page.screenshot(path='test-results/regularizacao-mobile.png', full_page=True)
                        page.goto(base + '/importar')
                        page.get_by_label('Planilha de controle').set_input_files(path)
                        page.get_by_role('button', name='Analisar planilha', exact=True).click()
                        expect(page.get_by_text('Este arquivo já foi importado. A repetição não substitui alterações feitas no site.', exact=True)).to_be_visible()
                        expect(page.get_by_role('button', name='Confirmar importação', exact=True)).to_have_count(0)
                        assert not errors, errors
                        print('PASS: import preview/confirmation, duplicate quarantine, keyed edits/history, sibling isolation, repeated-file protection, desktop/mobile, offline assets.')
                    except BaseException:
                        Path('test-results').mkdir(exist_ok=True)
                        page.screenshot(path='test-results/regularizacao-failure.png', full_page=True)
                        raise
                    finally:
                        browser.close()
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == '__main__':
    main()
