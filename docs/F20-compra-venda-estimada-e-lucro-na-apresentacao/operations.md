# F20 — Operação e laboratório financeiro

A aplicação mantém fórmula, taxa, política de elegibilidade e reconciliação existentes. Publicações mostram compra, venda estimada e lucro da mesma composição; novas autorizações usam `financial-trio-v1`. Corpos já autorizados continuam no formato anterior, sem preenchimento retroativo.

## Aplicação

Use `./scripts/init.sh` com arquivo privado de configuração conforme F02. A migration aditiva `0013_alert_message_snapshot` acrescenta `financial` e `body_format` às intenções, inicialmente vazios; não cria eventos, intenções ou envios. A folha paralela de F19 requer migration de merge na integração futura das branches. Não aplicar arquivo de migration de outra worktree isolada sem integrar e conferir dependências.

`profit_pending` reabre somente a decisão da intenção antiga ainda sem corpo/tentativa para a consulta normal F07 do evento. `profit_observation_mismatch` e `profit_incompatible` impedem nova autorização. `authorized_body_missing` conserva a tentativa e requer revisão: não reconstrua corpo de transmissão possivelmente ocorrida. Os logs expõem referência, estado, motivo e formato; corpo/destino ficam privados.

## Laboratório sintético

Na raiz, sincronize o lock com `uv sync --project apps/backend --locked --all-groups`. Crie um diretório temporário privado com `mktemp -d`, fora do repositório. Em `apps/backend/`, execute:

```bash
uv run --frozen --no-sync python -m tests.factories.financial_presentation_lab --private-dir /tmp/DIRETORIO-PROPRIO
```

O lab inicia os scripts oficiais em instância eval descartável com banco, portas, segredos e serviços próprios, fonte programável, relógio e WAHA sintéticos. A saída informa URL e IDs sintéticos. O arquivo `public.json` local identifica a instância e o caminho privado de configuração; não copie o arquivo de configuração ou seu conteúdo para evidências. Acrescente `--unconfigured` para percorrer o assistente no navegador antes de qualquer configuração.

O cenário padrão tem 42 ofertas cujo título contém `Oferta`, mais casos e comparáveis independentes. Em `/ofertas/?q=Oferta`, conferir páginas 20/20/2. POSITIVO é a identidade externa 10001; ZERO 10040; NEGATIVO 10041; SEM_VENDA/NOVO_APENAS 10042; SEM_COMPRA 10043; FRACAO 10044. O catálogo JSON em `tests/fixtures/valuation/financial_presentation.json` registra entradas/resultados. Os cinco usados independentes sustentam a venda de 1500; a referência de novo de 2400 não a preenche. Para FRACAO, persistir taxa de 12,50% e aguardar a publicação correspondente: venda 101, taxa12,63 e lucro18,37.

Envie uma ação JSON por linha no stdin do lab:

| Ação | Efeito em recursos sintéticos próprios |
|---|---|
| `{"action":"update"}` | Compra de 10001 passa a900; comparáveis passam à mediana1600; avança relógio e aguarda processamento normal. |
| `{"action":"fee","value":"20.00"}` | Edita configuração ativa preservando CEP/interesses e avança relógio. Esperar a revisão confirmada; o aviso de novidade conserva a anterior até o clique. |
| `{"action":"new_offer","key":"10951","price":"1000,00"}` | Insere uma oferta comprovadamente posterior ao marco e avança relógio, permitindo verificar envio sintético normal. |
| `{"action":"fail_read"}` | Renomeia temporariamente a tabela de ofertas publicada desta instância; leitura retorna503 e navegador conserva composição anterior. |
| `{"action":"recover_read"}` | Restaura o nome da tabela própria; ação de atualizar existente permite recuperação. |
| `{"action":"incompatible"}` | Corrompe somente a associação de observação da oferta10001 na massa descartável para demonstrar indisponibilidade. |
| `{"action":"restart"}` | Executa stop/init próprios conservando dados e sessão sintética. |
| `{"action":"pause_worker"}` / `{"action":"resume_worker"}` | Suspende/retoma grupo próprio em ponto sem transação, para ensaios controlados. |
| `{"action":"quit"}` | Recupera falha injetada e executa stop --clean exclusivamente na instância descartável do lab. |

Não usar estas mutações em dados pessoais ou bancos compartilhados. O fake WAHA registra corpos/POSTs e confirmações locais; isso não é prova de entrega/renderização em WhatsApp real. A configuração do lab nunca usa perfil Facebook pessoal.

## Verificação reproduzível

- `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests/unit/test_financial_presentation.py`
- `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests/http/test_financial_presentation.py apps/backend/tests/integration/test_financial_messages.py`
- `node scripts/run-gates.mjs` e suíte integral do contrato.
- UI com `playwright-cli -s=f20 open <URL>` e sessão própria; use snapshots e screenshots nas larguras360/768/1440. As capturas `zoom200` desta execução representam viewport CSS com metade da largura (equivalência de reflow a200%); não comprovam acionamento do zoom nativo do navegador.

A prova de migração dedicada aplica o schema0012 em banco descartável, preserva corpo e tentativa legados e aplica0013 verificando identidades/contagens/conteúdo. A prova de autorização testa rollback, duas conexões concorrentes, corpo congelado, reavaliação legada e reconciliação sem POST adicional. Os testes numéricos exercitam F07→autorização→fake WAHA, incluindo redução de1200 para1000 com observação posterior900 e arredondamento de centavo.

## Validação desta entrega

Avaliação clean:26/26 itens e8/8 ACs; suíte integral339 PASS/1133,04 s sobre fonte/testes congelados e seis gates Python aprovados. Relatório em `eval-report-2026-11-12T03-22-50Z.md`. Os ambientes de laboratório desta execução foram encerrados e seus dados descartáveis removidos; recrie o lab pelo comando acima para uma nova jornada. Código permanece isolado na branch feat/F20-apresentacao-financeira.
