# Implementação F17 — em execução

Branch isolada `feat/F17-resiliencia-operacional`, base `3ce35d5`. Este relatório parcial não declara aceite nem altera a feature para `done`.

O primeiro incremento contém modelos aditivos, progresso durável com deduplicação de fronteiras, instrumentação transacional de publicação, consumidores por fila, leitura de contagens por snapshot, comandos de backup/exportação/restauração, arquivo privado versionado por allowlist e barreira de recuperação persistente em arquivo e banco. A habilitação automática permanece desativada até a calibração e avaliação finais.

A captura usa `REPEATABLE READ READ ONLY`, registra schema, migrations, hash do código, perfil e cursor coberto. A exportação conserva exatamente os bytes do arquivo selecionado. URLs temporárias de mídia perdem query/fragment por schema, com exclusão declarada; campos arbitrários de credenciais em JSON são rejeitados. A restauração exige destino eval próprio, descartável e vazio; não importa autenticação nem jobs técnicos e conserva o despacho bloqueado.

Evidências do primeiro incremento: `evidence/calibration-initial.json`, `evidence/increment-gates.txt` e `evidence/increment-tests.txt`. Cinco percursos saudáveis usaram PostgreSQL/fonte/canal fake, com um recibo por percurso e nenhum envio real. Seis grupos Python passaram; onze testes unitários e um percurso integrado de backup/exportação/restauração passaram.

A integração controlada F14 agora conserva pins até publicação/abort, originais e miniaturas exatos, versões e associações; o ensaio restaurou os bytes por HTTP em raiz própria e recusou original obrigatório ausente. Isso usa corpus CONTROLADO gerado pela factory F14, não amostra do Facebook. A reconciliação CLI foi exercitada com cópia anterior ao POST: inventário incompleto e histórico fake ausente mantiveram a barreira; prova suficiente no vínculo original confirmou o recibo F09 e liberou somente o destino eval, conservando um único POST sintético original. A fila real foi limitada a1.000 tarefas com deduplicação da mesma requisição; repetição da fronteira não reinicia o orçamento de falhas. Snapshots operacionais podem ser reconsultados pelo UUID sem misturar momentos, em cache diagnóstico próprio excluído da cópia de negócio.

O lote mais recente teve18 testes alvo PASS em81,17s, junto dos seis grupos Python (359 fontes): evidence/media-recovery-tests.txt e evidence/media-recovery-gates.txt. Pendentes nesta revisão parcial: completar os cenários adversos restantes e a calibração do incremento; verificar UI/E2E com navegador; executar regressões completas e avaliação canônica por item. `spec.md`, `plan.md` e `contract.md` preservam a condição preliminar enquanto esses ensaios faltarem.

## Fechamento do checkpoint — aceite pendente

Fontes congeladas em `e4052ff`, com produção estabilizada antes do full final da união. `08b79b8` corrigiu retomada de mídia/inferência em execução e preservou PNGs preparados referenciados; `6c73dad` impede quinta tentativa de mídia restaurada; `840e98e` torna a preparação da fixture F16 determinística pela adoção pública antes da publicação. Não houve alteração nas assertivas de geração obsoleta, autorização/vínculo original ou unicidade do POST. `checkpoint-restore-and-restart.md` registra RED, testes afetados e gates.

Full próprio em `aae6fce`:568 coletados,566PASS/2FAIL, dois shards disjuntos com inventário e hashes estáveis. As duas falhas motivaram correções de deduplicação/continuação F13 e identidade de lock por run_id, seguidas de três testes dirigidos PASS67,44s. Restauração em execução, mídia/pins e PNGs:24 afetados PASS50,62s. Orçamento de mídia restaurado:2 afetados PASS45,03s. Fixture F16:12PASS157,78s. Os seis gates passaram em cada checkpoint. O full final675 da união, HEAD6144193, pertence ao coordenador e permanece pendente neste relatório.

Navegador verificou contagens reais, snapshots identificados, offline/retry preservando seis cards/contexto e exportação sem tráfego externo. `ui-evaluation.md` explicita as observações visuais e as jornadas ainda não integralmente executadas. Django e migrations passaram sem drift; harness quatro testes e verificador passaram.

O CLI calibrate direto falhou antes das medições por falta de inicialização Django na cadeia de import de FixtureSource. O wrapper de medição inicializa Django explicitamente sem alterar fonte congelada; também terminou exit1 na tentativa repetida de limpar destino já encerrado; nenhum calibration.json publicado. O resultado está em laboratory-checkpoint.md. O CLI fault completo e a matriz contratual continuam ausentes. Por isso a avaliação canônica permanece pending com pré-requisitos bloqueados; o contrato, plano e spec permanecem preliminares, F17 continua implementing e GARIMPEI_OPERATIONS_ENABLED continua falso. Não foi afirmado aceite parcial como done nem confirmação do perfil.


## Incremento de laboratório — 2026-11-13

`fault --case unit_persistent` injeta a terceira falha no cenário `recovery`/`backup` de uma instância eval própria, exige unidade com duas falhas e worker pausado, verifica suspensão e checkpoint, verifica outra unidade e recusa repetição. O relatório sanitizado registra duração e estados. O teste de integração usa lifecycle próprio e cleanup no `finally` (1 passou). Os seis gates Python passaram. A comparação com a mesma carga e todos os demais casos continuam ausentes; o perfil não foi confirmado, nem a avaliação integral executada.
