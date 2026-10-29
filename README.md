# Território · Gestão fundiária em Python

Aplicação web local para processos fundiários: imóveis, documentos, histórico, decisões, tarefas, perícias e áreas no mapa. O servidor, as regras de negócio, a persistência e a geração das páginas são escritos em **Python**. O navegador utiliza HTML/CSS e JavaScript para os controles visuais e a vetorização.

**Não requer Node.js, npm, React ou compilação.** SQLite faz parte do Python. Bibliotecas do mapa, fontes e limites municipais de Goiás estão incluídos no projeto e funcionam sem conexão externa. Ruas do OpenStreetMap são opcionais, carregadas pelo botão **Carregar ruas**.

## Executar no Windows

Requer **Python 3.10 ou superior**, preferencialmente **Python 3.12 de 64 bits**. Baixe o projeto pelo GitHub em **Code → Download ZIP**, extraia e mantenha todos os arquivos na mesma pasta.

1. Execute **`configurar.bat`** uma vez. Ele cria `.venv` dentro da pasta do projeto e instala as dependências Python.
2. Execute **`iniciar.bat`**. O servidor inicia e abre o navegador.
3. Mantenha a janela do terminal aberta enquanto usa o sistema. Para encerrar, pressione **Ctrl+C**.

A instalação inicial requer acesso aos pacotes Python. A instalação ocorre dentro da pasta do projeto, sem precisar instalar um banco de dados ou modificar a instalação global do Python.

Se preferir utilizar o terminal (PowerShell ou Prompt de Comando), na pasta que contém `app.py`:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe app.py --open
```

Se o comando `py` não estiver disponível, use `python -m venv .venv`. Não é necessário ativar a venv com scripts do PowerShell.

O endereço local é `http://localhost:3000`, no navegador **do mesmo computador**. Para outra porta:

```powershell
.\.venv\Scripts\python.exe app.py --port 3001 --open
```

Caso a rede corporativa bloqueie a instalação, encaminhe `requirements.txt` à TI para aprovação/configuração do repositório de pacotes, proxy ou certificado corporativo. A aplicação preserva a verificação TLS. Depois de instaladas as dependências, o uso local dispensa Internet, com exceção do mapa de ruas opcional.

## Executar no Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
.venv/bin/python app.py --open
```

Também é possível usar `bash scripts/setup.sh` para instalar e executar os testes, seguido de `.venv/bin/python app.py`.

## Dados e migração da versão anterior

O GitHub contém o código, sem os dados reais das planilhas. A primeira abertura mostra uma base vazia; você pode cadastrar um processo ou importar suas planilhas.

A versão Python mantém o formato SQLite e os identificadores usados pela versão Node. Para aproveitar uma instalação anterior:

1. Pare o servidor antigo e faça uma cópia de segurança de **toda a pasta `data/`**.
2. Use a pasta `data/` completa na versão Python, incluindo `territorio.sqlite` e `uploads/`. Não copie apenas o banco enquanto o servidor antigo estiver em execução: dados podem estar no WAL.
3. Inicie a aplicação Python. Ela abre os mesmos cadastros, fontes, documentos, tarefas, eventos e geometrias. Não reinicializa nem reaplica uma importação concluída.

A pasta `data/` guarda os registros e anexos; preserve-a entre execuções. Para usar outro diretório, execute `python app.py --data-dir "C:\caminho\minha-base"`. A aplicação cria `data/.session-key` para proteger os formulários locais; essa chave também fica fora do Git.

**Validação:** a compatibilidade foi testada com um banco no esquema da versão Node, incluindo vínculos, tarefas e anexos. Não foi executada uma migração no computador corporativo do usuário.

## Importar as planilhas

As dependências da importação já estão em `requirements.txt`. Pare o servidor e mantenha as planilhas fora do repositório. No Windows:

```powershell
.\.venv\Scripts\python.exe scripts/import_workbooks.py "C:\caminho\Planilha BRK GO - PERÍCIAS-REV01.xlsx" "C:\caminho\Planilha de Acomp. e STATUS APRESENTAÇÃO - Rev 112.xlsx" --output data/seed.json
.\.venv\Scripts\python.exe app.py --open
```

No Linux/macOS, use `.venv/bin/python` no lugar de `.\.venv\Scripts\python.exe`. Substitua os caminhos pelos arquivos originais.

A inicialização carrega `seed.json` somente se ainda não houver uma importação concluída. **Alterar `seed.json` não atualiza um banco já importado.** Não apague um banco com trabalho realizado para repetir a importação; revisões precisam de reconciliação. Arquivos originais não são modificados. Valores “N/A”, fontes, trechos e datas são preservados sem inventar coordenadas.

Consulte [a análise das planilhas](docs/ANALISE-DAS-PLANILHAS.md).

## Recursos preservados

- Painel, busca por imóvel/número/proprietário/matrícula/referência GIS, filtros, paginação e CSV.
- Cadastro de processos e referências de imóveis/trechos.
- Histórico com andamentos, decisões, contatos e marcos estruturados das planilhas.
- Documentos por processo ou área, downloads, SHA-256 e versões anteriores preservadas.
- Tarefas com responsável, prazo, conclusão e reabertura.
- Desenho e edição de polígonos, GeoJSON, áreas de interesse e limites dos imóveis, versões de geometrias.
- Perícias, valores por natureza e origem, campos originais e sinalização de divergências.
- Planejamento da evolução do produto.

A área geográfica é estimativa de apoio à gestão. Anexe o levantamento técnico aprovado. A validação de polígonos é feita em Python com Shapely, incluindo fechamento, limites de coordenadas, cruzamentos, furos e sobreposições em multipolígonos. GeoJSON: WGS84, um Polygon/MultiPolygon por arquivo, até 500 KB. Documentos: PDF, PNG, JPG, DOCX, XLSX ou TXT, até 25 MB.

A camada municipal tem atribuição em [public/maps/README.md](public/maps/README.md). As bibliotecas de navegador e licenças ficam em `territorio/static/vendor/`, com versões e hashes registrados no manifesto. Não há download de bibliotecas durante a execução.

## Testes e estrutura

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Com o servidor em execução, a verificação de prontidão usa somente a biblioteca padrão:

```powershell
.\.venv\Scripts\python.exe scripts/check_ready.py
```

O teste opcional `tests/browser.py` usa a API Python do Playwright e um Chromium de testes, com servidor e base temporários. Foi executado em Linux com toda a rede externa bloqueada, incluindo desenho real de polígonos e uso em viewport móvel. Não é uma dependência para utilizar o sistema.

- `app.py`: inicialização local com Waitress, compatível com Windows.
- `territorio/__init__.py`: rotas HTML e API JSON.
- `territorio/services.py`: validações e regras de negócio.
- `territorio/store.py`: SQLite, transações e importação inicial.
- `territorio/templates/`: páginas geradas pelo Python/Jinja.
- `territorio/static/`: estilos e interações do navegador, sem compilação.
- `scripts/import_workbooks.py`: importador das duas planilhas.
- `tests/`: testes em Python, sempre com dados fictícios.

## Uso compartilhado

Esta é uma aplicação local sem login corporativo, vinculada somente a `127.0.0.1`. A autoria é declarada manualmente. Login, permissões, auditoria autenticada, backups operacionais e implantação para a equipe estão no [planejamento](docs/PLANEJAMENTO.md).

Em tarefas de nuvem, use o checkout existente: cada tarefa já é isolada e não requer worktree. A publicação do código no GitHub não equivale à implantação de um servidor corporativo.
