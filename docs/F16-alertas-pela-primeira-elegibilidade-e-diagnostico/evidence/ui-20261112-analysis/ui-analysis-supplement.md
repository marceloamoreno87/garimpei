# F16 — Suplemento de apresentação de espera por análise

Executado em 12/11/2026, aproximadamente 13:11–13:13 UTC, com `playwright-cli` e inspeção visual segundo `frontend-ui-design`. Complementa exclusivamente UI-DIAGNOSTICO-01; não é avaliação canônica nem conclusão da feature.

Novo laboratório descartável criado por `first_eligibility_scenario(private, enabled=False)`: instância `wave11b_f16_4c489387`, banco `garimpei_eval_wave11b_f16_4c489387`, porta web 11646, sessão exclusiva `f16-ui-analysis-owned`. Fonte/WAHA em loopback, IA desativada, worker somente desse laboratório pausado. Nenhum acesso à instância real 20411.

Foi persistida uma **fixture de apresentação**, sem criar intenção ou tentativa: decisão atual `analysis_pending`, estado `waiting`, horário da avaliação `2026-11-12T12:00:00Z`. A consulta pública `build_read_alert_diagnostic().execute(...)` retornou:

- `reason` e `current_reason`: `analysis_pending`;
- `label` e `current_label`: **Aguardando análise das fotos**;
- `first_alert_state`: `not_sent`;
- `evaluated_at`: horário acima, sem efeitos de envio.

Esse seed e o DTO **não representam um produtor F15 implementado**, chamada de IA, análise de imagem concluída ou disponibilidade de GPU. Verificam a apresentação F16 de uma entrada futura equivalente.

O detalhe real respondeu HTTP 200. As capturas [desktop](01-analysis-desktop.png), [360 px](02-analysis-mobile360.png) e o [snapshot](01-analysis-desktop.snapshot.md) foram examinados: motivo legível, data explícita e prazo separados do rótulo principal, sem clipping ou overflow horizontal. A [observação do navegador](03-browser-observation.txt) registra viewport 360 × 900 e `overflow=false`.

Antes/depois do seed, leitura pública, navegação e reload: **zero intenções, zero tentativas, zero POSTs, zero mensagens e zero chamadas ao fake**. Arquivos `result-baseline.json`, `result-analysis-seed.json` e `result-after-get.json` comprovam os contadores e campos públicos. Não foi executada suíte nem alterado código/teste/progresso.

A lacuna de apresentação `analysis_pending` no relatório anterior fica suprida por esta evidência sintética. Mantêm-se as limitações de produção F15/IA e dos E2Es integrais descritas no relatório principal. A nota visual anterior não foi recalculada: o suplemento reutiliza o mesmo componente, sem nova direção de design.

Encerramento exclusivo do novo laboratório, remoção de seus recursos e fechamento da sessão são registrados em `cleanup.json`.
