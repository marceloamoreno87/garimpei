# Orchestration Journal — F17 Resiliência operacional e progresso verificável

**Run:** `2026-11-13T00-24-40Z`
**Branch:** `wave/current-f17`
**Retry budget:** 3
**Status:** `aborted`

## Cycle Log

| # | Kind | Status | Counts / Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | running | Retomada das medições adversas e pontos de queda | [contrato](contract.md) |
| 0 | testes dirigidos | passed | 35 medições em sete casos; teste integrado 57,14 s; seis gates aprovados | [evidência](evidence/fault-calibration-2026-11-13T00-24-40Z.json) |
| 0 | testes dirigidos | passed | CLI com dois cortes SIGKILL: teste combinado 114,82 s; seis gates aprovados | [implementação](impl-report.md) |
| 0 | calibração | partial | `calibrate`: 347,50 s; 30 controles/timeout, 35 falhas e cinco restaurações | [evidência](evidence/calibration-combined-2026-11-13T00-24-40Z.json) |
| 0 | calibração de quedas | partial | 25 SIGKILLs em cinco fronteiras, cinco por caso; recursos encerrados | [implementação](impl-report.md) |

## Cycle Detail

O perfil continua preliminar e a ativação real desabilitada. Os ensaios reduzidos em eval não substituem limites reais de operação.

O novo `calibrate-faults` mede cinco repetições de cada caso de rede, arquivo e fila, registrando controles, duração, filas e amostras de armazenamento. A fila de controle tem 999 itens contra 1.000; armazenamento é amostrado após cada operação, não medição contínua do pico. As demais falhas e fronteiras de queda continuam em desenvolvimento.

A CLI também executa, em instalações eval separadas, SIGKILL após POST e após lote confirmado. O comando canônico de calibração integra as 35 medições adversas; o perfil permanece preliminar.

A regressão canônica passou em 347,50 s, mantendo perfil não confirmado. Foram executados cinco cortes SIGKILL por fronteira: antes e depois da autorização, depois do POST, depois de confirmação e depois de lote confirmado. Todos recuperaram, com origens e canal falsos. Esses testes usam instalações separadas, não registram controle de mesma carga e tampouco medem o pico do banco; os limites de F17 ainda não foram confirmados.

## Final Verdict

**Status:** `aborted`

Interrompido por solicitação do usuário. A regressão final de cinco cortes falhou quando o daemon Docker deixou de responder; a limpeza automática `--clean` recusou operação sem propriedade verificável. Processos locais identificados nos manifestos da execução receberam encerramento; containers e volumes não puderam ser inspecionados com o daemon indisponível. Preservar `/tmp/garimpei-f17-five-cuts-test-PyivzY/test_persistent_unit_fault_sus0/operational-fault` para inspeção futura. A matriz, os controles de mesma carga, o pico de armazenamento e a avaliação integral continuam pendentes; não promover F17.
