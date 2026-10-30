# Validação da versão Python

Verificado em 30/10/2026 no ambiente Linux, com Python 3.12 e Chromium. Os testes usam dados fictícios em diretórios temporários.

- Instalação pelo `scripts/setup.sh`: ambiente virtual, dependências de `requirements.txt` e 14 testes `unittest`.
- Cadastro, prevenção de duplicidade por CNJ completo, histórico, mudança de etapa, tarefas e persistência após reabrir o banco.
- Geometrias: área estimada, Polygon/MultiPolygon, furos, versões, conflito de edição, isolamento entre processos e rejeição de coordenadas inválidas, cruzamentos e sobreposições.
- Anexos: bytes preservados no download, nomes com acentos, versões, vínculo com processo/área e rejeição de arquivos inválidos sem deixar arquivos órfãos.
- Compatibilidade com banco criado no esquema SQLite da versão Node, incluindo ordem original das colunas, registros vinculados e arquivo de anexo existente. Alterar a etapa conserva os vínculos.
- Importação inicial idempotente, proveniência, narrativas sem data inventada, busca em fontes secundárias, sinalização de divergências e rollback em falha.
- Importador das duas planilhas validado com arquivos sintéticos: agrupamento por CNJ completo, separação dos identificadores incompletos, “N/A” distinto de zero, datas, linhas com fórmulas sem dados e preservação dos arquivos originais.
- Interface HTML, CSRF nos formulários, bloqueio de origem externa, escape de conteúdo e exportação CSV com proteção contra fórmulas.
- Navegador em desktop (1440 × 1000) e viewport móvel (390 × 844): cadastro, andamento, etapa, tarefa, anexo/download, importação GeoJSON, edição de versão, desenho por cliques, persistência após recarga, busca, CSV e fechamento de formulário por teclado. Sem erros JavaScript.
- O teste de navegador bloqueia todas as requisições externas: fontes, bibliotecas e mapa municipal funcionam localmente. Ruas do OpenStreetMap são opcionais e não são necessárias para esses fluxos.
- Verificação de prontidão com `scripts/check_ready.py`: servidor Python, interface, bibliotecas locais, API e camada com 246 municípios.
- Dependências binárias disponíveis para CPython 3.12 no Windows de 64 bits, verificadas por download com `pip --platform win_amd64`. Os arquivos `.bat` foram preparados para Windows; não foram executados em um sistema Windows nesta entrega.

## Reproduzir

```bash
bash scripts/setup.sh
python tests/browser.py --python .venv/bin/python --chromium /usr/bin/chromium
python tests/browser_regularizacao.py --python .venv/bin/python --chromium /usr/bin/chromium
```

Os comandos de navegador requerem o pacote Python `playwright` no interpretador que executa o teste, além do Chromium indicado. Não são dependências da aplicação. Os testes iniciam e encerram servidores próprios nas portas 3199 e 3201. Capturas ficam em `test-results/`, ignorado pelo Git.

Com a aplicação iniciada por `.venv/bin/python app.py`, execute:

```bash
.venv/bin/python scripts/check_ready.py
```

O novo CONTROLE_REGULARIZACAO.xlsx foi lido e importado em uma base temporária de validação: 482 linhas candidatas, 466 imóveis elegíveis, 359 dossiês e 16 linhas bloqueadas. A operação levou cerca de 17 segundos neste ambiente; o tempo varia por computador. As páginas principais e uma ficha de imóvel responderam corretamente com essa base. A base temporária foi removida ao terminar; o download do GitHub continua sem dados reais.

O dicionário foi incorporado como metadados de 56 campos. Os novos testes cobrem datas seriais, linhas formatadas vazias, chaves repetidas, identificação incompleta, fórmulas sem cache, registros separados sob o mesmo CNJ, preservação de anexos/tarefas, backups, revisões, campos protegidos, conflito de versões, rollback, CSRF e escape HTML.

`tests/browser_regularizacao.py` validou upload, prévia sem gravação, filtro de linhas bloqueadas, confirmação, edição por área, histórico antes/depois, preservação do trecho vizinho, proteção contra repetição de arquivo e interface móvel, com a rede externa bloqueada. O teste original de mapa, documentos e tarefas também passou.

Os números históricos das demais análises não representam uma base pré-carregada no download. Para usar os dados, siga a importação ou migração de `data/` descrita no README.

Não houve validação no computador corporativo, de instalação multiusuário ou de restauração em uma nova tarefa de nuvem. Login corporativo e autorização por perfil continuam no planejamento.
