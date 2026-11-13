# F15 — Ciclo3: diagnóstico da resposta rejeitada

Itens: `WRK-FALHA-01`; avaliação prévia BLOCKED e regressão desta retomada FAIL.

Causa reproduzida: a resposta de inferência é corretamente rejeitada por F19, mas `_resolved` usa sempre o motivo da política de condição. Sem declaração positiva, o motivo `function_not_declared` substitui `invalid_analysis`, ocultando a causa técnica. Quatro variantes persistidas reproduzem `('failed', 'function_not_declared')`: chamada de ferramenta, JSON inválido, citação fabricada e foto inexistente. Evidência: `evidence/retomada-hostile-red.txt`, exit1,4FAIL/4deselected; fixture já corrigida antes desta reprodução.

Correção mínima: conservar o motivo técnico recebido quando status é `failed`. A política continua calculando a condição automática, incluindo defeito textual independente; o diagnóstico de falha não é prova de funcionamento. Nenhuma mudança de política, schema, modelo, pins ou gate.

Regressão: texto e foto hostis sintéticos passam pelo download/registro F14, preparação F15 e preparador/gateway/validação/publicação F19. Somente o transporte de inferência é controlado; tokenização real foi verificada com tokenizer oficial pinado já disponível. O teste automatizado sem cache controla apenas contagem de tokens, descrito na fonte. Nenhum modelo/GPU ou corpus humano foi executado.

Validação final é registrada no novo eval-report desta retomada; histórico `cycles=2`→`3` reflete uma correção real. Até três correções novas autorizadas; consumida uma.
