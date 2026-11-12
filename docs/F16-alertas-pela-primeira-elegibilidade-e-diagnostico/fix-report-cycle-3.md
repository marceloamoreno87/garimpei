# Correção 3 — origem do snapshot financeiro

Entrada: `eval-report-2026-11-12T15-09-59Z.md`. Última correção do orçamento: 3 de 3. A rodada anterior concluiu449testes com448PASS/1FAIL,exit1;431hashes before/after idênticos. Todas integrações/lifecycle/quality passaram, mas o gate global continuou falho.

O unit existente exigia rejeitar o payload v1 de evento quando marcado como schema_version2. O domínio permitia essa combinação embora já declarasse v1 como evento e v2 como primeira elegibilidade; prepare_first já recusava event_id não nulo. O ajuste fecha a mesma invariável na entidade: v1 exige evento e v2 exige event_id=None. Causalidade de queda fica no registro próprio. Não muda JSON, formato, corpo, vínculo ou snapshot autorizado já persistido.

A assert antiga foi preservada. Acrescentaram-se roundtrip válido v2/None, rejeição v1/None e rejeição explícita da versão3. RED:1FAIL/7PASS. Após a condição adicional no domínio, GREEN:8PASS. Focal completo:12PASS/95.04s, incluindo três integrações financeiras com legado/eventos e o percurso normal de primeira elegibilidade com restart. Seis gates, Django, drift, wheel e harness passaram com exit0.

A reavaliação final terá novo freeze e full449. Até seu exit0 e hashes before/after estáveis, permanece sem done. Nenhuma mensagem ou operação real será repetida.
