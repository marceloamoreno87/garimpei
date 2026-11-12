# F06 — Operação das avaliações

Execute o lifecycle conforme F02 e aplique a migration aditiva `0006_valuation` com `./scripts/migrate-dev.sh --apply` antes de reiniciar os processos. O worker usa as filas `runtime,listing,valuation`. Não há endpoint HTTP ou interface nova nesta feature.

A cada dois segundos, o reconciliador lê observações confirmadas de F04 sob o mesmo lock de publicação, captura o recorte imutável e persiste necessidade de trabalho e enqueue na mesma transação. A fila Procrastinate do PostgreSQL processa o recorte fora da transação, consulta novo e publica resultado/evidências atomicamente. Uma revisão superseded não substitui a mais recente. Uma falha de gravação conserva a versão anterior e deixa diagnóstico `valuation_publication_failed`, com nova tentativa após cinco segundos. Lease de 60 segundos permite reenfileirar após interrupção. O trabalho confirmado sobrevive à parada normal.

Consumidores F07/F08:

```python
from garimpei.main import build_read_valuation
reader = build_read_valuation()
current = reader.execute(listing_id)  # UUID F04; None somente se desconhecido
historical = reader.execute(evaluation_id, historical=True)
```

O retorno tipado identifica oferta, avaliação (None enquanto pendente), revisão F06, revisão F04, instante, método `median-brl-v1` e BRL. `resale.price` é Decimal ou None; `resale.reason`, contagens e `comparables` sustentam o resultado. Cada comparável conserva identidade da fonte, URL, título, preço anunciado e instante. `new` tem estado e cotação separados. Não há campo de lucro. Leituras usam somente PostgreSQL, nunca acionam rede. Validade é inclusiva em UTC; consulta atual oculta valor vencido ou identificação alterada enquanto aguarda trabalho. Histórico por ID preserva o resultado original.

O preço de compra continua na F04. Alteração exclusivamente desse preço não muda a base de revenda da própria oferta; alterações nos demais comparáveis podem mudar essa base. Falha de coleta não gera uma amostra vazia, e `origin_diagnostic` sinaliza falha persistente. A classificação manual da F05 não é alterada nem usada para certificar funcionamento de comparáveis.

A identificação inicial suporta as famílias verificadas PS5 e iPhone 12/13 com os atributos exigidos em `phase-1.md`. Atributos ausentes/ambíguos, outras famílias e edições não identificadas geram produto indeterminado. Anúncios e sua condição continuam preservados.

Fonte de novo: catálogo explícito `infra/gateway/valuation/retail_catalog.json`, inicialmente um SKU KaBuM!, PS5 Slim/disco/1TB. Cobertura e prova em `phase-1.md`; a ausência no catálogo significa ausência nessa cobertura, sem promessa sobre outras lojas. Chromium lê o documento público, BRL e disponibilidade; nenhuma conta varejista ou chave é necessária. Consultas têm timeout de 30 s e intervalo de 2 s por página. Falhas usam backoff 60/300/900 s, depois 3600 s; cotações válidas podem ser conservadas por até sete dias. Não confundir ausência com falha, nem cotação anunciada com venda.

Teste: `GARIMPEI_VALUATION_FIXTURE_URL` aceita somente instância eval e origem HTTP loopback com porta explícita. A fonte programável de `tests/factories/valuation.py`, o relógio F04 e `tests/fixtures/valuation/cases.json` exercitam dados, falhas e passagem do tempo. URLs exemplo.invalid e IDs Facebook sintéticos dessa fonte não provocam acesso real ao Marketplace. Segredos seguem o arquivo privado F02, nunca os relatórios.

Reprodução de mercado: `phase-1.md` distingue navegação real dos adapters e replay determinístico posterior desses registros pela coleta/worker reais. O replay conserva preços e IDs externos e registra seu instante de confirmação F04, distinto dos instantes de navegação originais. Não é anunciado como nova coleta de mercado ao vivo.
