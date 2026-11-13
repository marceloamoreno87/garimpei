# F15 — correção 7, segunda da nova onda

Revisão independente do checkpoint b3ae496 identificou P2 confirmado: `_validated_envelope` voltava a inserir duração/contexto brutos depois da filtragem inicial. Um envelope `done=stop`, contagens válidas e métricas opcionais contendo string/objeto podia atravessar o gateway; se o JSON de conteúdo fosse rejeitado depois, a telemetria persistida carregava esses valores.

A [regressão antes da correção](evidence/wave2-metric-sanitization-red.txt) reproduz seis variantes: string, null, bool, negativo, overflow e infinito. A mudança mínima reutiliza as mesmas listas de campos numéricos e valores inteiros não negativos menores que 2**63 para métricas do envelope e da residência. Valor ausente/desconhecido é omitido, sem fabricar zero. Não altera schema de análise, prompt, caps, pins ou política.

Verificação atual:

- [34 unitários PASS](evidence/wave2-metric-sanitization-unit.txt), incluindo envelope aceito com conteúdo inválido e métricas malformadas.
- [7 integrações PostgreSQL PASS](evidence/wave2-metric-sanitization-integration-corrected.txt), incluindo HTTP controlado real → gateway aceita envelope → caso de uso rejeita JSON → consulta pública sem canário/conteúdo bruto. As proteções de rejeição e histórico v1/v2 permanecem verdes.
- [Seis gates Python PASS](evidence/wave2-metric-sanitization-six-gates.txt).
- A primeira rodada integrada preservada em [wave2-metric-sanitization-integration.txt](evidence/wave2-metric-sanitization-integration.txt) teve 13 PASS e uma falha de preparação no novo teste: faltava cohort obrigatório do perfil F15. O fixture foi corrigido com identidade/geração explícitas antes da execução final. As sete integrações F19 existentes passaram nessa primeira rodada; não se somam contagens como nova suíte completa.

Correção 7 = segunda de três autorizadas nesta onda; histórico cycles=7. Backend será congelado neste commit. Avaliação física/full permanecem separadas. O par físico v2 coordenado no checkpoint anterior continuou length/512; esta correção de filtragem não pretende resolver truncamento. Nenhum aumento de limite é aplicado sem autorização explícita e canon correspondente.
