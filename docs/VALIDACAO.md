# Validação da versão Python

Verificado em 29/10/2026 no ambiente Linux, com Python 3.12 e Chromium. Os testes usam dados fictícios em diretórios temporários.

- Instalação pelo `scripts/setup.sh`: ambiente virtual, dependências de `requirements.txt` e sete testes `unittest`.
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
```

O segundo comando requer o pacote Python `playwright` no interpretador que executa o teste, além do Chromium indicado. Não são dependências da aplicação. O teste inicia e encerra seu próprio servidor na porta 3199. Capturas ficam em `test-results/`, ignorado pelo Git.

Com a aplicação iniciada por `.venv/bin/python app.py`, execute:

```bash
.venv/bin/python scripts/check_ready.py
```

Esta entrega não reimportou as planilhas reais: elas não estão no checkout atual nem no GitHub. Os números históricos da análise das planilhas não representam uma base pré-carregada no download. Para usar os dados, siga a importação ou a migração de `data/` descrita no README.

Não houve validação no computador corporativo, de instalação multiusuário ou de restauração em uma nova tarefa de nuvem. Login corporativo e autorização por perfil continuam no planejamento.
