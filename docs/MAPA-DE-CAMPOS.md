# Onde encontrar cada campo

Caminho comum: **Imóveis e trechos → abrir o imóvel/subtrecho → área indicada abaixo**. Referência dos 56 campos do dicionário incorporado em 30/10/2026.

Em toda alteração, informe autor e motivo. Deixar a entrada vazia mantém o valor atual. As colunas do Excel ajudam a localizar a origem; não é necessário decorá-las para usar o site.

Os campos automáticos não aceitam digitação. Campos protegidos podem ser preenchidos quando ainda não informados, mas não substituídos depois de preenchidos. A chave permanece estável após a criação.

[Voltar ao manual de testes](MANUAL-DE-TESTES.md)

## Cadastro

| Campo da tela | Coluna em BANCO_REG | Preenchimento | Restrição |
|---|---|---|---|
| Chave do imóvel / trecho | C | Somente consulta / automático | Não editável |
| Item de origem | D | Somente consulta / automático | Não editável |
| Município | E | Escolha na lista | Protegido após preenchimento |
| Denominação do imóvel | F | Texto livre | Protegido após preenchimento |
| Subtrecho | G | Texto livre | Protegido após preenchimento |
| Proprietário | H | Texto livre | Editável; vazio preserva |
| Ofício vinculado | I | Texto livre | Editável; vazio preserva |
| Tipo de processo | J | Escolha na lista | Protegido após preenchimento |
| Processo administrativo / protocolo | K | Texto livre | Editável; vazio preserva |
| Processo judicial | L | Texto livre | Editável; vazio preserva |
| Patrocínio MVGA | M | Escolha na lista | Editável; vazio preserva |
| Etapa atual | N | Escolha na lista | Editável; vazio preserva |
| Passível de reequilíbrio | O | Escolha na lista | Editável; vazio preserva |
| Área inicial (m²) | P | Texto livre | Editável; vazio preserva |
| Matrícula inicial | R | Texto livre | Editável; vazio preserva |
| DUP | T | Texto livre | Editável; vazio preserva |
| Indenização depositada | X | Valor sem R$ e sem milhar: 12000,50 | Editável; vazio preserva |
| Contato do proprietário / advogado | AQ | Texto livre | Editável; vazio preserva |
| Início previsto da obra | BB | Data exata pelo calendário | Editável; vazio preserva |

## Posse e obras

| Campo da tela | Coluna em BANCO_REG | Preenchimento | Restrição |
|---|---|---|---|
| Solicitação de ajuizamento | U | Data exata pelo calendário | Protegido após preenchimento |
| Data da petição inicial | V | Data exata pelo calendário | Protegido após preenchimento |
| Dias para ajuizar | W | Somente consulta / automático | Não editável |
| Andamento da imissão provisória | AN | Escolha na lista | Editável; vazio preserva |
| Cumprimento do mandado | AO | Data exata pelo calendário | Editável; vazio preserva |
| Indicador pela data do mandado | AP | Somente consulta / automático | Não editável |

## Perícia

| Campo da tela | Coluna em BANCO_REG | Preenchimento | Restrição |
|---|---|---|---|
| Proposta do expropriado | Y | Texto livre | Editável; vazio preserva |
| Laudo apresentado | Z | Escolha na lista | Editável; vazio preserva |
| Segunda perícia | AA | Escolha na lista | Editável; vazio preserva |
| Primeiro laudo (R$) | AB | Valor sem R$ e sem milhar: 12000,50 | Editável; vazio preserva |
| Segundo laudo (R$) | AC | Valor sem R$ e sem milhar: 12000,50 | Editável; vazio preserva |
| Manifestação sobre o laudo | AD | Escolha na lista | Editável; vazio preserva |
| Fase pericial atual | AE | Escolha na lista | Editável; vazio preserva |
| Perito nomeado | AF | Texto livre | Editável; vazio preserva |
| Honorários periciais / comentários | AG | Texto livre | Editável; vazio preserva |
| Tentativa de acordo na perícia | AH | Escolha na lista | Editável; vazio preserva |
| Situação do acordo pericial | AI | Texto livre | Editável; vazio preserva |

## Acordos

| Campo da tela | Coluna em BANCO_REG | Preenchimento | Restrição |
|---|---|---|---|
| Valor do acordo (R$) | AK | Valor sem R$ e sem milhar: 12000,50 | Editável; vazio preserva |
| Data da assinatura do acordo | AL | Data exata pelo calendário | Editável; vazio preserva |
| Andamento do acordo | AM | Escolha na lista | Editável; vazio preserva |

## Registro

| Campo da tela | Coluna em BANCO_REG | Preenchimento | Restrição |
|---|---|---|---|
| Área registrada (m²) | Q | Texto livre | Editável; vazio preserva |
| Matrícula do registro | S | Texto livre | Editável; vazio preserva |
| Registro da imissão provisória | AR | Texto livre | Editável; vazio preserva |
| Registro definitivo | AS | Texto livre | Editável; vazio preserva |

## Fase final

| Campo da tela | Coluna em BANCO_REG | Preenchimento | Restrição |
|---|---|---|---|
| Sentença | AJ | Texto livre | Editável; vazio preserva |
| Data do arquivamento | AT | Data exata pelo calendário | Editável; vazio preserva |

## Acompanhamento MVGA

| Campo da tela | Coluna em BANCO_REG | Preenchimento | Restrição |
|---|---|---|---|
| Providência / situação | AU | Texto livre | Editável; vazio preserva |
| Averbação / registro da servidão | AV | Texto livre | Editável; vazio preserva |
| Matrícula conferida | AW | Escolha na lista | Editável; vazio preserva |
| Andamento MVGA | AX | Texto livre | Editável; vazio preserva |
| Obter certidão de matrícula | AY | Escolha na lista | Editável; vazio preserva |
| Contato com a vara | AZ | Texto livre | Editável; vazio preserva |
| Previsão de imissão | BA | Data exata pelo calendário | Editável; vazio preserva |
| Previsão de liberação MVGA | BC | Data exata pelo calendário | Editável; vazio preserva |
| Responsável MVGA | BD | Texto livre | Editável; vazio preserva |

## GIS

| Campo da tela | Coluna em BANCO_REG | Preenchimento | Restrição |
|---|---|---|---|
| Status GIS | A | Escolha na lista | Editável; vazio preserva |
| Identificador GIS | B | Texto livre | Protegido após preenchimento |

## Fora desses formulários

| Informação | Onde consultar / preencher |
|---|---|
| Valores e referências das planilhas anteriores | Processos → abrir processo → Resumo; consulta por fonte, sem edição direta |
| Dados de origem | Processo → Dados de origem, ou imóvel → Versões de origem preservadas; consulta |
| Documento do laudo, acordo ou decisão | Processo → Documentos → Anexar documento |
| Próxima ação, responsável e prazo | Processo → Resumo → Criar tarefa, ou Tarefas e prazos |
| Parecer, contato ou decisão em texto | Processo → Registrar andamento |
| Polígono geográfico | Processo → Mapa e áreas → Desenhar área ou GeoJSON |

Área inicial e área registrada são campos de texto. Elas não são calculadas a partir do polígono. O campo Sentença é texto na nova ficha; um valor monetário de sentença das planilhas anteriores pode continuar aparecendo no quadro de referências da fonte.
