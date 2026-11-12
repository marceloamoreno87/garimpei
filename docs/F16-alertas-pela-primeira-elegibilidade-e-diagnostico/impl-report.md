# Implementação F16

Worktree `34bb/garimpei`, branch `feat/F16-primeira-elegibilidade`, base `c8ca8ae79d5a9760a251e14931db4cbc2549b594`. Implementação e três correções concluídas; avaliação final clean: 39 itens PASS e 6 ACs verificados. Commit local autorizado pelo usuário ao final; integração, push, PR e deploy ficam sob o coordenador.

## Fases e resultado

1. Regras/corpus: prazo inclusivo de 48h sobre publicação absoluta com proveniência da mesma evidência; ausência/duvidosa/futura distintas; lucro positivo/zero/negativo. Escolha manual consome assinatura semântica persistente e não dispara fila. Entrada automática independente reavalia com precedência manual. Corpus TypedDict valida identidades, comparáveis, valores, datas, legado e quedas antes de I/O.
2. Persistência/adoção: migration 0015 depende exclusivamente de 0014 merge F19/F20. `FirstAlertInventory` mantém cursor e conclusão; `FirstAlertIdentity` é única por instalação/listing e mantém assinatura/manual_signature/generation/next_action/estado/motivo/intenção; `FirstEligibilityDecision` registra observação, revisão da condição, causa, assinatura, publicação/proveniência, composição e horário imutáveis por geração. AlertIntent aceita origem primeira decisão ou evento. Executor sobre banco preenchido preserva101 legados e retoma100 + 1 sem consulta externa; despacho aguarda conclusão.
3. Reavaliação/envio: portas explícitas/usecases adopt/refresh/read; hooks transacionais de coleta/valoração e varredura periódica; F07 primeiro event=False, redução event=True. Autorização revalida imediatamente após check lento do canal, inclusive validade dos comparáveis. Snapshot financeiro v2 tem event_id=null sem fabricar ListingEvent; v1, eventos e legado e corpos autorizados preservados. Tentativa causal durável permite recibo tardio sem sobrescrever geração nova. Binding original acompanha reconciliação de ambas origens. Intenção comprovadamente não transmitida incompatível encerra com motivo e pode ganhar sucessora na mesma identidade; uncertain/confirmed não recebem segundo POST.
4. Diagnóstico/UI: DTO público tipado, sem I/O externo ou reavaliação, falha técnica distinta de ausência. Lista/detalhe preservam versão/filtros/valores; separação de impedimento atual e recibo histórico; rótulos PT, datas/ressalva e retry no próprio bloco. Identidade indeterminada não é rotulada como variante divergente. Navegação 1440/360, teclado/foco/overflow/falha parcial e mesmo detalhe após restart têm evidência visual examinada.
5. Integração/prova: fonte HTTP→worker→WAHA fake→recibo→restart→mesma identidade/grupo/referência/detalhe; prova externa única especificamente autorizada, com confirmação técnica ACK2 e observação humana separadas. Nenhum Facebook autenticado, IA ou GPU foi usado.

## Arquivos e coordenação

- Domínio: `domain/alert/{first_eligibility,first_ports,diagnostic}.py`, Delivery.attempt_id e FinancialSnapshot v2; Evidence.published_at_source compatível.
- Usecases: `usecase/alert/{adopt_first_alerts,refresh_first_eligibility,read_alert_diagnostic}_usecase.py`, reconciliação original.
- Persistência/repositórios: `alert_models.py`, migration 0015, `repository/alert/{first_inputs,first_financial,first_authorization,first_alert_repository,delivery_state,postgres_repository,financial,message_authorization}.py`, condição manual, mapper/proveniência.
- Consulta/UI: `queries/alert/diagnostic_queries.py`, apresentação/listing, handlers/projeções/templates e estágios worker.
- Gateway: fix mínimo WAHA usa helper canônico existente para JID de dispositivo, após RED público; corpo/conta/grupo/fromMe/ACK mantêm exigências estritas.
- Factories/fixtures/testes: cenários F16 isolados, fronteiras/corridas/migrations/recuperação/HTTP; regressões antigas só adaptadas quando premissa F16 explicitamente substituída. Lookup F10 agora cobre ambas origens e mantém corpo/financeiro/grupo anteriores. Reduções continuam por evento; rollback, ACK/fencing, reconciliação e formatos legados permanecem asserts.
- Fronteiras comuns foram aplicadas exclusivamente pelo coordenador: composição/main, registros models, scheduling/runworker, hooks listing/valuation, fixture_source, consolidation e registros quality. Não foram editados adapters Facebook ou portas pertencentes à F13.

## Verificações e histórico

`eval-report-2026-11-12T13-49-00Z.md` preserva avaliação inicial fail:117 PASS/1 FAIL,exit2,420hashes e divergência da janela F09 em WRK-REDUCAO-04. Correção1/3 trata seleção temporal da intenção anterior, lookup F10 e clareza de identidade ausente. Nenhuma rodada interrompida recebeu aprovação.

`evidence/coverage-closure.md` mapeia G1–G9. Rodadas focais:34 PASS/3 FAIL iniciais preservados,9 PASS e 8 PASS finais; união de 38 casos. Os FAIL de preparo foram corrigidos sem remover asserções de negócio. RED/GREEN da janela e da identidade ausente estão preservados. Seis gates backend, Django, drift, build wheel e harness 4 testes/estrutura passaram (exit0) nos logs `evidence/f16-audit-closure-gates.log` e `evidence/f16-final-*.log`.

A suíte final concluiu 449 PASS, zero falhas, exit0, em 1777,54s. Os 431 inputs before/after são idênticos: nenhum changed/added/removed. O relatório `eval-report-2026-11-12T16-16-18Z.md` avalia cada then dos 39 itens e projeta os 6 ACs: clean. Progresso F16 atualizado atomicamente para done, cycles=3; relatórios fail anteriores preservados.

## Operação e limpeza

Laboratórios fake pertencem às factories e foram limpos. Labs UI e sessões Chromium foram fechados. O ambiente real próprio 20411 foi encerrado normalmente, exit0, preservando banco, volumes e sessão pareada. Antes da parada: alertas false, ACK2, uma tentativa, corpo/hash/vínculo originais e zero intenções incertas; o worker próprio foi verificado e retomado somente para shutdown. A fonte sintética foi fechada e os drivers temporários de diagnóstico removidos. Nenhuma mensagem adicional foi transmitida. Segredos e identificadores privados completos ficam somente DB/.runtime; evidências públicas usam hashes/booleanos/counts. `operations.md` detalha retomada, adoção e encerramento.

A avaliação do ciclo1 também está preservada como fail(gate):54PASS/1FAIL,431hashes before/after idênticos. A correção2 altera exclusivamente o preparo temporal da regressão financeira: respeita next_action persistido com worker pausado e relógio controlado; não altera produção nem garantias event1000/latest900/valores/corpo/6POST. Ver `fix-report-cycle-2.md`.3 financeiros PASS e trio final PASS, todos os gates/checks novamente exit0.

A avaliação do ciclo2 concluiu448PASS/1FAIL com431hashes estáveis; o unit antigo de schema revelou combinação v2/evento aceita. A correção3 mantém essa rejeição, fecha v1/evento versus v2/None no domínio e acrescenta roundtripv2 e versão3 desconhecida.12 focais e seis gates/checks/build/harness PASS. Ver `fix-report-cycle-3.md`; o full final passou e está em `eval-report-2026-11-12T16-16-18Z.md`.

## Entrega final

- 449 testes PASS/exit0; seis gates, Django, drift, build e harness exit0. Wheel contém política, caso de uso, migration e template F16.
- 39 itens PASS/6 ACs verificados; correções3/3, sem pendência contratual. Prova real única:1POST/1attempt/ACK2, observação do usuário separada; nenhuma repetição.
- `evidence/f16-final-{before,after,integrity,result}.json` e `f16-final-full-suite.log` preservam a execução final. Logs públicos recebem somente remoção de ANSI/espaços finais; originais permanecem privados em .runtime.
- `evidence/privacy-scan.json`, `normal-stop-preflight.json` e `cleanup-final.json` documentam sanitização e limpeza própria. Conta/pareamento preservados; principal não foi tocada por esta execução.
- Lock exclusivo desta execução liberado após conclusão. Commit local autorizado; sem push/merge por este agente.
