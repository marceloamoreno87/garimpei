# F07 — Consultas de lucro

A feature deriva a composição na leitura. Não cria tabelas, migrations, jobs ou endpoints. Reutiliza configuração confirmada de F03, observações/eventos de F04 e avaliação atual de F06. Lifecycle e segredos seguem F02.

```python
from garimpei.main import build_read_profit

reader = build_read_profit()
current = reader.execute(listing_id)  # UUID F04
for_event = reader.execute(event_id, event=True)  # discovered ou price_decreased
```

`None` significa identidade inexistente. Evento de outro tipo lança `UnsupportedProfitEvent`. Uma oferta conhecida pode devolver composição com valores indisponíveis, incluindo motivos, sem fabricar zeros. Falha de leitura lança `ProfitReadFailed`, código `PROFIT_DEPENDENCY_UNAVAILABLE`, `retryable=True`, sem composição. O log JSON identifica evento `profit_read_failed`, código e UUID; não inclui CEP nem detalhes privados.

`ProfitComposition` é um DTO imutável com Decimal em BRL, instante UTC, IDs de anúncio/observação/evento, configuração e revisão, avaliação e revisão, política `profit-brl-v1`, componentes com estado/origem e composições por modalidade. `principal`, `profit` e `freight` representam retirada prioritária, seguida de envio, somente quando confirmados pela F04 para o escopo vigente. `modalities` conserva as alternativas. Percentual conhecido continua disponível mesmo sem revenda. `shipping_freight` conserva o frete aplicável/conhecido ou estimado mesmo sem modalidade confirmada; isso não torna o lucro calculável. `excluded_costs` e `resale_scope` explicam que deslocamento, reparo, embalagem, impostos e frete de revenda não entram na estimativa de uma unidade funcional equivalente.

A F08 pode reler a avaliação **histórica pelo `evaluation_id`** para exibir os comparáveis exatos. A F09 deve capturar valores e referências da composição ao registrar sua decisão; outra consulta usa configuração e avaliação vigentes e pode mudar o resultado. A observação do evento continua fixa.

As consultas abrem uma transação PostgreSQL `REPEATABLE READ` para todas as dependências e usam um único instante. Devem ser chamadas fora de uma transação ou dentro de uma transação externa que já seja `REPEATABLE READ`/`SERIALIZABLE`. Transação externa `READ COMMITTED` recebe falha explícita e repetível; não altera silenciosamente o isolamento do consumidor. Conflitos de banco são convertidos na mesma falha de dependência.

## Reprodução descartável

Na raiz:

```bash
uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests/unit/test_profit.py apps/backend/tests/integration/test_profit.py -v -s
```

Cada teste integrado inicia `init.sh --disposable`, verifica manifesto e `/health/ready` 200, prepara segredos privados próprios, PostgreSQL/WAHA e worker. As factories de F03 configuram custos e interesse; `profit_rows()` em `tests/factories/valuation.py` alimenta o coletor real F04 pelo adaptador HTTP loopback de teste. O worker F06 calcula as avaliações usadas. Os dados vêm de `tests/fixtures/valuation/cases.json`, seção `profit`: cenário 699 é OFERTA, 700–709 são variações, comparáveis 600–604 e 800–804. Anúncios sintéticos com defeito não entram na amostra de revenda; a própria condição da oferta é preservada. Datas usam o relógio controlado F04.

Os UUIDs são obtidos por `Listing.objects.get(external_id='699')`, `latest_id`, `ListingEvent.objects.get(listing=..., kind='price_decreased', observation__price=Decimal('1500'))` e `build_read_valuation().execute(listing.id).id`. O teste REDUCAO publica 1550 → 1500 → 1450 pelo coletor; há também estado prévio de 1500 da OFERTA. A consulta do evento solicitado é inequívoca pelo preço e tipo.

A falha técnica usa `FailingProfitConfiguration`, injetada em `PostgresProfitQueries`. Os demais casos usam leituras PostgreSQL integradas. A prova de snapshot publica duas revisões normalmente e intercala uma troca atômica dos ponteiros de leitura por outra conexão, sem modificar os registros imutáveis. O teste exige que a composição iniciada conserve a revisão anterior ao commit concorrente e a consulta seguinte veja os ponteiros novos.

`stop.sh --clean` encerra e remove somente a instância descartável criada pelo teste, inclusive em falhas. As avaliações não exigem nova navegação externa nem envio de WhatsApp.
