# F14 — Relatório preliminar de implementação

Base3ce35d5, branch feat/F14-imagens-locais, worktree isolada. Implementados domínio de mídia, manifesto associado à observação, aquisição/miniatura independentes, quota/lease/fencing, galeria/versionamento, referências duráveis, retenção/tombstone, HTTP local com HEAD/ETag/304/410/503, recuperaçãoCSRF e galeria acessível integrada à publicaçãoF08. Extração limitada ao objeto identificado do anúncio, sem recomendações. Migrações0017/0018/0019 aditivas.

Validação preliminar: seis gatesPython aprovados;7testes de integraçãoPostgreSQL aprovados (incluindo mesmahash/fotos distintas, pins, quota, Retry-After, revisão, remoção e estoque ausente da busca);6testes unitários/transportes aprovados em rodada anterior;2regressões HTTPF05 aprovadas. Django/drift/estáticos/build/tokens executados; saídas em evidence/. A suíte completa está em execução, portanto não há aprovação global anunciada.

O navegador controlado confirmou originais1280×960 e1000×800 e miniaturas640px via URLs locais. A avaliação visual e o mapa completo do contrato serão finalizados após integração/prova da fonte. E2E-FONTE-01 permanece pendente: não foi usado perfil real nem copiada sessão nesta worktree. Relatório preliminar não declara done.


## Fechamento após dois ciclos

Código final: e311eba após a fonte congelada a7e7469. Suíte completa congelada533PASS (shards222/311, zero skip/erro/duplicação,513 hashes iguais durante a execução); depois, apenas presentation.py mudou para corrigir rótulo de retenção. Esse delta passou regressão4casos, foco14testes e seis gates. Suplementos novos adicionais totalizam15testes (6integrações de falhas +4rede +4apresentação +1LEGADO com recibo confirmado fake), todos PASS. Inventário atual548; não foi declarado full548 nesta worktree. Django/drift/static/build/tokens aprovados novamente após delta.

Avaliação final em eval-report-2026-11-12T20-12-37Z.md:34PASS/1BLOCKED;6ACverificados/2indeterminados. Dois anúncios reais forneceram13originais com hashes/dimensões/carregamento local comprovados; permanece ausente prova de duas resoluções efetivamente oferecidas da mesma foto. Thumbnail nativa e imagem principal com mesmas dimensões naturais/URI não contam como variantes. Orquestração manual-pending, status implemented, nenhum done/waiver. Laboratórios e browsers desta execução parados; lock próprio liberado. Nenhuma mensagem WhatsApp real.
