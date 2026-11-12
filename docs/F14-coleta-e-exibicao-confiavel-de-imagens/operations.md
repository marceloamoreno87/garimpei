# F14 — Operação de mídia local

A obtenção usa fila PostgreSQL `media`, reconciliação independente a cada30s e uma transferência por ambiente. O original é imutável; miniaturaWebP é arquivo separado e pode ser refeita sem transferência. URLs candidatas ficam somente no estado privado; rotas de produto usam UUIDs locais.

## Armazenamento

O usuário aprovou **5GiB (5368709120bytes)** para a instalação real nesta execução. O coordenador aplica `GARIMPEI_MEDIA_BUDGET_BYTES=5368709120` na configuração privada principal durante integração. Sem valor positivo a aquisição fica suspensa; originais existentes continuam legíveis. A configuração não é gravada no Git.

`GARIMPEI_MEDIA_ROOT` deve ser diretório privado externo ao checkout. Padrão: `~/.local/share/garimpei/media/<environment_id>`, permissões0700 e arquivos0600. Nunca compartilhar raiz entre instâncias. Orçamento inclui arquivos, temporários e reservas; falta de espaço suspende novas transferências e conserva evidência protegida. O laboratório utiliza64MiB, reserva1MiB e arquivos até1MiB (limites deliberadamente reduzidos). Produção usa20MiB/arquivo e40Mpixel.

## Laboratório descartável

Da raiz:

```bash
uv run --project apps/backend --frozen --no-sync python apps/backend/scripts/media_lab.py prepare --output /tmp/garimpei-media-lab
uv run --project apps/backend --frozen --no-sync python apps/backend/scripts/media_lab.py inspect --manifest /tmp/garimpei-media-lab/manifest.json
uv run --project apps/backend --frozen --no-sync python apps/backend/scripts/media_lab.py stop --manifest /tmp/garimpei-media-lab/manifest.json
```

O preparo cria origem HTTP explícita de avaliação, configuração privada, instância descartável, corpus e casos. `init.sh --disposable` aplica migrations e comprova web/worker/PostgreSQL/WAHA; mensagens reais ficam sem configuração. O manifesto privado contém propriedade do servidor de origem e identificação do ambiente. `stop` confere PID/criação/comando e remove apenas a instância descartável própria. O corpus é sintético e não comprova a fonte real.

## Recuperação e retenção

O formulário solicita outra geração respeitando a próxima tentativa, sem baixar na web. A versão antiga continua referenciada pela observação original; captura nova não substitui fotos de uma revisão já aberta. Falhas transitórias têm tentativa inicial +3repetições em15/60/300s, respeitando Retry-After maior, inclusive HTTP-date. Arquivo inválido aguarda ação/nova evidência; CDN403/404/410 não significa anúncio removido.

Backfill cria manifestos desconhecidos para até5observações legadas por rodada e agenda o ciclo de coleta existente, com espera mínima300s por oferta. `PostgresCollectionRepository.detail_targets()` inclui correspondências históricas dos interesses mesmo quando o anúncio não reaparece na busca. F13 usa esse conjunto na frente de investigação; nenhum segundo perfil é criado. A regressão `test_legacy_detail_backfill_does_not_require_search_rediscovery` confirma busca vazia +detalhe acessível +cópia900px sem descoberta adicional e com escolha manual preservada.

`media_tracking_active` começa verdadeiro para todas as ofertas, inclusive legadas. Ausência em busca,48h ou foto nova não desprotegem arquivos. Uma referência durável também protege a versão. Limpeza requer ambas as proteções ausentes; marca remoção antes de unlink e conserva tombstone410 com hash/origem/datas. Somente a factory de avaliação prepara ofertas não acompanhadas; F14 não oferece ação de deixar de acompanhar.

## Consumidor F15 e backup F17

- `ReadMediaGalleryUseCase.execute(listing_id,observation_id,expected_revision=None)` retorna galeria sanitizada exata; revisão incompatível retorna409.
- `AcquireMediaForAnalysisUseCase.execute(listing_id,observation_id,version_id,consumer,execution)` confirma pin antes de leitura. Repetição ativa é idempotente; referência liberada não é reativada silenciosamente.
- `ReleaseMediaReferenceUseCase.execute(reference_id)` libera explicitamente e preserva histórico.
- `PostgresMediaQueries.file(...,'original'|'miniatura')` e `build_media_store().read(file)` fornecem bytes exatos com hash validado, sem revelar caminhos ao consumidor público.
- F17 pode chamar `build_media_repository().protected_versions(execution,now)` para enumerar e adquirir pins de backup atomicamente. Deve copiar originais/derivados e metadados, verificar hashes e liberar pins explicitamente ao concluir/abortar; a existência desta fronteira não comprova integração do backup.

Não publicar manifesto privado, URLs assinadas, cookies, QRcode ou fotos identificáveis em relatórios. A prova real precisa de dois anúncios distintos e variantes comprovadas, coordenada pelo proprietário do perfil.
