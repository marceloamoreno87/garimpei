# F15 — correção 8, terceira da nova onda

O usuário aprovou explicitamente “Aprovar até1024 somente naF15”, referente à proposta `docs/wave-proposal-2026-11-13T15-51-31Z.md`. A canon foi registrada pelo coordenador no commit master b2688de. Este ciclo aplica esse escopo, sem editar os documentos canônicos nem mudar a referência e13/splits/política.

A prova física do perfil v2 confirmou truncamento nas duas chamadas controladas, fria/quente, em 512 tokens. A [reprodução anterior à mudança](evidence/wave2-profile-1024-red.txt) mostra que o gateway ainda reservava/aceitava o teto legado para F15.

A configuração finita está centralizada em `domain/inference/profile_limits.py`: legado `local-evidence-v1` usa 512; condição `condition-evidence-v3` usa 1024. Contexto total continua 4096. `InferenceSettings` recusa expansão global do contexto ou do teto legado. Assinatura de request, num_predict, validação de contagens e reserva de contexto usam o perfil; não há parâmetro externo arbitrário nem alteração do model-lock.

O preparador conserva o máximo textual 2048 e a folga visual anterior de 1536 (=4096−2048−512). Com saída1024, o texto multimodal F15 fica limitado efetivamente a1536, incluindo prompt/schema e margem256. Entrada que não cabe é recusada; nenhuma entrada é cortada. O envelope real também precisa satisfazer prompt_eval_count+1024≤4096. Uma imagem por chamada e derivados até512×512 permanecem. A [auditoria offline](evidence/wave2-profile-1024-budget.json) usa tokenizer oficial pinado e os23textos congelados: máximo1506, todos cabem com identidade vazia; o contexto real exato continua sujeito ao preparador e ao envelope. Isso não substitui recalibração GPU.

v3 altera prompt/const de versão e identidade de cache, mantendo schema estrutural estrito. v1/v2 permanecem identificados no histórico; jobs antigos são recusados antes do gateway/validador legado e nova avaliação recebe fingerprint/geração/request próprios. `condition-policy-v1` e autoria `ai_assisted`, ausência humana independente e hashes da referência permanecem.

Verificação:

- [50 testes unitários PASS](evidence/wave2-profile-1024-unit.txt), incluindo limites512/1024, fronteira4096, reserva visual/textual e telemetria segura de falhas.
- [14 integrações PASS](evidence/wave2-profile-1024-integration.txt), incluindo os sete casos F19 existentes e persistência/consulta da telemetria.
- [9 integrações adicionais do módulo final PASS](evidence/wave2-profile-1024-history-integration.txt), explicitando históricos v1 e v2 separados, sem somar execuções repetidas como testes distintos.
- [Seis gates Python PASS](evidence/wave2-profile-1024-six-gates.txt).

Cycles=8, três de três correções desta onda consumidas. Backend congelado neste checkpoint para revisão, recalibração/ensaio físico1024 e suíte completa coordenados. Sem novo ciclo de código por iniciativa própria. Nenhum sucesso visual, qualidade aprovada ou F15done é inferido desses testes controlados.
