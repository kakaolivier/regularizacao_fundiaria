# Plano do produto

## Entrega atual

Aplicação local de gestão fundiária com mapa municipal, processo detalhado, campos originais, referências de imóveis/trechos, histórico, documentos versionados, tarefas, controle pericial, geometrias versionadas e exportações CSV/GeoJSON. Fontes reais importadas em banco local ignorado pelo Git; testes usam bases temporárias fictícias.

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

1. Reconciliação manual de fontes, identificação de imóveis e vínculo explícito entre matrículas, proprietários, processos e parcelas. Importação de revisões com prévia das diferenças.
2. Login corporativo, autorização por perfil, autoria autenticada e trilha de auditoria protegida. A autoria declarada da versão local não atende esse requisito.
3. Banco PostgreSQL/PostGIS, armazenamento privado de arquivos, rotinas de backup/restauração e implantação revisada pela TI.
4. Fluxos configuráveis por modalidade, condicionantes, listas documentais e alertas de prazo.
5. Integração com GIS/protocolo e formatos KML, Shapefile e GeoPackage com tratamento explícito de projeções.
6. Indicadores financeiros validados, relatórios gerenciais e integração de assinatura.
7. Coleta móvel/offline, OCR e assistência à leitura de documentos, após estabilizar o fluxo e os controles de acesso.

Critério para evolução: o fluxo deve ser validado por usuários das áreas responsáveis. Uma demonstração local funcional não comprova autorização, consistência cadastral, precisão topográfica nem prontidão para operação corporativa.
