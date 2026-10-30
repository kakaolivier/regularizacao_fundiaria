# Território · Gestão fundiária em Python

Aplicação web local para processos fundiários: imóveis, documentos, histórico, decisões, tarefas, perícias e áreas no mapa. O servidor, as regras de negócio, a persistência e a geração das páginas são escritos em **Python**. O navegador utiliza HTML/CSS e JavaScript para os controles visuais e a vetorização.

**Não requer Node.js, npm, React ou compilação.** SQLite faz parte do Python. Bibliotecas do mapa, fontes e limites municipais de Goiás estão incluídos no projeto e funcionam sem conexão externa. Ruas do OpenStreetMap são opcionais, carregadas pelo botão **Carregar ruas**.

**Quer aprender a testar sem conhecer a área jurídica?** Consulte o [manual de testes](docs/MANUAL-DE-TESTES.md). Ele explica os caminhos de edição, a seção “Valores e referências”, os termos usados nas telas e 16 exercícios com resultados esperados. Execute `gerar_material_teste.bat` para criar exemplos fictícios e `iniciar_testes.bat` para abrir uma base separada da sua pasta `data/`.

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

## Importar o novo controle pelo site

Para **CONTROLE_REGULARIZACAO.xlsx**, não é necessário executar comandos de importação:

1. Inicie o sistema e abra **Base de dados → Importar controle**.
2. Selecione o XLSX que contém a aba **BANCO_REG** e clique em **Analisar planilha**. A leitura pode levar alguns segundos: o arquivo enviado contém mais de um milhão de linhas formatadas vazias.
3. Confira os registros novos, atualizações, valores anteriores e linhas bloqueadas. Use o filtro **Para conferência** para localizar chaves repetidas ou dados insuficientes.
4. Informe o responsável e clique em **Confirmar importação**. Somente as linhas elegíveis são aplicadas; o relatório conserva as linhas bloqueadas.
5. Abra **Imóveis e trechos** para consultar e atualizar cadastro, posse/obras, perícia, acordos, registro, fase final, acompanhamento MVGA e GIS.

As 56 definições de **DICIONARIO_DADOS_REGULARIZACAO.xlsx** já estão incorporadas ao sistema; não é necessário importar esse arquivo. As outras abas do controle são referências de desenho do fluxo, sem execução de VBA ou fórmulas.

Um processo pode conter vários imóveis/subtrechos. A atualização usa a chave específica do imóvel, não apenas o CNJ. Campos vazios preservam os valores atuais. Cada mudança registra o responsável, o motivo e os valores antes/depois. Campos automáticos e campos de cadastro protegidos seguem as restrições do dicionário. Corrigir o número judicial na ficha mantém a chave permanente; uma reconciliação de identidade entre chaves diferentes exige revisão própria.

Para uma revisão do controle, repita o fluxo e confira a prévia antes de confirmar. Reenviar o mesmo arquivo já importado não reaplica dados antigos sobre edições feitas no site. Se alguém alterar a base enquanto a prévia estiver aberta, será necessário gerar uma prévia nova.

Antes de aplicar, o sistema cria uma cópia consistente do banco em `data/backups/`. Esse backup contém os registros do banco; os anexos continuam em `data/uploads/`. Para backup completo da instalação, preserve **toda a pasta `data/`**. As fontes importadas e o histórico ficam no banco; os XLSX originais não são modificados.

Datas aproximadas e textos como “LIBERADO” permanecem como texto com observação. O indicador calculado pela data do mandado não substitui a confirmação documental de liberação da obra. Veja [a análise do novo controle](docs/EVOLUCAO-DO-CONTROLE.md).

### Atualizar uma instalação existente no Windows

Pare o servidor com **Ctrl+C**, faça backup da sua pasta `data/` e baixe o código atualizado. Extraia em uma nova pasta, copie sua `data/` para ela e execute `configurar.bat` e `iniciar.bat`. A nova tabela de imóveis é criada automaticamente, preservando os processos, fontes, anexos, geometrias e tarefas anteriores. Importe o novo controle pela interface. Não apague o banco nem gere um novo `seed.json` para aplicar uma revisão desse controle.

## Importar as duas planilhas anteriores pelo Python

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
- Imóveis e subtrechos individualizados, formulários guiados pelo dicionário e histórico de campos alterados.
- Importação de BANCO_REG pelo navegador, com prévia, conferência de chaves, backup e proteção contra revisões desatualizadas.

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

O teste `tests/browser_regularizacao.py` cobre o upload, a prévia, a confirmação, a separação dos imóveis, a edição por área, o histórico e a repetição de arquivos. Os dois testes de navegador usam dados fictícios.

- `app.py`: inicialização local com Waitress, compatível com Windows.
- `territorio/__init__.py`: rotas HTML e API JSON.
- `territorio/services.py`: validações e regras de negócio.
- `territorio/store.py`: SQLite, transações e importação inicial.
- `territorio/regularizacao.py`: importação revisável e regras dos imóveis/subtrechos.
- `territorio/regularizacao_schema.json`: campos e listas derivados do dicionário, sem dados cadastrais reais.
- `territorio/templates/`: páginas geradas pelo Python/Jinja.
- `territorio/static/`: estilos e interações do navegador, sem compilação.
- `scripts/import_workbooks.py`: importador das duas planilhas.
- `tests/`: testes em Python, sempre com dados fictícios.

## Uso compartilhado

Esta é uma aplicação local sem login corporativo, vinculada somente a `127.0.0.1`. A autoria é declarada manualmente. Login, permissões, auditoria autenticada, backups operacionais e implantação para a equipe estão no [planejamento](docs/PLANEJAMENTO.md).

Em tarefas de nuvem, use o checkout existente: cada tarefa já é isolada e não requer worktree. A publicação do código no GitHub não equivale à implantação de um servidor corporativo.
