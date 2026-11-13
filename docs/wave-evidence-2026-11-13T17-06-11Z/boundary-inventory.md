# Inventário independente de fronteiras — base a73642d

Investigação somente leitura pelo agente boundary_inventory. Caminhos relativos a `apps/backend/src/garimpei/`; números indicam a base, não a versão final. Este inventário orienta a revisão e não declara implementação/aprovação.

| Etapa | Fronteira |
|---|---|
| Navegação F13 | `usecase/navigation/run_slice_usecase.py:82`, `run_suggestions_usecase.py:35/43`: cada busca e detalhe |
| Facebook | `infra/gateway/listing/facebook_marketplace.py:88/96/100`: reconstrução e continuação podem fazer duas páginas na mesma chamada |
| Pesquisa F18 | `usecase/valuation/run_research_usecase.py:64`: cada página/detalhe; `research_repository.py:245`: claim consome tentativa |
| Identificação F18 | `infra/repository/valuation/identity_repository.py:123/135`: reconciliação publica por anúncio; composição em `main.py:473` |
| Valoração F06 | `usecase/valuation/evaluate_usecase.py:13`; `infra/gateway/valuation/new_source.py:61`: cada URL em thread própria |
| Mídia F14 | `usecase/media/obtain_media_usecase.py:24/37/49/67`: claim, variantes, download e derivação |
| Avaliação F15 | `infra/worker/assessment_handler.py:40`: loop de dez; `prepare_assessment_usecase.py:27`, `assessment_media.py:31`, `assessment_inference.py:55` |
| Inferência F19 | `run_analysis_usecase.py:22–38`, `inference/postgres_repository.py:141`: permissão de cada parte; negativa conserva pending/tentativas |
| Alertas F09/F16 | `send_alert_usecase.py:35/40/43`, `alert/postgres_repository.py:211`: canal lento, autorização final e POST; retry seguro também é nova transmissão |
| Reconciliação | `reconcile_alert_usecase.py:12`: consulta no vínculo original e conclusão devem continuar durante pausa |

Ordem de locks: controle global antes da publicação `73003`, quota de mídia `140014`, controle da inferência e recursos/tentativas. Negativa não vira falha de fonte, backoff ou consumo de tentativa. Lease/heartbeat ausentes não comprovam término. Considerar autorizações legadas e `InferenceControl.active_request` no diagnóstico.

Pontos F21: `first_inputs.py:19` não fornece assinatura completa de mídia/análise; `message_authorization.py:12` retorna corpo congelado antes de outros checks; `first_authorization.py:20` já revalida observação/assinatura/prazo/composição sob publicação. Acrescentar assinatura própria e validade sem reconstruir corpo histórico.
