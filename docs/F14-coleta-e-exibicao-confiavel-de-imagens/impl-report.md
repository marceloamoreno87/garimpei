# F14 — Relatório preliminar de implementação

Base3ce35d5, branch feat/F14-imagens-locais, worktree isolada. Implementados domínio de mídia, manifesto associado à observação, aquisição/miniatura independentes, quota/lease/fencing, galeria/versionamento, referências duráveis, retenção/tombstone, HTTP local com HEAD/ETag/304/410/503, recuperaçãoCSRF e galeria acessível integrada à publicaçãoF08. Extração limitada ao objeto identificado do anúncio, sem recomendações. Migrações0017/0018/0019 aditivas.

Validação preliminar: seis gatesPython aprovados;7testes de integraçãoPostgreSQL aprovados (incluindo mesmahash/fotos distintas, pins, quota, Retry-After, revisão, remoção e estoque ausente da busca);6testes unitários/transportes aprovados em rodada anterior;2regressões HTTPF05 aprovadas. Django/drift/estáticos/build/tokens executados; saídas em evidence/. A suíte completa está em execução, portanto não há aprovação global anunciada.

O navegador controlado confirmou originais1280×960 e1000×800 e miniaturas640px via URLs locais. A avaliação visual e o mapa completo do contrato serão finalizados após integração/prova da fonte. E2E-FONTE-01 permanece pendente: não foi usado perfil real nem copiada sessão nesta worktree. Relatório preliminar não declara done.


## Fechamento após dois ciclos

Código final: e311eba após a fonte congelada a7e7469. Suíte completa congelada533PASS (shards222/311, zero skip/erro/duplicação,513 hashes iguais durante a execução); depois, apenas presentation.py mudou para corrigir rótulo de retenção. Esse delta passou regressão4casos, foco14testes e seis gates. Suplementos novos adicionais totalizam15testes (6integrações de falhas +4rede +4apresentação +1LEGADO com recibo confirmado fake), todos PASS. Inventário atual548; não foi declarado full548 nesta worktree. Django/drift/static/build/tokens aprovados novamente após delta.

Avaliação final em eval-report-2026-11-12T20-12-37Z.md:34PASS/1BLOCKED;6ACverificados/2indeterminados. Dois anúncios reais forneceram13originais com hashes/dimensões/carregamento local comprovados; permanece ausente prova de duas resoluções efetivamente oferecidas da mesma foto. Thumbnail nativa e imagem principal com mesmas dimensões naturais/URI não contam como variantes. Orquestração manual-pending, status implemented, nenhum done/waiver. Laboratórios e browsers desta execução parados; lock próprio liberado. Nenhuma mensagem WhatsApp real.

## Retomada — 2026-11-13T02-35-56Z

Implementação existente preservada; não se reproduziu defeito de código nem se executou nova implementação. A avaliação parcial atual está em `eval-report-2026-11-13T02-35-56Z.md`: E2E-FONTE-01 BLOCKED, 34 itens SKIPPED. Auditoria do registro sanitizado mais recente encontrou 44 fotos de oito anúncios, nenhuma com duas dimensões distintas comprovadas. Gates/testes e jornada real não reexecutados; resultados históricos acima não constituem aprovação desta rodada. Para resolver o bloqueio, é necessária amostra real nova com variantes comprovadas, comparação entre bytes recebidos/conservados e carregamento local na lista/detalhe/ampliação.

## Avaliação real — 2026-11-13T12-24-34Z

Amostra do usuário destravou variantes261×261/540×960 da mesma foto.9originais/9miniaturas locais verificados, entrada para análise e ampliação preservamSHA.35regressões e6gatesPASS;8jornadasUI e35itens contratuaisPASS. Implementação sem mudanças. Relatório `eval-report-2026-11-13T12-24-34Z.md`.
