# Orchestration Journal — F20 Compra, venda estimada e lucro na apresentação

**Run:** `2026-11-12T02-10-44Z`
**Branch:** `feat/F20-apresentacao-financeira`
**Started at:** 2026-11-12T02:10:44.019864+00:00
**Retry budget:** 3
**Status:** success

## Escopo
Implementação e avaliação locais, sem commits novos, merge, push, PR, deploy ou envio real. Ambiente eval wave11_f20, base bc1bc84.

## Cycle Log

| # | Kind | Status | Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | success | Fases4/4, gates/suíte aprovados | impl-report.md |
| 0 | evaluator | clean | P26 F0 B0 M0 S0; ACs8verificados | eval-report-2026-11-12T03-22-50Z.md |

## Cycle Detail

### Cycle 0
Preparação isolada; dependências F07/F08/F09/F12 done.

## Incremento de implementação — fases 1–3

- Regressão inicial: `pytest tests/unit/test_financial_presentation.py` retornou 1 (rótulo antigo e composição de outra identidade aceita). Corrigida fixture de condição para isolar comportamento; nova execução confirmou ambas falhas funcionais.
- Snapshot imutável FinancialSnapshot, validação Decimal/BRL/referências e congelamento junto à tentativa na transação existente. Corpo legado não é reescrito; tentativa sem corpo vai revisão; legado sem autorização volta somente à avaliação do evento existente.
- Migration `0013_alert_message_snapshot` sobre `0012_opportunity_collection`, aditiva. Branch F19 tem folha paralela independente; integração futura requer migração de merge, ainda fora do escopo.
- Publicações novas conservam ID da observação separado. Projeção confere identidade/observação/preço/moeda e avaliação do mesmo snapshot (ID/revisão/produto/valor). Formato pré-F20 decodifica a referência de observação já presente em sua composição, sem consultar estado corrente.
- Revisão externa readonly reportou dois defeitos confirmados: perda de valores em publicação pré-F20 e aceitação de referência de avaliação incompatível. Ambas regressões reproduzidas (exit 1) e corrigidas (seis testes F20, exit 0).
- `pytest tests/unit` no primeiro incremento: 200 passed, exit 0. Testes novos de revisão foram acrescentados depois.
- `node scripts/run-gates.mjs`: primeiros ensaios identificaram um erro de tipo e campos não utilizados; corrigidos usando versão de corpo no diagnóstico e conservando formatação legada para compatibilidade. Ensaio `.runtime/f20-gates-fourth.log`: seis grupos PASS, exit 0.
- `init.sh --disposable` da instância eval_wave11_f20: exit 0, web 23586, banco/volumes/segredos próprios. Aplicada nova migration com stop/init próprios: exit 0.
- Lab CLI em `/tmp/garimpei-f20-lab-aM0bMm`, instância eval_f04_99427d41b3, web 24311. Fonte e WAHA sintéticos, 42 ofertas filtradas, cinco comparáveis por produto, novo separado, leitura/falha/revisão controláveis. Primeiro ensaio misturou ofertas com comparáveis por condição declarada da massa; corrigida massa para conservar os cinco usados independentes, sem alterar regra do produto.
- Caso POSITIVO confirmado no lab com lucro 350 antes da navegação; navegador próprio f20 aberto. Integração transacional e evidência de UI em andamento.

Nenhuma avaliação canônica concluída nesta fase; status F20 permanece implementing.

### Verificação ampliada em andamento

- Teste de integração F20: `pytest tests/integration/test_financial_messages.py -q -s` exit 0, 1 teste/14,67s, com rollback, corrida de autorização, WAHA/reconciliação e variantes legadas.
- Teste HTTP dedicado: exit 0, 1 teste/13,35s, com 42 identidades/20-20-2, zero/negativo, referências separadas, indisponibilidade e 400/404/410/503.
- UI: capturadas lista/detalhe em 360/768/1440 e viewport CSS equivalente a zoom 200%. Primeiro ensaio CSS zoom não altera media queries como zoom de navegador; o ensaio final usa metade da largura CSS para representar zoom 200%, método registrado no log. Correções de container/reflow e tamanhos de valores eliminaram clipping observado.
- Jornada de configuração revelou uma explicação financeira antiga em region_fields.html; substituída pelo trio e removido link de erro para campo logístico invisível em form.html. Capturas finais serão refeitas após reinício próprio.
- Gates finais até este ponto: seis grupos PASS. Suíte completa de 335 testes iniciada; resultados pendentes.

### Verificação final do incremento

- Integração numérica F07→autorização→fake WAHA: exit 0,1 teste29,49s. POSITIVO350, ZERO0, NEGATIVO−50; primeiro alerta/redução; redução1200→1000 conserva compra1000 após nova observação900; taxa12,50%/12,63 e lucro18,37; seis POSTs sintéticos confirmados.
- Migração de esquema0012 com corpo/tentativa legados→0013: exit 0,1 teste14,57s; mesmos IDs/eventos/corpo/destino/tentativa, sem mensagem nova.
- Falha collection reproduzida: exit1, ProgrammingError campo financial ausente após teste F12 aplicar só0012 e usar modelo corrente. Teste adaptado para aplicar folhas atuais depois de validar cutoverF12. Regressões focadas collection+HTTP: exit 0,2 testes19,84s.
- Primeira suíte integral interrompida no processo próprio após as correções terem tornado o código importado desatualizado; saída preservada em .runtime/f20-pytest-full.log. Não foi aprovada e não fundamenta conclusão. Suíte integral atualizada em execução, saída .runtime/f20-pytest-final.log.
- Novas regressões de composição completamente ausente e componente obrigatório ausente: ambas reproduzidas e corrigidas; oito testes F20 passam (exit 0).
- Django check, migrations --check --dry-run, collectstatic, build sdist/wheel e tokens --check: todos exit 0.
- Browser: configuração concluída pelas três etapas sem logística; reaberta com CEP01001-000, câmeras e taxa10%; reinício próprio preservou valores. Lista A conservou composição/revisão/página2 durante falha503; clique após recuperação aplicou nova revisão no mesmo recorte e moveu foco conforme exploração.
- Método de zoom: viewport CSS equivalente a200%, sem alegação de zoom nativo. Medições reais de labels/valores/fontes/overflow em evidence/browser-layout-observed.txt.

### Recuperação adicional e diagnóstico da massa

Detalhe A manteve1000/1500/350 e sua revisão durante503, com erro visível; a recuperação mediante clique aplicou revisão posterior preservando contexto. FRACAO verificado no browser70/101/18,37 e taxa12,50%/12,63 sem overflow (evidence/fraction-browser-observed.txt). Composição incompatível e completamente ausente também foram exercitadas em HTML real legível, preservando compra900 e mostrando motivo explícito.

A revisão posterior do primeiro lab ficou sem venda: diagnóstico da massa confirmou os cinco comparáveis com preçoNone. A ação update do lab atribuía strings sem prefixoR$ exigido pelo parser, enquanto a factory inicial incluía o prefixo. Correção restrita ao lab para preservar formato de preço da fonte; a aplicação havia mantido indisponibilidade corretamente. Nova execução do lab será usada para a prova de composição B completa.

### Rodada congelada e avaliação

A suíte ampla anterior encerrou338PASS/1FAIL em1164,36s. O traceback em test_complete_snapshot_roundtrip_validates_components_and_provenance foi AttributeError schema_version: a classe havia sido importada antes do adendo de serialização enquanto a função codificadora foi importada depois. Alterar fontes durante o processo longo produziu mistura de versões; a execução falha não é aprovação. Saída integral e traceback preservados em evidence/broad-suite-mixed-imports.txt.

Congelados333 arquivos de fonte/teste/qualidade,10 arquivos novos e hash do diff620de463a84373ca9fb4cfe9ad107647e91634c47cc97e5e3ffd32d96f4f088d. Nova suíte integral exata em processo novo iniciada, sem novas edições de produto/testes até terminar. Hashes serão comparados no fim.

O adendo schema_version=1 é explícito e versões incompatíveis são rejeitadas. Nova regressão PostgreSQL comprovou que evaluation_revision=999 era aceita, embora os números fossem coerentes: FAIL15,01s. Correção confere avaliação imutável por ID/listing/revisão/produto/venda e configuração existente antes de autorizar corpo novo; o corpo já autorizado continua sem reconsulta. Três integraçõesF20 atuais PASS58,59 s; seis regressõesF09 atuais PASS217,37 s; oito unitáriosF20 atuais PASS0,04 s; seis gates214 módulos PASS.

E2E completo da mesma identidade: card/detalhe/corpoA1000/1500/350 com taxa10%/150 e schema_version1; reinício próprio e atualizaçãoB900/1600/380+20%/320 aplicada por clique. Snapshot/corpo/reciboA permaneceram idênticos e com uma tentativa; fake reteve dois POSTs de duas ofertas de preparo, sem novoPOST pelo recálculo. Artefatos e2e-*. Prova visual200% mantém o método equivalente de viewport CSS declarado.

## Final Verdict

**Status:** success
**Completed at:** 2026-11-12T03:22:50.153023+00:00
**Total cycles:**1 (1 implement-feature +0 fix-runner); cycles do progresso=0.
**Total commits across cycles:**0. Commit basebc1bc84 criado pelo coordenador antes da feature.

Avaliação canônica clean:26 PASS,0FAIL/BLOCKED/MANUAL/SKIPPED;8 ACs verificados. Relatório: docs/F20-compra-venda-estimada-e-lucro-na-apresentacao/eval-report-2026-11-12T03-22-50Z.md.

Suíte integral congelada:339 PASS em1133,04 s, exit 0. Seis gates Python214 módulos PASS; Django/migrations/estáticos/build/tokens/harness aprovados. Hash do diff620de463a84373ca9fb4cfe9ad107647e91634c47cc97e5e3ffd32d96f4f088d,333 arquivos e10 novos idênticos início/fim. Evidência em source-stability.json. Nenhum gate foi contornado; ensaios falhos anteriores permanecem preservados.

Browsers f20/f20setup fechados. Labs eval_f04_99427d41b3, eval_f04_0f8fe72603 e eval_f04_b0bd8b5f84 encerrados pelos scripts oficiais; baseline eval_wave11_f20:stop--clean exit 0. A suíte encerrou suas próprias instâncias. Somente lock desta execução será liberado no fechamento.

Limitações:zoom200% equivalente por viewport CSS, sem acionamento nativo; fonte/WAHA sintéticos; folhas0013 paralelas exigem merge de migration somente na integração futura autorizada. Código continua nesta worktree/branch sem commit/merge/push/PR/deploy.

Lock F20 liberado: processo proprietário encerrado e arquivo .runtime/F20.lock removido. Inventário final: nenhum container em execução com label deste checkout e nenhum manifesto com processos ativos.
