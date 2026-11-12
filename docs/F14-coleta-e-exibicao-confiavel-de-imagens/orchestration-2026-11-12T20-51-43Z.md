# Orchestration Journal — F14 — auditoria da prova externa

**Run:** `2026-11-12T20-51-43Z`
**Feature folder:** `docs/F14-coleta-e-exibicao-confiavel-de-imagens/`
**Branch:** `feat/F14-imagens-locais`
**Started at:** `2026-11-12T20:51:43.062395+00:00`
**Retry budget:** `0` para nova coleta; auditoria das evidências existentes.
**Status:** `manual-pending`

## Escopo

Retomada solicitada pelo coordenador para verificar se a prova de duas resoluções reais da mesma foto pode ser concluída com os artefatos disponíveis. A implementação e o contrato são preservados. Nenhum navegador, perfil, serviço, banco ou fonte real foi acessado nesta execução.

## Cycle Log

| # | Kind | Status | Counts / Notes | Artifact |
|---|---|---|---|---|
| 0 | evidence audit | pending | E2E-FONTE-01 continua BLOCKED; sem novo ciclo de correção | evidence/source-proof-audit-2026-11-12T20-51-43Z.json |

## Evidência e limites

O manifesto real contém dois anúncios e 13 fotos. Todos os 13 pares de hashes recebido/conservado coincidem; cada foto tem exatamente uma resolução oferecida registrada. As três observações sanitizadas anteriores correlacionam dez PhotoIDs cada e também não contêm PhotoID com dimensões distintas.

A miniatura nativa da fonte tem dimensões naturais iguais às da foto principal (735×960) e o mesmo digest de URI registrado. Dimensões CSS de 36×36 não constituem outra resolução recebida. A miniatura derivada pelo Garimpei também não constitui variante oferecida pela fonte.

O registro prova cópias locais e carregamento da amostra, mas não demonstra seleção entre duas resoluções reais da mesma foto. Nenhuma inferência a partir de fotos diferentes ou de divergência de arredondamento 722/723 px foi promovida a prova.

## Final Verdict

**Status:** `manual-pending`
**Total cycles:** `0` novas correções; a execução anterior encerrou com dois ciclos.
**Canonical evaluation:** [eval-report-2026-11-12T20-12-37Z.md](eval-report-2026-11-12T20-12-37Z.md), preservada: 34 PASS, 0 FAIL, 1 BLOCKED; seis ACs verificadas e duas indeterminadas.

Bloqueio: `E2E-FONTE-01`, requisito externo de variantes reais não comprovado. Para retomar, é necessário obter, por fluxo autorizado e perfil exclusivo, um caso da mesma foto efetivamente oferecida em duas resoluções, conservar a melhor e confrontar bytes, versão e carregamento local. Não houve waiver nem mudança do progresso para done.

## Verificação desta execução

Asserções executadas sobre os quatro JSONs versionados e três probes sanitizados anteriores; contagens e hashes dos insumos estão no artefato da auditoria. Alterações limitadas a documentação/evidência. Gates e suíte da aplicação não foram repetidos: esta execução não altera seus inputs e não declara uma nova avaliação completa. A suíte final da união continua responsabilidade do coordenador.

Lock exclusivo desta auditoria liberado após a escrita; nenhum recurso de runtime criado. Arquivos privados dos probes não foram copiados, apenas seus hashes e contagens sanitizadas.
