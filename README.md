# Território · Gestão fundiária

Primeira versão funcional construída a partir das duas planilhas fornecidas. Reúne cadastro, documentos, histórico, perícias, tarefas e geometrias em uma aplicação web local.

## Baixar e executar no seu computador

Requer **Node.js 24 ou superior**, disponível em https://nodejs.org. O banco SQLite já vem no Node; Python é necessário somente para importar as planilhas.

Baixe o projeto em **Code → Download ZIP**, extraia e abra o terminal na pasta que contém `package.json`. Se utilizar Git:

```bash
git clone https://github.com/kakaolivier/regularizacao_fundiaria.git
cd regularizacao_fundiaria
```

Na pasta do projeto, execute:

```bash
npm ci
npm run dev
```

Com o terminal aberto, acesse a porta **3000** da sua própria máquina no navegador: `http://localhost:3000`. Para encerrar, pressione **Ctrl+C**. Nas próximas execuções, basta `npm run dev`.

No Windows, se o PowerShell bloquear `npm`, use `npm.cmd ci` e `npm.cmd run dev`. Para executar a versão compilada, use `npm run build` seguido de `npm start`; esses comandos também funcionam no Windows.

**O código no GitHub inicia sem os dados reais das planilhas.** Você pode criar um processo pela interface ou seguir as instruções de importação abaixo. A base real, os documentos e os backups ficam na pasta local `data/`, ignorada pelo Git.

O servidor escuta em **127.0.0.1** e serve a interface e a API na mesma origem. `PORT` altera a porta. A versão atual é local e usa autoria declarada manualmente. Acesso compartilhado depende de autenticação e autorização antes da exposição em outras interfaces de rede.

Em Linux/macOS/Git Bash, o script `bash scripts/setup.sh` instala com o lockfile, compila e executa os testes da API. O cache padrão é `.npm-cache/`; `npm_config_cache` permite escolher outro diretório.

No ambiente de nuvem original, o projeto está em `/workspace/regularizacao_fundiaria`. Cada tarefa já é isolada: utilize o checkout existente e não crie worktrees durante a configuração.

## O que funciona

- Painel, busca por número, imóvel, proprietário, matrícula e referência GIS, filtros e exportação CSV.
- Cadastro de processos; referências de imóveis e trechos preservadas por fonte.
- Histórico com andamentos, contatos, decisões, mudanças de etapa e marcos estruturados das planilhas.
- Documentos por processo ou área, download, identificação SHA-256 e versões anteriores preservadas.
- Tarefas com responsável, prazo, conclusão e reabertura.
- Mapa Leaflet: desenho e edição de polígonos, importação/exportação GeoJSON, distinção entre limite do imóvel e área de interesse, histórico de versões.
- Visão pericial, valores por referência e acesso a todos os campos originais.
- Página de qualidade da base e planejamento das próximas etapas.

Os arquivos mencionados nas planilhas não foram anexados automaticamente: as planilhas não contêm o acervo dos processos. A área geográfica exibida é estimativa geodésica; o levantamento técnico aprovado deve ser anexado como documento.

## Dados locais e importação

`data/` é ignorado pelo Git. Contém `seed.json`, `territorio.sqlite`, anexos e backups. Os dados reais permanecem na máquina em que foram importados; o código e os testes não incorporam nomes ou números reais de processos. O snapshot do ambiente pode reter `data/`, mas um clone novo do código não traz os dados reais. Não copie a base para um repositório público.

Na primeira inicialização, se houver `data/seed.json` e o banco ainda não tiver metadados de importação, o servidor importa a base em uma transação. Reiniciar **não** duplica os registros. Alterar `seed.json` **não** sobrescreve um banco já inicializado.

A importação inicial usa Python 3 e `openpyxl==3.1.5`, sem modificar as planilhas. Mantenha os arquivos XLSX em uma pasta fora do código. Pare o servidor antes de preparar a importação inicial.

**Windows (PowerShell):**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-import.txt
.\.venv\Scripts\python.exe scripts/import_workbooks.py "C:\caminho\Planilha BRK GO - PERÍCIAS-REV01.xlsx" "C:\caminho\Planilha de Acomp. e STATUS APRESENTAÇÃO - Rev 112.xlsx" --output data/seed.json
npm.cmd run dev
```

**Linux/macOS:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-import.txt
.venv/bin/python scripts/import_workbooks.py \
  '/caminho/Planilha BRK GO - PERÍCIAS-REV01.xlsx' \
  '/caminho/Planilha de Acomp. e STATUS APRESENTAÇÃO - Rev 112.xlsx' \
  --output data/seed.json
npm run dev
```

Substitua os caminhos pelos locais onde você salvou os dois arquivos. Na inicialização seguinte, a base é carregada se ainda não houve uma importação. Preserve `data/` para manter seus cadastros e anexos entre execuções.

Não remova um banco já utilizado para repetir a importação. Revisões futuras precisam de reconciliação; essa atualização recorrente está no planejamento. `DATA_DIR` permite apontar para outra base isolada.

Consulte [a análise das planilhas](docs/ANALISE-DAS-PLANILHAS.md) e [o planejamento](docs/PLANEJAMENTO.md).

## Mapas

As planilhas não fornecem coordenadas. Nenhum polígono de imóvel foi inventado. A camada municipal local contém os limites de Goiás do projeto Geodata BR, cuja fonte declarada é o IBGE e a licença é CC0; veja [a atribuição cartográfica](public/maps/README.md). Essa camada representa municípios, não terrenos.

O mapa de ruas usa `tile.openstreetmap.org`. Na máquina de desenvolvimento, o proxy respondeu 403 para esse domínio. O site funciona com a camada municipal local quando o mapa de ruas está indisponível. A liberação desse domínio nas configurações permite tentar carregar ruas; não foi confirmada nesta instância. Fontes tipográficas são distribuídas localmente, sem depender do Google Fonts.

GeoJSON deve usar longitude/latitude WGS84 (EPSG:4326), um Polygon ou MultiPolygon por arquivo, até 500 KB. O servidor verifica coordenadas, fechamento, área positiva e cruzamento de linhas. Arquivos de documentos aceitos: PDF, PNG, JPG, DOCX, XLSX e TXT, até 25 MB. Downloads usam `Content-Disposition: attachment`.

## Verificações

```bash
npm run build
npm test
npm run test:ui
```

O teste de interface utiliza Chromium instalado em `/usr/bin/chromium`; ajuste `CHROMIUM_PATH` se necessário. Ele sobe um servidor na porta 3199 com banco temporário e dados fictícios, testa o fluxo completo e remove apenas seus próprios arquivos. Não altera a base real.

API: `/api/health` verifica conexão e quantidade de cadastros; `/api/bootstrap` retorna o estado inicial; `/api/cases/:id` reúne a ficha. O banco usa SQLite com WAL. Para backup consistente, use a API de backup do SQLite ou pare o servidor antes de copiar **todo** `data/` (banco e anexos). Copiar apenas o arquivo `.sqlite` de um processo ativo pode perder alterações do WAL.

## Antes do uso compartilhado

Implementar login corporativo e autorização por perfil, autoria autenticada, armazenamento privado, backup/restauração operacional e validação dos fluxos com as equipes técnica, fundiária e jurídica. A versão local não equivale a uma implantação corporativa nem a uma publicação concluída.
