# Plano de implementação da F05 — Classificação por condição

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-11T17-03-39Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

## Pré-requisitos

- F04 disponível conforme a dependência do [PRD](../PRD.md#f05-classificação-por-condição), com identidade estável, observações de anúncio persistidas, visibilidade e caminho de coleta exercitável com uma fonte sintética. Conferir o mapeamento com a [especificação](spec.md#2-arquitetura-e-integração) antes de integrar.
- Ambiente local F02, banco descartável migrado e ferramentas do [contrato](contract.md#prerequisites). Usar as versões e o lock do checkout.
- [Design aprovado](../design/flows-reference.md#gravação-classificação-e-correção) para abas, estado pendente e recuperação em detalhes.

## Etapa 1 — Entrada da coleta e regra de condição

**1. Contrato de dados de F04** — Confirmar identidade, evidência de condição e fronteira de atualização do anúncio nos processos web e worker. Preparar observações reproduzíveis com os casos do contrato.

**2. Condição efetiva** — Implementar a interpretação da evidência e a projeção compartilhada de condição, procedência, aba e conflito.

**Verificação da etapa** — Executar a matriz automática e observar a mesma identidade, origem e link após leitura por aba e por ID. Exercitar anúncios preexistentes, dados ausentes, atualização válida e falha da coleta.

## Etapa 2 — Gravação manual

**3. Escolha persistida** — Implementar classificação e correção com precedência manual, falha recuperável e proteção contra páginas antigas e gravações concorrentes. Integrar a consulta usada por F08 e F09.

**Verificação da etapa** — Em PostgreSQL, demonstrar primeira escolha, correção, rollback, nova coleta e reinício. Confirmar os efeitos observados no contrato de alertas.

## Etapa 3 — Abas, detalhes e aceite

**4. Interação de classificação** — Conectar as abas e os detalhes ao backend, com os controles de primeira escolha, correção e recuperação do [design aprovado](../design/DESIGN.md). Reusar a navegação e os componentes de formulário existentes.

**5. Evidência de aceite** — Executar o contrato por superfície e registrar resultados por ID e por critério do PRD. Consolidar as evidências de integração, navegação e verificação do backend.

**Verificação da etapa** — Executar os gates e as jornadas do [contrato](contract.md) na aplicação local. Registrar snapshots de espera, falha, sucesso e conflito, incluindo o destino em cada aba.
