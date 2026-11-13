# Integração da auditoria com a master

Data: 2026-11-13. A auditoria original foi registrada em `9d3990f`; a master publicada `d8c53ae` foi integrada em `40e8316`. Esse merge acrescentou as implementações de F21/F22 à interface refinada. O [relatório original](README.md) continua descrevendo seus 38 templates e seus próprios resultados, anteriores a essa integração; a aplicação integrada contém 42 templates.

## Composição preservada

- Os context processors de integrações, orientação por rota e resumo do robô coexistem.
- O controle persistente de F22 continua em Acompanhamento, junto dos atalhos, coleta, etapas e percurso; o resumo do robô continua nas ofertas.
- O sinal e o diagnóstico ouro de F21 foram preservados. F21 permanece `implemented`, com a prova real positiva bloqueada; F22 permanece `done`.
- Os registros exatos de entradas dinâmicas e a whitelist de qualidade conservam os consumidores das duas implementações.
- As novas rotas de controle do robô, inclusive sua página de erro, selecionam **Acompanhamento** no menu. Duas regressões reproduziram a seleção errada antes do ajuste e passaram depois, com a correção em `d245b64`.

## Navegador após integração

O [roteiro complementar](post-merge.cjs) e os [resultados](post-merge-results.json) cobrem 20 combinações em 1440/375 px: acompanhamento, ofertas, detalhe, configurações, IA, backups, sugestões, robô pausado, consulta de ofertas durante pausa e erro ao salvar comando. Cada página conservou um título principal e um destino atual, sem overflow horizontal, verificações incompletas ou violações detectadas pelo axe.

Oito checks de fluxo confirmaram, nas duas larguras, pausa persistente após recarregar, ofertas consultáveis durante a pausa, orientação correta no erro de comando e retomada explícita. Não houve erro JavaScript de página nesses percursos. Os dados e serviços usados eram próprios e sintéticos; nenhum envio real ou autenticação de conta foi acionado.

| Estado integrado | Desktop | Janela estreita |
|---|---|---|
| Acompanhamento e controle | [Captura](evidence/integrated-tracking-1440.png) | [Captura](evidence/integrated-tracking-375.png) |
| Ofertas e resumo do robô | [Captura](evidence/integrated-offers-1440.png) | [Captura](evidence/integrated-offers-375.png) |
| Pausa confirmada | [Captura](evidence/integrated-robot-paused-1440.png) | [Captura](evidence/integrated-robot-paused-375.png) |
| Erro de comando | [Captura](evidence/integrated-robot-save-error-1440.png) | [Captura](evidence/integrated-robot-save-error-375.png) |

## Sincronização documental

[Estado atual](../../status-atual.md), README, PRD, stack, arquitetura, diretrizes, operação do harness, design, glossário e orientação factual do AGENTS foram alinhados ao código integrado. As 22 features possuem situação e avaliação referenciadas em seus 66 artefatos spec/plan/contract. Planos e contratos originais são preservados integralmente após retirar o aviso de atualização. O JSON de progresso conserva exatamente os dados da master publicada, incluindo F21 incompleta.

As novas convenções de apresentação estão descritas nas specs das features afetadas, com rastreabilidade para os relatórios. Foram acrescentados guias de operação de F17/F22 e corrigidas duas referências a código de coleta substituído por navegação em fatias. Relatórios datados, falhas antigas e decisões originais não foram convertidos em sucesso retroativo.

## Validação final

A suíte final aprovou **899 casos únicos** em três lotes de 126, 178 e 595, sem falhas, erros, skips, omissões ou duplicatas. A união dos JUnits coincide exatamente com a coleção, e os hashes dos arquivos de código/testes permaneceram estáveis. Os seis grupos de gates, o check do harness e os quatro testes do harness passaram. A [evidência de integração](integration-validation.json) registra comandos, manifestos, resultados, checks documentais e limites de atribuição. O estado de publicação deve ser conferido pelo commit e pela referência remota informados na entrega; este relatório não afirma um push antes de sua execução.

A validação visual conserva os limites do relatório original: sem leitor de tela real, outros motores, dispositivo físico ou todas as combinações de fotos/IA com dados reais. O bloqueio positivo real de F21 continua explícito em sua avaliação.

## Revisão do diff

A comparação com `d8c53ae` conferiu o shell, a coexistência dos context processors, os registros de qualidade, os handlers de erro e a apresentação financeira. A integração conserva o controle/diagnóstico recebidos e não altera fórmulas, elegibilidade, recibos ou critérios de F21/F22. O único defeito novo confirmado foi a seleção de navegação das rotas do robô, corrigido e coberto pelas regressões acima. Não há outro finding confirmado restante dessa revisão; os limites de validação real continuam explícitos.

Para reproduzir a checagem documental desta revisão, execute `python3 docs/design/audit-2026-11-13/check-documentation.py` na raiz. O script usa a baseline publicada da revisão e valida status, DAG/ondas, avaliações, links locais e preservação dos planos/contratos/progresso; ele não é um gate que aprove futuras mudanças de requisitos automaticamente.
