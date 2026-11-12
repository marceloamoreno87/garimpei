# Integração das pendências F14/F15/F17/F18

Execução iniciada em 2026-11-12, autorizada pelo usuário para reunir todas as worktrees na master e executar pendências em paralelo. Sem push ou publicação remota.

## Estado inicial

Base master `8e94dab`, limpa. Nove das doze branches de worktrees já estavam contidas na master. F17 tinha incremento versionado e verificação ativa; F15 e F18 continham implementação não versionada de agentes ainda ativos. Escritores originais foram preservados; coordenação de progresso permanece única.

Seis gates Python passaram na base; harness: quatro testes aprovados e check-harness aprovado. Evidências adjacentes. Essas verificações são da base, não da união final.

## Integrações

- F14: auditoria documental `f999b1b` integrada. Preserva 34 PASS e 1 BLOCKED: nenhuma foto do corpus real auditado possui duas resoluções oferecidas comprovadas. Feature permanece implemented/manual-pending.

- F15: checkpoint `aa2c6b2` integrado por `8f70782`, flag opt-in/default false e seis gates aprovados. Avaliação do contrato ainda incompleta.
- União F15/F17 preparada em worktree isolada a716: reconciliador F15 preservado no supervisor F17; migration aditiva 0023 reúne os históricos; backup/restauração com histórico de avaliações e proveniência dos alertas passou em PostgreSQL. Novo guard recusa campos de negócio sem decisão explícita de recuperação.

## Verificação da união final

Candidato de código `e6bbc22`, em a716, branch `integration/pending-features-2026-11-12`: **676 PASS**, quatro grupos disjuntos por arquivo, 818,63 s. Os 676 itens coletados foram executados exatamente uma vez; nenhuma omissão, duplicata ou mudança de entrada durante a execução. [Resumo integral](evidence/final-union-suite/full-summary.json), [inventário](evidence/final-union-suite/full-manifest.json) e [hashes](evidence/final-union-suite/frozen-inputs.json).

Os seis gates Python, Django check, ausência de drift, coleta de estáticos, build, quatro testes do harness, check-harness e sincronismo/contraste dos tokens passaram no mesmo candidato. Evidências `evidence/final-union-*`.

As execuções anteriores permanecem intactas: primeira rodada657 terminou650PASS/5FAIL/2ERROR; segunda675 terminou674PASS/1FAIL. As falhas foram corrigidas com regressões. A terceira rodada676 acima é a validação final, sem relaxar os testes anteriores.

Todos os15HEADs das worktrees existentes são ancestrais do candidato; nenhuma worktree de feature tem mudanças não versionadas. [Inventário](worktree-inventory-before-merge.json). Worktrees são preservadas, incluindo os formulários de revisão humana F15.

## Correções nas fronteiras

- F15 `060be5d`: coortes mantêm os lotes de 5/12 fotos aplicáveis sem colisão com o perfil anterior F19; WebP F14 gera derivado PNG sem alterar o original. Doze integrações focais passaram na união.
- F18 `8723131`: identidade/correção, pesquisa limitada e diagnósticos integrados ao supervisor F17 e à condição F15. Rotas/configurações de todas as features preservadas; migrations aditivas culminam em `0025_merge_identity_research`.
- F17 `08b79b8`: mídia/inferência interrompidas retomam sem posse antiga, partes confirmadas permanecem intactas, PNG preparado integra o pacote e inferência restaurada aguarda retomada explícita. Evidência focal do autor corrigiu também as duas falhas do full inicial.
- Backup inclui avaliações, cabeças, sete modelos de identidade/pesquisa, coortes e proveniência dos alertas. Campos de negócio ausentes passam a ser recusados antes do snapshot, com seis exclusões privadas de sessão explícitas.
- A serialização conserva microssegundos de DateTimeField. O roundtrip PostgreSQL com toda a proveniência e grafo F15/F18 passou em 19,88 s; antes, timestamps no modelo e no JSON divergiam por truncamento Django.
- Identidade efetiva/família/atributos/conflitos/política entram na mesma fronteira semântica usada para preparar e validar avaliação. Correção manual invalida a avaliação imediatamente; conteúdo equivalente preserva cache. Duas regressões reproduzidas e 12 testes afetados aprovados.
- Verificações das fronteiras de identidade, pesquisa, avaliação e alertas: 21 PASS em 103,41 s. Seis gates do candidato: PASS, 423 fontes. Django, drift, estáticos, build, tokens e harness: PASS.

## Revisão independente

Os P1 iniciais e as correções de integração foram revisados. O P2 do orçamento de mídia recebeu regressão e correção6c73dad: tentativa4 é exaurida, sem quinta transferência. O rollback de inicialização passou a usar orçamento compartilhado e sondagens limitadas pelo restante; cenários medidos PostgreSQL3,82s, WAHA6,39s e imagem1,04s, todos dentro dos8s originais. A reserva do envelope é medida, sem promessa de hardcap para suspensão do OS/preflight externo arbitrário.

Deltas adicionais preservam dano/suspeita/divergência manual na mensagem, recusam versões antigas de prompt/schema e não publicam como atual resposta de observação/modelo/coorte divergente. Os avisos de dano não alteram a elegibilidade nem os recibos históricos.

## Pendências preservadas

- F14: duas resoluções reais da mesma foto não comprovadas, sem waiver do contrato.
- F15: usuário confirmou em 2026-11-12 que fará depois a revisão humana. Rótulos/medição real ficam pendentes; não executar o conjunto reservado antes dessa revisão.
- F18: fonte real respondeu raio nativo de 6 km diante de 500 km solicitados. Nenhuma amostra local indevidamente publicada. Política medida combinada ainda não completa; ativação automática permanece fechada.
- F17: contrato permanece preliminar, políticas reais desativadas e CLI/matriz completa de falhas ausente. Avaliação final original58BLOCKED/10ACindeterminados; integração do código e testes não equivalem a aceite da feature. O [suplemento da calibração](calibration-supplement.md) registra a execução direta corrigida:30 medições, cinco controles de recuperação e recursos próprios encerrados.


## Consolidação e escopo

Somente F14/F15/F17/F18 tiveram seu progresso consolidado pelo coordenador. Os demais16 registros permanecem idênticos à base `8e94dab`. Nenhuma das quatro selecionadas foi promovida a `done`: testes do código integrado não substituem as provas contratuais pendentes.

O [estado da onda](wave-status.md) reúne branches, ciclos, relatórios e limitações. O usuário autorizou merge na master local; não houve push, PR ou publicação remota. Merge local `2dd9906` concluído. A aplicação está pronta e configuração/interesses foram preservados: [verificação na master](master-verification.md). Um rascunho documental concorrente da F21 foi preservado sem commit; não altera os resultados da onda.
