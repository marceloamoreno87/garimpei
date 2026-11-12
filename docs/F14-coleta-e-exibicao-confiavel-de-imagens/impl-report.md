# F14 — Relatório preliminar de implementação

Base3ce35d5, branch feat/F14-imagens-locais, worktree isolada. Implementados domínio de mídia, manifesto associado à observação, aquisição/miniatura independentes, quota/lease/fencing, galeria/versionamento, referências duráveis, retenção/tombstone, HTTP local com HEAD/ETag/304/410/503, recuperaçãoCSRF e galeria acessível integrada à publicaçãoF08. Extração limitada ao objeto identificado do anúncio, sem recomendações. Migrações0017/0018/0019 aditivas.

Validação preliminar: seis gatesPython aprovados;7testes de integraçãoPostgreSQL aprovados (incluindo mesmahash/fotos distintas, pins, quota, Retry-After, revisão, remoção e estoque ausente da busca);6testes unitários/transportes aprovados em rodada anterior;2regressões HTTPF05 aprovadas. Django/drift/estáticos/build/tokens executados; saídas em evidence/. A suíte completa está em execução, portanto não há aprovação global anunciada.

O navegador controlado confirmou originais1280×960 e1000×800 e miniaturas640px via URLs locais. A avaliação visual e o mapa completo do contrato serão finalizados após integração/prova da fonte. E2E-FONTE-01 permanece pendente: não foi usado perfil real nem copiada sessão nesta worktree. Relatório preliminar não declara done.
