# Validação da entrega local

Verificado em 15/10/2026, neste ambiente. Não equivale a validação da publicação ou de uma tarefa nova.

- Instalação reproduzida pelo script `scripts/setup.sh` com `npm ci` e o lockfile.
- Compilação TypeScript/Vite concluída.
- Quatro suítes de testes da API aprovadas: ciclo do processo, tarefas e persistência; geometrias/versões/isolamento; upload/download/versionamento; importação idempotente e proveniência.
- Navegador Chromium em desktop e viewport móvel: criação, etapa, andamento, tarefa, documento/download, GeoJSON, edição de geometria, desenho por cliques, persistência após recarga, filtros, CSV e fechamento do modal por teclado.
- Dados fictícios dos testes permanecem isolados da base real.
- Checagem independente: 956 IDs de origem distintos; cada origem vinculada a um cadastro; 489 agrupamentos conservadores; 468 linhas de ajuizados e 68 linhas periciais contabilizadas.
- SHA-256 dos arquivos originais corresponde ao registrado na importação; fontes não modificadas.
- API, interface compilada, assets, ficha e mapa municipal local validados por `scripts/check-ready.mjs`.
- Não houve erro JavaScript no navegador ao abrir o painel e uma ficha com dados importados.

O mapa de ruas OpenStreetMap retornou 403 no proxy. A camada municipal local foi carregada e o desenho/importação funcionaram com o serviço externo bloqueado. O domínio foi incluído no rascunho de rede, com aplicação/publicação pendentes de revisão nas configurações.

Sem login corporativo nesta versão. A base é local e não foi publicada. As limitações cadastrais e financeiras estão documentadas em `ANALISE-DAS-PLANILHAS.md`.
