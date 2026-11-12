# Orchestration Journal — F18 prova geográfica

**Run:** `2026-11-12T23-20-23Z`
**Branch:** `wave/resume-f18`
**Status:** `aborted`
**Retry budget:** 3 ciclos; nenhum consumido.

## Pré-requisitos e prova

O usuário autorizou a prova real. O coordenador concedeu exclusividade após F14 fechar o navegador; workers e web permaneceram parados. A primeira preparação não abriu navegador porque o PostgreSQL estava parado; o coordenador disponibilizou apenas o banco principal para leitura. A consulta leu a configuração de monitoramento sem modificá-la, utilizou o adaptador presente na master e não publicou dados nem enviou mensagens.

Uma consulta do caso RTX 4060 8GB do corpus aprovado retornou 24 cartões e continuação. O contexto nativo informou raio de **6 km**, contra **500 km** solicitados; a verificação permaneceu falsa. A prova parou sem consultar a continuação nem publicar candidatos. O navegador foi fechado e a exclusividade liberada. Evidência sanitizada: `evidence/live-geography-retry-2026-11-12T23-20-23Z.json`.

## Resultado

`WRK-RESEARCH-01` permanece bloqueado; não foi feita avaliação completa nesta retomada e não há nova contagem de itens aprovados. O último relatório canônico é `eval-report-2026-11-12T22-01-57Z.md`. Uma segunda observação reproduziu a divergência da fonte e não demonstrou correção local; alterar a aceitação para ignorar o raio violaria a política geográfica. Pesquisa automática continua desabilitada e F18 não é `done`.
