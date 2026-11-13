# Contrato — F12 Coleta e oportunidades

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-12T00-44-24Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

*Gerado por spec-writer a partir do pedido e das decisões aceitas na conversa.*

## Prerequisites

### Runtime services

Aplicação/worker e PostgreSQL iniciados por `./scripts/init.sh`; avaliação isolada em env próprio e limpeza somente desse ambiente.

### Persistent state

Migrations aplicadas; fixtures sintéticas criam histórico, datas, variantes, amostras e destinatário fake pelos testes. A adoção em dados existentes preserva recibos e histórico.

### Static inputs

Catálogo de categorias versionado, manifesto sanitizado da validação real; corpus sintético com equivalentes, variantes incompatíveis, peças e defeitos.

### Configuration

CEP, ao menos um interesse e taxa explicitamente configurados; frete não obrigatório. Segredos externos ao repositório.

### External dependencies

Perfil autenticado exclusivo autorizado para leitura do Marketplace. Desafio/falha de acesso suspende coleta e requer recuperação humana existente. WAHA fake para regressões, sem novo envio real necessário.

## Quality gates

Cada gate deve passar para a feature ser considerada pronta.

- **Seis gates Python** — `node scripts/run-gates.mjs` — tipos, lint, arquitetura, dependências, ciclos e código não utilizado.
- **Regressões** — suíte pytest de `apps/backend` com ambiente de teste — regras, integração e HTTP sem regressões não justificadas.
- **Navegador** — `playwright-cli` — configuração e exploração verificadas; evidências sem segredos.

## Coverage Manifest

| Critério | Itens |
|---|---|
| F12-AC01 | WORKER-COLETA-01, WORKER-COLETA-02 |
| F12-AC02 | EVENT-NOVOS-01, EVENT-NOVOS-02 |
| F12-AC03 | E2E-CATEGORIAS-01, UI-CATEGORIAS-01 |
| F12-AC04 | SVC-LUCRO-01, SVC-LUCRO-02, UI-LUCRO-01, EVENT-ALERTA-01 |
| F12-AC05 | SVC-IDENTIDADE-01, SVC-CONDICAO-01 |
| F12-AC06 | WORKER-FALHAS-01, WORKER-INTERVALO-01, E2E-OPERACAO-01 |

## Service

**Verification mode:** Invocar serviços públicos consumidos por configuração, exploração e alertas; observar resultados sobre entradas sintéticas.

#### `SVC-LUCRO-01` — Fórmula independente de logística
- given: compra, revenda e taxa válidas, sem cobertura de envio/retirada ou frete.
- when: calcular composição de lucro.
- then: retorna revenda menos compra menos taxa com arredondamento monetário; componente desconhecido permanece indisponível e frete não é tratado como custo zero.

#### `SVC-LUCRO-02` — Aguardar referências incrementais
- given: descoberta elegível e amostra ainda insuficiente, dispersa ou vencida.
- when: chegam comparáveis suficientes durante as 48 horas posteriores à observação.
- then: reavalia o mesmo evento aguardando sem criar intenção antes da estimativa; pode alertar uma vez quando houver lucro calculável; após 48 horas sem referências encerra a espera, sem reabrir exclusões históricas.

#### `SVC-IDENTIDADE-01` — Equivalência ampliada
- given: famílias eletrônicas documentadas com modelo, variante e capacidade; entradas conflitantes, lotes e acessórios.
- when: identificar produto para comparáveis.
- then: famílias adicionadas distinguem variantes; combinações inválidas ou ambíguas não se misturam em amostras; mínimo e dispersão permanecem exigidos.

#### `SVC-CONDICAO-01` — Funcionamento em descrição natural
- given: afirmações explícitas em frases compostas e contraexemplos com negação, perguntas ou defeito.
- when: classificar condição.
- then: afirmação válida é reconhecida; negação/defeito prevalece; incerteza não vira funcionamento presumido e escolha manual persiste.

## UI

**Verification mode:** Formulários HTTP e jornada real de navegador em ambiente isolado.

#### `UI-CATEGORIAS-01` — Escolhas válidas
- given: catálogo ampliado e preferência histórica em rota indisponível.
- when: abrir configuração.
- then: novas categorias validadas aparecem; indisponível não é oferecida como válida e a preferência antiga tem diagnóstico visível sem apagar histórico.

#### `UI-LUCRO-01` — Alerta e lucro sem logística
- given: usuário configura monitoramento e explora uma oferta com estimativa.
- when: salvar taxa sem frete e abrir lista/detalhes.
- then: configuração funciona sem frete; mostra lucro potencial antes de frete/transporte, taxa e amostra; não exige escolha de envio/retirada.

## Worker

**Verification mode:** Executar coleta com fonte fake e PostgreSQL, verificar estado publicado e retomada.

#### `WORKER-COLETA-01` — Busca única
- given: interesses configurados.
- when: coletar um ciclo.
- then: executa uma busca por interesse sem acrescentar a palavra envio; preserva deduplicação entre interesses e limites seguros de paginação.

#### `WORKER-COLETA-02` — Publicação incremental
- given: uma consulta longa seguida de outras consultas e detalhes válidos disponíveis.
- when: processar um lote enriquecido antes de concluir todo o ciclo.
- then: observações tornam-se consumíveis antes do fim; retomada/matches sobrepostos não duplicam anúncio, observação ou descoberta.

#### `WORKER-FALHAS-01` — Prova e falha honestas
- given: rota errada, cursor repetido, datas fora de ordem ou desafio.
- when: coletar.
- then: distingue parcial de vazio; parâmetros escritos pelo adapter não são prova de filtro aplicado; não corta histórico pela ordenação não comprovada; desafio suspende acesso e não é contornado.

#### `WORKER-INTERVALO-01` — Cadência rápida e recuperação de falhas
- given: ciclo parcial com progresso e espera antiga de uma hora sem prazo exigido pela fonte.
- when: reconciliar o agendamento.
- then: aplica intervalo de 60 segundos entre ciclos e remove a espera antiga; não acumula falhas globais por categoria/paginação; três falhas consecutivas de detalhe pausam a tentativa; falha geral sem progresso começa em 15 segundos e limita o recuo a 300 segundos, respeitando espera maior pedida pela fonte.

## Event

**Verification mode:** Consumir eventos e intenções com dependências de envio fake.

#### `EVENT-NOVOS-01` — Novos durante histórico parcial
- given: marco persistido e carga inicial parcial; anúncios anteriores, posteriores, sem data e futuros.
- when: publicar detalhes confirmados.
- then: somente publicação comprovadamente posterior e não futura pode emitir descoberta não silenciosa; outras elegibilidades continuam obrigatórias; repetição não duplica evento.

#### `EVENT-NOVOS-02` — Adoção e retomada
- given: instalação com histórico e envios já registrados.
- when: migrar e reiniciar.
- then: preserva histórico/recibos e marco; não transforma estoque antigo em alerta; redução continua exigindo confirmação anterior.

#### `EVENT-ALERTA-01` — Conteúdo e elegibilidade
- given: evento elegível com lucro calculável e logística desconhecida.
- when: preparar mensagem.
- then: informa compra e lucro potencial antes de frete/transporte e link; logística não bloqueia; condição, interesse, disponibilidade e idempotência continuam validados.

## E2E

**Verification mode:** Aplicação real local e leitura autorizada da fonte; manifesto sanitizado e medições agregadas.

#### `E2E-CATEGORIAS-01` — Cada categoria validada
- given: catálogo final de eletrônicos.
- when: consultar cada categoria selecionável na fonte.
- then: contexto correto e resultado/estado vazio verificável ficam registrados; para resultados paginados, continuação apresenta progresso; redirecionamento genérico reprova categoria.

#### `E2E-OPERACAO-01` — Sistema retomado e resultados medidos
- given: alterações verificadas e perfil autenticado exclusivo.
- when: iniciar o ambiente e observar coleta.
- then: web/worker operam; relatório compara busca e enriquecimento com diagnóstico anterior, sem prometer completude ou lucro realizado; falhas externas permanecem explícitas.
