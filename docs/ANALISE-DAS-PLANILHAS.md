# Interpretação das planilhas

As duas planilhas são **controles complementares**. A Rev. 112 acompanha a tramitação fundiária e os registros. A planilha de perícias acompanha avaliações judiciais, laudos, contestações e estimativas de desembolso. A base contém modalidades judiciais e extrajudiciais; não há evidência de que cada arquivo corresponda exclusivamente a uma dessas modalidades.

## Inventário conferido

| Arquivo / aba operacional | Registros importados |
|---|---:|
| Rev. 112 — Processos ajuizados | 468 |
| Rev. 112 — Processos a serem ajuizados | 7 |
| Rev. 112 — Caução - Reembolso | 52 |
| Rev. 112 — Processos - ANEXO II 4º TA | 25 |
| Rev. 112 — REGISTROS | 336 |
| Perícias — LAUDOS APRESENTADOS | 45 |
| Perícias — LAUDOS AINDA NÃO APRESENTADO | 23 |
| **Total de linhas operacionais preservadas** | **956** |

As demais abas (listas, casos positivos e simulações) permanecem no material de referência do arquivo `data/seed.json`. Não são tratadas como novos processos ou parcelas de um total financeiro.

O agrupamento produziu **489 cadastros**, com **56 cadastros vinculando registros dos dois arquivos**. Esses números não equivalem a uma contagem jurídica validada de processos únicos. **218 cadastros** não têm um CNJ completo de 20 dígitos e permanecem separados. Esse grupo inclui casos extrajudiciais sem CNJ, protocolos e números incompletos; não significa que todos estejam errados.

O controle pericial tem **68 linhas em 67 cadastros**: um número completo aparece tanto na aba de laudos apresentados quanto na de pendentes. A ficha sinaliza a divergência e mantém as duas fontes. Não foi escolhida uma delas como verdade atual.

## Regras de importação

1. Agrupar somente números completos, com 20 dígitos, idênticos após remover pontuação. Não completar dígitos, inferir comarca nem mesclar somente pelo nome.
2. Preservar cada linha operacional como registro de origem, com arquivo, aba, linha, colunas, texto, valores e datas.
3. Expandir somente as células mescladas efetivamente presentes nas planilhas. Não propagar valores de uma linha para outra por suposição.
4. Preservar referências a vários trechos dentro de um mesmo processo. A vinculação de diferentes referências à mesma parcela física ainda precisa de conferência.
5. Tratar números de Excel como números; texto como “N/A”, “em projeto” e propostas descritivas permanece texto. Não converter indisponibilidade em zero.
6. Mostrar valores por origem e natureza. Não somar depósitos repetidos entre abas; estimativa, laudo, caução e reembolso não são equivalentes.
7. Criar marcos do histórico apenas a partir de células de data estruturadas. Textos narrativos ficam no histórico com indicação de ausência de data individual; não foram fracionados automaticamente em decisões supostas.
8. O cabeçalho da Rev. 112 menciona 13/05/2025, mas há células com datas posteriores, inclusive de 2026. A planilha pericial também usa referências de 2026. Não foi atribuída uma única data de atualização a toda a base.
9. A aba de ajuizados contém fórmulas estendidas até a última linha do Excel. O importador percorre o XML e descarta linhas sem dados operacionais, evitando criar milhões de processos falsos.
10. Um registro com denominação “N/A” foi mantido como **Imóvel não informado**, preservando o número, o trecho e todos os campos originais. Outro registro de caução sem denominação foi preservado pelo número completo.

## O que o domínio exige

- **Processo, imóvel e área de interesse** são conceitos distintos. Um processo pode envolver diferentes trechos, matrículas e proprietários.
- **Liberação da obra**, **imissão de posse**, **registro definitivo**, **fase pericial** e **encerramento financeiro** são controles independentes. “Liberado para obra” não implica conclusão da regularização.
- É necessário preservar a sequência: avaliação, divergência, eventual segunda perícia, manifestações, acordo/sentença e obrigações financeiras.
- DUP, ajuizamento, mandados, assinatura de acordo, registro e arquivamento são marcos úteis para o histórico quando existe data estruturada.
- Os arquivos anexados ao processo são documentos próprios; a planilha de acompanhamento é uma fonte de informações, não o acervo documental.

## Limites da interpretação

Não foi determinada automaticamente a área real de nenhum terreno. Não foram inferidas coordenadas a partir de nomes de proprietários ou empreendimentos. Nenhuma estimação monetária foi recalculada, e a importação usa os resultados armazenados pelo Excel para fórmulas. Números sem CNJ completo, divergências de valores, modalidades e equivalência entre referências exigem revisão pela equipe responsável.
