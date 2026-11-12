# F08 — Operação e verificação

A exploração está em `/ofertas/`, com detalhes por UUID e acesso pela navegação e pelo acompanhamento. Serve HTML completo ou parciais HTMX. Busca, categoria, modalidade, aba, página e revisão viajam nos links. A revisão inicial é normalizada na URL pelo cliente; links e formulários também funcionam sem JavaScript.

## Publicação e integração

- O reconciliador do worker de F02 chama `build_publish_exploration().execute()`. Não há coleta de marketplace na web. Ele lê a configuração F03, observações F04 e avaliações F06 em lote e deriva a composição pela política `compose_profit` de F07, dentro de uma transação PostgreSQL REPEATABLE READ.
- Uma trava consultiva de sessão serializa publicadores antes de abrir o snapshot. Revisão e todas as suas linhas são confirmadas juntas. Falha conserva o último head. Cada revisão copia evidência, avaliação e composição, incluindo os comparáveis exatos. O identificador F04 continua a identidade da oferta.
- A assinatura considera conteúdo de negócio, cobertura, pertinência e validade. Novos IDs de observação e horários técnicos de reobservação idêntica não criam aviso; a publicação selecionada conserva sua procedência. Alterar preços, referência, custos, validade ou disponibilidade pode criar revisão.
- Somente a escolha manual F05 é sobreposta em tempo de leitura. Contagem, filtragem, ordenação e página compartilham uma transação consistente. A gravação verifica a revisão e elegibilidade vigentes de F05. Divergência automática vigente é informativa.
- `source_available=False` confirmado por F04 retira a oferta de novas listas, mantendo detalhes e a última observação válida. Falha ou ausência em busca não equivalem a esse sinal. Cobertura desconhecida permanece em Todas.
- O polling HTMX consulta `/ofertas/atualizacoes/` a cada 30 segundos, somente com a página visível, e ao retornar à aba. Atualiza apenas o aviso. Navegação substitui requisições anteriores; respostas de contexto antigo são descartadas. “Atualizar lista” escolhe o head no início da leitura, preserva o recorte e ajusta página/foco.

Configuração central em `config/env.py`, também carregada do arquivo privado de F02:

| Chave | Padrão | Intervalo |
|---|---|---|
| `GARIMPEI_EXPLORATION_INTERVAL_SECONDS` | 10 s | 2–300 s |
| `GARIMPEI_EXPLORATION_RETENTION_SECONDS` | 86400 s | 60–604800 s |

A limpeza considera o horário em que uma revisão foi substituída, sempre preservando a atual. A expiração resulta em 410 com recuperação explícita. A implementação inicial copia linhas por revisão; não compacta intervalos. Na massa de 59 registros (49 ofertas e dez auxiliares), publicação sem mudança mediu 36–57 ms/17 consultas; página 8,89 ms/9 consultas. Esses números são locais, não um limite de escala. O EXPLAIN está nas evidências. A retenção limita revisões substituídas; o histórico F04/F06 e eventos ficam independentes.

Referências de mecanismo: [polling HTMX](https://htmx.org/attributes/hx-trigger/), [sincronização HTMX](https://htmx.org/attributes/hx-sync/).

## Massa sintética reproduzível

Fixtures em `tests/fixtures/listing/exploration_cases.json` e `tests/factories/exploration.py`. Executar os comandos abaixo em `apps/backend/`:

```bash
uv run --frozen --no-sync pytest tests/unit/test_exploration.py tests/integration/test_exploration.py
uv run --frozen --no-sync python -m tests.factories.exploration /tmp/garimpei-f08-lab-NOVO
uv run --frozen --no-sync python -m tests.factories.exploration_states /tmp/garimpei-f08-states-NOVO
```

Use um diretório novo por execução. Cada laboratório cria segredos próprios, instância eval marcada descartável, PostgreSQL/WAHA e web/worker reais via `./scripts/init.sh --disposable`. A porta está no `public.json` do diretório privado. Para encerrar e limpar somente seus recursos, crie o arquivo `stop` nesse diretório; o laboratório chama `./scripts/stop.sh --clean`. Segredos não devem ser copiados para evidências.

O laboratório principal aceita ações pelo arquivo `action`: `A`, `B`, `C`, `fail`, `recover`. Escreva uma ação por vez e espere a publicação. O laboratório de estados começa sem configuração; ações sequenciais `configure`, `empty`, `populate`, `partial`, `fail`, `interrupt` demonstram primeiro uso, primeira coleta bloqueada/liberada, vazio válido, coleta parcial, falha e diagnóstico de interrupção. `interrupt` controla exclusivamente o recibo sintético de F02, sem parar outros processos.

As labels Câmera/Fone são nomes sintéticos. As descrições carregam identidades já suportadas por F06 (PS5/iPhone); isso exercita a política real sem expandir a identificação de produtos. Dez comparáveis auxiliares ficam fora do recorte por cobertura explicitamente excluída. O catálogo Áudio é injetado somente em eval por `GARIMPEI_CATALOG_FIXTURE`; não comprova categoria verificada na fonte real. A factory configura custos por F03 e entrega observações às interfaces normais de coleta/avaliação no worker. Somente IDs e datas de primeira identificação da massa são preparados antecipadamente para desempates determinísticos.

Mapa: CAM01–CAM42 usam IDs externos 10001–10042 e UUIDs de inteiros 1–42. EXTRA43–EXTRA47 usam 10043–10047. DEF01=10048/UUID 48 e INC01=10049/UUID 49. A revisão é UUID gerado por execução. As imagens HTTPS sintéticas e a navegação externa devem ser interceptadas no navegador conforme o contrato. A foto usada na avaliação vem do laboratório de design e não demonstra mídia real de marketplace.

## Gates

Executar todos os comandos declarados no contrato. O build inclui templates, estáticos e migration 0007. Os testes anteriores de F05 aguardam a publicação assíncrona antes de verificar a interface ou uma nova evidência da fonte; suas regras e expectativas de classificação/escape permanecem preservadas.
