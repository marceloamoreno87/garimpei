# F09 — Operação de alertas

Os alertas ficam desligados por padrão. A preparação local usa os scripts e a imagem GOWS fixada em [F02](../F02-fundacao-tecnica-e-ambiente-local/versions.md). O teste programável verifica as regras locais. O pareamento, o envio e o recebimento reais continuam pendentes por decisão do usuário nesta execução.

No arquivo privado usado por `GARIMPEI_ENV_FILE`, configurar `GARIMPEI_ALERTS_ENABLED=true`, `GARIMPEI_WAHA_SESSION`, `GARIMPEI_WAHA_RECIPIENT` e `GARIMPEI_WAHA_ACCOUNT`; manter `WAHA_API_KEY`. Não há sessão, conta ou destino operacional padrão. O destinatário deve ser um chat direto canônico `numero@c.us`, verificado na imagem local para o destinatário autorizado. A conta deve corresponder exatamente a `me.id` da sessão em `WORKING`. Não publicar os valores.

Abra o dashboard local do WAHA conforme a configuração privada da F02, pareie a conta pelo procedimento do serviço e confira conta e destinatário antes de habilitar o envio. Não salve QR codes em evidências. Use apenas uma oferta sintética na primeira prova autorizada, confira o recebimento e consulte o mesmo ID/ACK antes de considerar o canal validado. Preserve o volume de sessão na parada normal. `./scripts/stop.sh` e o próximo `./scripts/init.sh` conservam os recibos; não use `--clean` com sessão real.

O worker atende a fila `alert` e agenda quatro estágios independentes: ingestão, avaliação, reconciliação e envio. A aplicação visual não participa dessa autorização. O supervisor só agenda o pipeline depois de existir um evento F04; a configuração inicial sem eventos não cria jobs de alerta. Cada estágio tem um lock de sessão PostgreSQL próprio, liberado na desconexão do worker; leases e gerações das intenções protegem concorrência e respostas tardias. Um erro financeiro por identidade conserva espera com `profit_query_failed` e permite o avanço das outras identidades. Uma falha de leitura do histórico suspende novas autorizações. A configuração ausente gera `configuration_missing`, sem tentativa autorizada.

## Perfil e estados

| Parâmetro privado | Padrão |
|---|---:|
| `GARIMPEI_ALERT_TICK` | 5 s (verificado pelo supervisor a cada 2 s) |
| `GARIMPEI_ALERT_TIMEOUT` | 10 s por chamada |
| `GARIMPEI_ALERT_LEASE` | 60 s |
| `GARIMPEI_ALERT_RETRY_BASE` | 15 s |
| `GARIMPEI_ALERT_RETRY_MAX` | 300 s |
| `GARIMPEI_ALERT_WINDOW` | 86400 s desde a autorização |
| `GARIMPEI_ALERT_HISTORY_PAGES` | 10 páginas de 100 mensagens |

A espera cresce exponencialmente até o teto. Sem prova de transmissão, apenas a falha na conexão anterior à requisição permite `safe_retry`. Não foi adotada interpretação de rejeição HTTP como não aceitação sem a prova da imagem. Qualquer resposta incompleta, 5xx ou perda posterior à conexão permanece incerta. A busca inclui margem de relógio de 300 s e não baixa mídia. Toda página configurada é consultada, com offsets incrementados pelo limite mesmo quando há poucos resultados. Se a última página ainda contiver mensagens, a busca é incompleta e não confirma por referência. Aumente o limite de páginas dentro da configuração documentada quando necessário; a ausência de resultado não autoriza reenvio.

`confirmed` exige ID, mensagem de saída, corpo e chat exatos, conta conferida na sessão e ACK numérico entre SERVER (1) e PLAYED (4). Isso comprova aceitação no servidor; não declara leitura ou entrega ao aparelho. `uncertain` mantém a tentativa original, sem novo POST. `review` encerra sondagens frequentes após a janela. O início de outro worker agenda uma consulta adicional de `review`; a tentativa continua com a autorização original. Uma alteração de conta, sessão ou destino conserva o vínculo anterior e impede despachar essa intenção ao novo destino. O corpo e a referência se conservam em tentativas seguras.

## Diagnóstico local

Use o mesmo arquivo privado e `manage.py dbshell` ou sua conexão local identificada. As consultas abaixo omitem corpo, conta, número e IDs do provedor:

```sql
SELECT state, reason, count(*) FROM runtime_alerteventdecision GROUP BY state, reason;
SELECT id, state, reason, generation, next_action, lease_until, confirmed_at
FROM runtime_alertintent ORDER BY created_at;
SELECT intent_id, ordinal, state, reason, authorized_at, finished_at, ack, provenance
FROM runtime_alertattempt ORDER BY authorized_at;
SELECT sequence, history_ready, dispatch_suspended, updated_at FROM runtime_alertfeedcursor;
```

Os logs JSON `alert_state` contêm somente referência local, estado e motivo. Falhas técnicas usam códigos fixos; não copie logs privados de outros serviços. Tempos podem ser extraídos de `ListingEvent.occurred_at`, `AlertEventDecision.evaluated_at`, `financial.calculated_at`, `AlertAttempt.authorized_at` e `AlertIntent.confirmed_at`. Nos testes determinísticos esses valores usam relógio controlado: não são medições de latência real. Na prova real medir publicação → composição disponível, composição → autorização/POST e POST → confirmação separadamente.

## Restauração e reconciliação operacional

Antes de habilitar envios após uma restauração que possa ter perdido recibos, mantenha o worker parado e marque `dispatch_suspended=true` em `runtime_alertfeedcursor`. Confira o intervalo perdido com o histórico WAHA e os recibos disponíveis. Só libere esse bloqueio após conferir a integridade. Reconstruir um cursor não recupera recibos perdidos. Apagar decisões/intencões para tentar novamente pode duplicar mensagens e não é uma política automática.

Uma tentativa em `review` pode ser recolocada exclusivamente em reconciliação, preservando autorização, corpo, conta, destino e referência, por operação local documentada:

```sql
UPDATE runtime_alertintent
SET state='uncertain', next_action=CURRENT_TIMESTAMP, lease_until=NULL, generation=generation+1
WHERE id='<referência-local>' AND state='review';
```

Isso não libera POST. Nunca transforme uma tentativa incerta em `queued` ou `safe_retry` apenas porque uma busca não encontrou mensagem. Se o resultado continuar incerto, a decisão de enviar novamente permanece uma decisão operacional externa à automação.

## Verificação

As factories `tests/factories/alert*.py` criam ambientes `eval` descartáveis, fontes integradas de F04/F06 e WAHA programável em loopback, com credenciais próprias. `GARIMPEI_ALERT_FIXTURE_URL` só é aceito nessas instâncias. Os testes conferem quantidade de POSTs, IDs, ACKs, rollback, ordem manual, upgrade de migrations e duas conexões concorrentes. A parada de testes identifica o processo pelo manifesto antes de pausar seu grupo; a limpeza conserva recursos alheios. Não executar as factories contra um ambiente de operação.

Referências do protocolo consultadas: [sessões WAHA](https://waha.devlike.pro/docs/how-to/sessions/), [envio](https://waha.devlike.pro/docs/how-to/send-messages/) e [consultas/paginação/ACKs](https://waha.devlike.pro/docs/how-to/chats/). A documentação atual fundamenta o adapter; a confirmação na imagem fixa pareada continua sendo requisito separado do contrato.

## IDs diretos GOWS e recibos com alias

O destinatário pode ser um ID canônico `@c.us` ou `@lid`, além do grupo `@g.us` configurado pela F10. Resolva número/conta pelo endpoint local autenticado de check-exists; não invente LID nem troque o binding de uma intenção existente. GOWS pode retornar `from=Chat`, `to/participant=null`, `Sender` em LID e `SenderAlt` como JID PN. A confirmação exige prova de conta, chat, saída, corpo/referência e ACK; alias não libera reenvio incerto. Os identificadores completos permanecem privados.
