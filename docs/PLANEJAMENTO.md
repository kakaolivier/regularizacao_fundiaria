# Plano do produto

## Entrega atual

Aplicação local de gestão fundiária com mapa municipal, processo detalhado, campos originais, referências de imóveis/trechos, histórico, documentos versionados, tarefas, controle pericial, geometrias versionadas e exportações CSV/GeoJSON. Servidor e regras em Python, páginas Jinja e SQLite compatível com a versão anterior. Instalação e abertura no Windows pelos arquivos `configurar.bat` e `iniciar.bat`, sem Node.js ou compilação.

O download do GitHub começa sem os dados reais. As planilhas podem ser importadas localmente ou uma pasta `data/` anterior pode ser reaproveitada após backup. Banco e anexos são ignorados pelo Git; testes usam bases temporárias fictícias.

A evolução de 30/10/2026 acrescenta registros por imóvel/subtrecho, 56 campos guiados pelo dicionário, oito áreas de atualização, histórico antes/depois e importação revisável de BANCO_REG pelo site. Chaves repetidas ficam para conferência. Veja [a análise das mudanças e pendências](EVOLUCAO-DO-CONTROLE.md).

## Primeiro piloto com a equipe

| Decisão | Quem pode esclarecer | Resultado esperado |
|---|---|---|
| Etapas por modalidade (compra, servidão, desapropriação, extrajudicial) | Fundiário e jurídico | Fluxos com responsáveis, condições de avanço e exceções |
| Limite do imóvel versus parcela de intervenção | Topografia e projetos | Padrão de geometria, referência técnica e documentação |
| Correspondência dos números incompletos e trechos | Controle de processos | Cadastro reconciliado sem perda de fontes |
| Data-base, cálculos e natureza dos valores | Jurídico e financeiro | Regras financeiras aprovadas, sem somas duplicadas |
| Quem pode visualizar, editar, aprovar e encerrar | Gestores e TI | Matriz de acesso e autoria autenticada |
| Integração com número oficial / protocolo | TI e protocolo | Identificador estável e prevenção de duplicidade |

Sugestão de piloto: selecionar um caso judicial em perícia, um caso extrajudicial e um caso com vários trechos. Conferir todas as referências com a equipe, cadastrar uma geometria correta, anexar um documento, registrar um andamento e concluir uma tarefa. Avaliar se a próxima ação fica clara para outra pessoa.

## Próximas entregas

1. Reconciliação manual de fontes e de chaves, divisão/fusão de parcelas e vínculos explícitos entre matrículas, proprietários, processos e áreas. A prévia de revisões já existe para BANCO_REG; falta estender a reconciliação aos demais formatos e às mudanças de identidade.
2. Login corporativo, autorização por perfil, autoria autenticada e trilha de auditoria protegida. A autoria declarada da versão local não atende esse requisito.
3. Banco PostgreSQL/PostGIS, armazenamento privado de arquivos, rotinas de backup/restauração e implantação revisada pela TI.
4. Fluxos configuráveis por modalidade, condicionantes, listas documentais e alertas de prazo.
5. Integração com GIS/protocolo e formatos KML, Shapefile e GeoPackage com tratamento explícito de projeções.
6. Indicadores financeiros validados, relatórios gerenciais e integração de assinatura.
7. Coleta móvel/offline, OCR e assistência à leitura de documentos, após estabilizar o fluxo e os controles de acesso.

Critério para evolução: o fluxo deve ser validado por usuários das áreas responsáveis. Uma demonstração local funcional não comprova autorização, consistência cadastral, precisão topográfica nem prontidão para operação corporativa.
