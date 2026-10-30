# Evolução a partir do dicionário e do controle

Análise em 30/10/2026 dos arquivos DICIONARIO_DADOS_REGULARIZACAO.xlsx e CONTROLE_REGULARIZACAO.xlsx. Este documento contém estrutura e contagens agregadas; os dados cadastrais e as planilhas permanecem fora do Git.

## O que mudou

| Aspecto | Controles anteriores | Novo material e implementação |
|---|---|---|
| Organização | Acompanhamento geral e perícias, distribuídos em diversas abas | BANCO_REG reúne 56 campos. As outras nove abas descrevem consultas e formulários pretendidos |
| Significado dos campos | Interpretação a partir dos cabeçalhos e valores | Dicionário com tipo, lista, obrigatoriedade, origem, frequência e restrições de atualização |
| Identificação | CNJ completo organiza o dossiê e reúne fontes | Cada imóvel/subtrecho tem chave própria; o CNJ continua organizando o dossiê, sem identificar uma atualização de imóvel |
| Atualização | Etapa e histórico do processo; dados originais consultáveis | Formulários por área de trabalho, com valores atuais, listas, motivo, autoria e antes/depois |
| Revisões | Importação inicial por seed.json | Upload no site, prévia de diferenças, confirmação, fonte preservada e backup do banco |
| Qualidade | Números incompletos e divergências entre fontes | Também aponta chaves repetidas, campos obrigatórios ausentes, listas fora do padrão e datas inexatas |

As instruções e exemplos VBA dentro dos documentos foram tratados como descrição do fluxo pretendido. Não foram executados. O esquema dos formulários foi revisado e incorporado como metadados Python/JSON, sem interpretar texto da planilha como código.

## Achados no arquivo enviado

- 56 colunas em BANCO_REG, de A a BD, com cabeçalhos na linha 3.
- 482 linhas com conteúdo cadastral candidato; 1.048.575 linhas físicas na aba, em sua maioria formatadas e vazias. A leitura percorre as células efetivas sem materializar uma matriz de um milhão de linhas.
- Três grupos de chaves repetidas, envolvendo dez linhas. Nesses grupos há diferenças de área inicial: não é seguro consolidá-los automaticamente.
- Seis linhas não têm município, denominação ou subtrecho suficientemente informado, incluindo quatro linhas incompletas ao final. “N/A” não é considerado identificação suficiente.
- Em uma base vazia de teste: **466 imóveis/subtrechos elegíveis**, organizados em **359 dossiês**, e **16 linhas bloqueadas para conferência**. Em uma base existente, a contagem de novos/atualizados depende dos vínculos e valores já cadastrados.
- ETAPA_ATUAL está vazia nas 482 linhas candidatas. O site exibe “Etapa não informada”; a narrativa não é transformada em uma decisão de etapa.
- O campo PREVISAO_DE_LIBERAÇÃO_MVGA contém textos como “LIBERADO”, “DESISTÊNCIA”, meses e intervalos, embora o dicionário o classifique como data. O texto original permanece visível, com aviso; nenhuma data exata é inventada.
- Há 69 divergências entre o indicador de liberação de origem e o cálculo pela data do mandado. O cálculo é identificado como tal e não substitui uma autorização documental de obra.
- STATUS GIS e ID GIS são campos de controle. Não são coordenadas ou polígonos de imóvel.

## Regras implementadas

1. **Chave por imóvel.** A chave importada é preservada; se uma fórmula de concatenação não tiver resultado salvo, ela é construída a partir de processo, denominação e subtrecho. Fórmulas arbitrárias nunca são executadas. Duplicatas e chaves incompatíveis ficam bloqueadas.
2. **Atualização direcionada.** A revisão encontra o registro por sua chave completa. O mesmo CNJ pode ter muitos registros independentes. Um vínculo a dossiê existente exige CNJ completo e correspondência não ambígua; isso não substitui o cadastro geral desse dossiê.
3. **Vazios preservam.** Células em branco não eliminam informação existente. “N/A”, zero e valores ausentes continuam distintos.
4. **Campos protegidos.** Chave, item, dias calculados e indicador pela data do mandado não aceitam edição manual. Campos definidos como sem sobrescrita podem ser preenchidos quando ainda não informados, mas não substituídos após preenchimento válido.
5. **Datas e valores.** Datas seriais são interpretadas segundo o calendário do XLSX e o campo definido no dicionário. Datas inexatas permanecem texto. Os formulários aceitam datas completas e valores monetários explícitos; os originais continuam disponíveis.
6. **Histórico.** Edições registram antes/depois, responsável e motivo. Revisões mantêm as fontes anteriores, com arquivo, hash, aba e linha. Anexos, tarefas e geometrias anteriores permanecem no dossiê.
7. **Revisão segura.** A prévia não grava registros operacionais. A confirmação valida se a base mudou, cria backup consistente do SQLite e aplica a transação. Uma falha reverte as gravações. Arquivo com hash já importado não é reaplicado.
8. **Pendências contextuais.** A obrigatoriedade do dicionário aparece como observação, porque campos como matrícula de registro ou data de mandado dependem da fase. Não são inventados valores para permitir importação. Falta de identificação suficiente, entretanto, bloqueia o registro.

## Pontos que ainda precisam da equipe

- Diferenciar os subtrechos nas chaves repetidas; as áreas distintas podem representar parcelas diferentes.
- Definir as etapas dos registros hoje sem ETAPA_ATUAL.
- Revisar listas divergentes, como a classificação “BRK É RÉ -JUDICIAL”, e as inconsistências cadastrais sinalizadas.
- Decidir se a previsão de liberação deve ter campos separados para data exata, período e situação.
- Validar o indicador de liberação nos casos extrajudiciais, acordos e exceções; a presença de uma data isolada não cobre todo o fluxo real.
- Planejar reconciliação explícita para alterações de identidade e divisão/fusão de parcelas. A chave permanece estável após uma correção do número judicial na ficha; uma nova chave na planilha não é automaticamente fundida à anterior.

O sistema não edita o Excel original nem exporta uma versão sincronizada de BANCO_REG nesta entrega. Revisões são importadas mediante conferência. Login corporativo e autoria autenticada continuam no planejamento; a autoria local é declarada pelo usuário.
