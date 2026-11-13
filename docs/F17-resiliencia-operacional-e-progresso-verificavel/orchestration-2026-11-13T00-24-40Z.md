# Orchestration Journal — F17 Resiliência operacional e progresso verificável

**Run:** `2026-11-13T00-24-40Z`
**Branch:** `wave/current-f17`
**Retry budget:** 3
**Status:** `running`

## Cycle Log

| # | Kind | Status | Counts / Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | running | Retomada das medições adversas e pontos de queda | [contrato](contract.md) |
| 0 | testes dirigidos | passed | 35 medições em sete casos; teste integrado 57,14 s; seis gates aprovados | [evidência](evidence/fault-calibration-2026-11-13T00-24-40Z.json) |
| 0 | testes dirigidos | passed | CLI com dois cortes SIGKILL: teste combinado 114,82 s; seis gates aprovados | [implementação](impl-report.md) |

## Cycle Detail

O perfil continua preliminar e a ativação real desabilitada. Os ensaios reduzidos em eval não substituem limites reais de operação.

O novo `calibrate-faults` mede cinco repetições de cada caso de rede, arquivo e fila, registrando controles, duração, filas e amostras de armazenamento. A fila de controle tem 999 itens contra 1.000; armazenamento é amostrado após cada operação, não medição contínua do pico. As demais falhas e fronteiras de queda continuam em desenvolvimento.

A CLI também executa, em instalações eval separadas, SIGKILL após POST e após lote confirmado. O comando canônico de calibração integra as 35 medições adversas; sua regressão integral está em curso e o perfil permanece preliminar.
