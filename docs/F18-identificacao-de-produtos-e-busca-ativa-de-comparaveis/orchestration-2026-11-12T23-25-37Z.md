# Orchestration Journal — F18 investigação geográfica

**Run:** `2026-11-12T23-25-37Z`  
**Branch:** `wave/resume-f18`  
**Status:** `aborted` — evidência geográfica efetiva indisponível.

## Investigação

O usuário autorizou a investigação e uma janela exclusiva para a fonte real. Preservou-se a implementação e não houve ciclo de correção nem nova avaliação completa. A inspeção local mostrou que os 6 km reportados anteriormente são metadados da navegação HTML inicial. A consulta GraphQL posterior recebe filtros alterados para 500 km; o teste local de integração de navegador confirma a separação desses estágios, passando em 13,45 s. A resposta real não forneceu parâmetros geográficos reconhecidos. A interface foi inspecionada sem salvar configuração e não forneceu mecanismo verificável de mudança e restauração na observação limitada.

Correção de interpretação: os diários e relatórios anteriores que associam 6 km à resposta da pesquisa devem ser lidos como referência aos metadados anteriores à consulta, não como prova do raio aplicado à resposta GraphQL. Permanecem sem alteração histórica. Também não existe confirmação de que a fonte aplicou 500 km; o bloqueio e a desativação automática permanecem apropriados. Detalhes e limites em `diagnostico-geografia-2026-11-12.md` e `evidence/live-response-context-2026-11-12T23-25-37Z.json`. Navegador fechado, perfil liberado e nenhum dado de negócio publicado.
