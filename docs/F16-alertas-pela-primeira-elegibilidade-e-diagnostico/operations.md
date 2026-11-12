# Operação F16

F16 usa a stack Python/Django/HTMX, PostgreSQL e Procrastinate existente. O primeiro alerta tem identidade única `local + Listing.id`, independente de grupo, revisão ou versão da política. `FinancialSnapshot` v1 continua representando evento; v2 representa primeira elegibilidade corrente, com `event_id = null`. Corpos já autorizados e vínculos anteriores permanecem congelados.

## Ambiente desta execução

O ambiente próprio pareado é `eval_wave11b_f16`: web `127.0.0.1:20411`, PostgreSQL `20511`, WAHA `20611`, IA desativada. O arquivo privado é `.runtime/f16.env`, fora do versionamento. A conexão WhatsApp foi conferida como WORKING no grupo escolhido pelo usuário; alertas foram explicitamente desativados antes do preparo. Não foi copiada sessão de outro ambiente.

Parada normal, se necessária após a prova autorizada:

```sh
GARIMPEI_ENV_FILE=$PWD/.runtime/f16.env ./scripts/stop.sh
```

A conexão real deve ser preservada. Não usar `--clean` nesse ambiente pareado. As instâncias dos testes e da avaliação visual têm nomes `wave11b_f16_<token>`, dados e canais sintéticos próprios; suas factories executam início descartável e limpeza somente dos respectivos recursos.

## Adoção e reavaliação

O worker agenda `adopt`, `ingest`, `refresh`, `evaluate`, `reconcile` e `send`. Adoção e refresh não dependem de haver evento de descoberta. Cada página de inventário ou refresh limita-se a 100 identidades. O cursor de inventário é persistido, e a retomada usa o cursor confirmado. Primeiros POSTs ficam suspensos até concluir o inventário; histórico F09 indisponível/suspenso também impede autorização.

- Recibo anterior de descoberta ou redução impede outro primeiro alerta.
- Intenções legadas ainda sem tentativa são incorporadas ou encerradas com motivo. Intenções possivelmente transmitidas conservam referência, corpo, destino e tentativas; transmissão incerta nunca volta à fila de POST por ausência de configuração.
- Publicação precisa vir de evidência absoluta do adapter. Falta de data, valor duvidoso e data futura são estados distintos. Coleta e marco de monitoramento não substituem publicação.
- Autorização usa o relógio depois da consulta lenta do canal. O limite inclusivo é publicação +48h; reconciliação de um efeito anterior permanece possível depois disso.
- Invalidações de coleta/valoração compartilham o commit de publicação. A varredura periódica repara trabalho não sinalizado. Assinatura semântica ignora mera recoleta, horário de observação e foto sem mudança de análise.
- A escolha manual consome atomicamente a entrada automática vigente. Reinício e recoleta equivalente não liberam envio. Entrada automática independente pode reavaliar usando a escolha manual vigente.
- Reduções usam o próprio evento, a consulta F07 `event=True` e a janela histórica F09/F12. A queda usada na primeira composição não produz também redução; queda posterior a uma primeira autorização pode aguardar o recibo anterior.

Rede ocorre fora dos locks. Ordem de escrita: publicação de monitoramento, identidade, intenção e tentativa. Preparação F07 corrente ocorre fora da transação de publicação, evitando aninhar repeatable read em isolamento incompatível. A referência persistente da tentativa acompanha send/reconcile para preservar evidência tardia sem substituir uma geração nova.

## Diagnóstico

A consulta `ReadAlertDiagnosticUseCase.execute(listing_id, displayed_observation_id)` não cria intenção, não reavalia e não acessa WAHA. Falha técnica é distinta de anúncio inexistente. Lista/detalhe preservam revisão e filtros; o bloco declara divergência da observação atual e separa confirmação histórica do impedimento atual. ACK de servidor não comprova entrega/leitura.

O diagnóstico usa estados e motivos públicos tipados. Rótulos de histórico são apresentados em português; códigos persistidos continuam disponíveis para consultas programáticas. Uma falha exclusiva desse bloco conserva HTTP200 e os dados da oferta, com retry da mesma jornada.

## Prova real

A prévia exata e a referência proposta estão em [real-proof-preview.md](evidence/real-proof-preview.md). A conexão não equivale a autorização de envio. Antes de qualquer ativação: obter aprovação específica da mensagem e do grupo, verificar a conta/vínculo na instância própria, conferir ausência de outras intenções enviáveis e manter a fonte da oferta explicitamente sintética em loopback. Não utilizar Facebook autenticado nem enviar oferta real para suprir esse item.

Registrar separadamente mensagem observada no grupo, recibo técnico inequívoco e retomada sem segundo POST. Identificadores de conta/chat e chaves ficam fora das evidências versionadas. Sem essa autorização/prova, `E2E-GRUPO-01` permanece pendente e F16 não pode receber `done`.

A prova desta execução foi posteriormente autorizada especificamente pelo usuário para o grupo escolhido e concluída com a referência 040048a8-8845-4375-9ca1-0b31ad3324c9: exatamente 1 POST e 1 tentativa, ACK2 persistido por GET da mesma mensagem e diagnóstico confirmado após restart. O usuário confirmou separadamente a visibilidade no grupo. Ver `real-proof-user-observation.json` e `real-proof-diagnostic-after-restart.json`. Essa aprovação foi consumida; não autoriza outra mensagem, ativar alertas gerais ou repetirPOST. A sessão pareada deve ser preservada na parada normal.

## Estado ao encerrar

Em12/11/2026, o ambiente próprio20411 foi parado normalmente (exit0), com banco, volumes e sessão retidos. A fonte HTTP sintética também foi fechada. Alertas permaneceramfalse; nenhuma nova mensagem foi transmitida. Para iniciar novamente esse ambiente preservado, use o arquivo privado e `./scripts/init.sh`; a fonte sintética deve ser preparada pelo operador. Não usar `--clean` no ambiente pareado. Evidências em `normal-stop-preflight.json` e `cleanup-final.json`.
