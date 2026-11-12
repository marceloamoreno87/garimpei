# Regressões integradas de exploração — F08/F18

Base: `6c315ca56b97a09cf0e40f817a972922e248e6ea`. Branch: `fix/integrated-exploration-regressions`. Worktree isolada `6cd6`; nenhuma alteração no candidato congelado `a716`, na instalação principal ou no perfil Facebook. Testes usam PostgreSQL e fonte/canal loopback próprios.

## Causas e correções

A fixture antiga descrevia uma câmera no título e um PlayStation ou iPhone no corpo. O reconhecimento F18 recusava corretamente essas famílias conflitantes, impedindo a publicação esperada de lucro. Câmeras agora descrevem corpos Sony A6000; CAM05 descreve A6300 com cinco referências próprias e sem oferta de novo; CAM42 mantém modelo ausente e estimativa indisponível. Fones descrevem JBL Tune 520BT. Comparáveis e oferta sintética de novo correspondem à mesma identidade suportada. IDs, preços, recortes, ordem e assertivas financeiras foram preservados.

A projeção passou a realizar 11 consultas após acrescentar a busca de IdentityProgress. [A reprodução](projection-before.txt) manteve os mesmos Offer completos mas ultrapassou o orçamento de dez. A consulta existente de anúncios agora carrega a identidade manual e sua observação; o mapa é entregue explicitamente à consulta de valoração. Chamadores sem esse mapa conservam a busca em lote anterior. A regressão inclui revisão manual999, observação e horário de proveniência, e continua exigindo até dez consultas, sem recarga tardia dos JSONs do ciclo.

Depois dessas correções, quatro dos cinco testes focais passaram. O teste de custos revelou outra corrida: editar a taxa inicia coleta por mudança da revisão de configuração. A referência20003 permanecia em1700, com observação2, quando o teste já aguardava lucro376 correspondente a1720; o lucro publicado era360. O [diagnóstico de dados](source-mutation-diagnostic.json) mostra que a rodada aguardada continha preços anteriores à mutação da fonte. A sincronização agora conclui o ciclo2 da configuração antes da alteração e aguarda o ciclo3 depois da mutação e avanço do relógio controlado. Nenhum timeout, valor esperado ou regra do produto foi alterado.

## Verificação

- Seis gates Python: exit0, [gates.txt](gates.txt), depois da sincronização final do teste.
- Projeção/MVCC: três testes PASS no lote inicial; cobertura de snapshots coerentes, exclusão dos cinco JSONs, orçamento até10 e identidade manual999.
- Exploração/paginação: primeiro teste PASS no mesmo lote;52 resultados, IDs/ordem/páginas, lucro530→830, congelamento de revisões, mudança manual, histórico e remoção da origem.
- Custos/referências/concorrência: após corrigir a sincronização, teste completo PASS em48,50s, [costs-after.txt](costs-after.txt); preservadas as verificações de530→360→376, referência1720, eventos, consumidores e expiração.
- O [lote anterior](initial-targeted-summary.txt) registra4PASS/1FAIL em171,50s antes da sincronização. A conclusão combina essas quatro verificações ainda válidas com a reexecução verde do teste alterado; não declara um lote único5PASS nem uma nova suíte completa.
- Ruff e `git diff --check` sem erro; temporários e dumps de diagnóstico ficam em `.runtime/regressions/`, fora do versionamento. O hook temporário de diagnóstico foi removido.

A verificação completa da união posterior e a integração na master pertencem ao coordenador. Este commit não conclui as pendências externas/manuais de F14/F15/F18.
