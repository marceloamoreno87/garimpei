# Revisão inicial das fronteiras de integração

Revisão independente somente leitura por integration_review, base master 8e94dab contra F17 aae6fce e interfaces F15/F18 em elaboração. Não substitui avaliação dos contratos nem revisão dos fixes finais.

## P1 — retomada de mídia após restauração

`infra/gateway/operations/snapshot_gateway.py` limpa `MediaJob.lease_until`, preservando `state=running`. A seleção `PostgresMediaRepository.due` exige `pending` ou `running` com lease vencido. SQL não seleciona NULL nessa comparação; o trabalho restaurado deixa de ser executado. Exigir regressão de snapshot com mídia em voo e retomada sem reiniciar o orçamento.

## P1 — retomada de inferência após restauração

O allowlist conserva `InferenceRequest/InferencePart` em execução, mas exclui `InferenceControl`, e a restauração não ajusta esses estados. O novo controle não conhece active_request; claim/reconcile não recuperam esse par. Exigir regressão com inferência em voo e continuidade limitada dos trabalhos.

Ambos encaminhados ao implementador F17 antes da integração final.

## Fronteiras da união

- SCHEMA deve conter ConditionAssessment, AssessmentHead, sete modelos de identidade/pesquisa e campos assessment_id/revision dos registros de decisão de alertas.
- O validador atual detecta modelos ausentes, mas não campos ausentes. Preservar exclusões privadas explícitas das seis colunas de sessão Facebook em IntegrationSettings.
- Conservar reconciliador F15 e execução F18 ao reunir worker com isolamento F17.
- Unir folhas aditivas das migrations; não renumerar migrations já aplicadas em outras worktrees.

Nenhum novo problema de privacidade ou destruição de dados foi confirmado nos caminhos auditados. Isso não é alegação de auditoria exaustiva.
