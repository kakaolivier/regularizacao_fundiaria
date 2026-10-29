import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook

SPEC=importlib.util.spec_from_file_location('importer',Path(__file__).resolve().parents[1]/'scripts/import_workbooks.py')
importer=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(importer)


class ImporterTests(unittest.TestCase):
    def test_layout_cnj_dates_missing_title_and_no_invented_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);a=Workbook();s=a.active;s.title='Processos ajuizados'
            for column,label in {'E':'MUNICÍPIO','F':'DENOMINAÇÃO','H':'PROPRIETÁRIO','I':'PROCESSO','T':'PETIÇÃO','V':'VALOR','AN':'SITUAÇÃO'}.items():s[f'{column}5']=label
            for row,number in [(6,'1234567-89.2025.8.09.0001'),(7,'incompleto')]:
                s[f'E{row}']='Goiânia';s[f'F{row}']='N/A';s[f'H{row}']='Pessoa fictícia';s[f'I{row}']=number;s[f'V{row}']='N/A';s[f'AN{row}']='Relato sem data'
            s['T6']=datetime(2025,1,3);s['D1000']='=ROW()';a.save(root/'acompanhamento.xlsx')
            b=Workbook();t=b.active;t.title='LAUDOS APRESENTADOS'
            for column,label in {'B':'Município','C':'Imóvel','E':'Processo','F':'Parte','G':'Depósito','S':'Fase'}.items():t[f'{column}11']=label
            for col,value in {'B':'Goiânia','C':'Área fictícia','E':'1234567-89.2025.8.09.0001','F':'Pessoa fictícia','G':100.25,'S':'Laudo apresentado'}.items():t[f'{col}12']=value
            b.save(root/'pericias.xlsx')
            original=(root/'acompanhamento.xlsx').read_bytes()
            importer.run([root/'acompanhamento.xlsx',root/'pericias.xlsx'],root/'seed.json')
            result=json.loads((root/'seed.json').read_text(encoding='utf-8'))
            self.assertEqual(len(result['cases']),2);self.assertEqual(len(result['sources']),3)
            self.assertEqual(result['summary']['linkedBoth'],1);self.assertFalse(result['summary']['hasCoordinates'])
            self.assertEqual(result['sources'][0]['title'],'Imóvel não informado')
            self.assertEqual(result['sources'][0]['financial'],{})
            self.assertEqual(result['sources'][0]['events'],[{'date':'2025-01-03','title':'Petição inicial'}])
            self.assertEqual((root/'acompanhamento.xlsx').read_bytes(),original)


if __name__=='__main__':unittest.main()
