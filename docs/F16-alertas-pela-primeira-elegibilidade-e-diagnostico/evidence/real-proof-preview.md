# Prévia efetiva da prova real — nenhum POST autorizado

Ambiente próprio eval_wave11b_f16, web http://127.0.0.1:20411/integracoes/. Worker próprio pausado. Schema0015 aplicado; sessão WORKING; grupo escolhido: `garimpei - alertas`. Alertas do produto permanecem desativados. Há exatamente uma intenção elegível, da oferta sintética16001, sem tentativa autorizada.

Referência efetiva gerada normalmente: `040048a8-8845-4375-9ca1-0b31ad3324c9`. Snapshotv2: compra1000, venda1500, taxa10%/150, lucro350; event_id=null. SHA-256 do corpo: `739fe10ed4af395733ce4ba3fe7539217225ca5bcf61f259f8474b18793a0597`. Data observada sintética11:30UTC; publicação absoluta10:00UTC. A autorização revalidará o relógio atual depois da checagem do canal.

Mensagem exata aguardando autorização específica:

```text
Nova oferta · [TESTE F16] PlayStation 5 Slim disco 1TB
Facebook Marketplace
Preço de compra: R$ 1.000,00
Preço de venda estimado: R$ 1.500,00
*Lucro estimado: R$ 350,00*
Observado em 12/11/2026 às 08:30 (São Paulo)
https://www.facebook.com/marketplace/item/16001/
Ref. 040048a8-8845-4375-9ca1-0b31ad3324c9
```

Após autorização: executar somente esta intenção por caso de uso explícito, com Binding conferido do grupo selecionado. Antes do Send conferir external_id16001, referência, único item pronto, corpo/hash/snapshot coerentes e product alertsFalse. O cliente limitado não pode despachar outra identidade. Não ativar fila geral. Conferir mensagem observada no grupo separadamente do recibo técnico e retomar sem outro POST. Identificadores privados/conta/chaves ficam fora do versionamento.
