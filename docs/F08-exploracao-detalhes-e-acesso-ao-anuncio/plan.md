# Plano de implementação da F08 — Exploração, detalhes e acesso ao anúncio

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-11T19-05-22Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

## Pré-requisitos

- F04, F05, F06 e F07 disponíveis conforme o [PRD](../PRD.md#f08-exploração-detalhes-e-acesso-ao-anúncio). Confirmar dados e revisões de origem, incluindo a composição de F07 e o sinal de indisponibilidade de F04.
- Preparar a instância descartável de F02 e a massa descrita no [contrato](contract.md#prerequisites). Usar a [composição editorial aprovada](../design/DESIGN.md) e os [fluxos de atualização](../design/flows-reference.md#atualização-ordenação-e-volume).

## Etapa 1 — Contratos e projeção

**1. Integração de leitura** — Mapear observação, condição, avaliação e cálculo para a mesma oferta. Registrar como as dependências identificam dados compatíveis e informam ausência, falha e indisponibilidade.

**2. Publicação e recortes** — Implementar as revisões de apresentação e as consultas por aba, filtro, página e ID. Definir a retomada do reconciliador e a expiração de revisões conforme a especificação.

**Verificação da etapa** — Em PostgreSQL, demonstrar ordenação global, conjunto filtrado, contagem, desempates e leitura consistente antes e após novas publicações. Confirmar que a perda de validade e a falha de uma publicação são distinguíveis.

## Etapa 2 — Exploração e detalhes

**3. Lista editorial e navegação** — Integrar a exploração à navegação do produto. Entregar abas, busca, filtros, paginação e os estados de leitura aprovados.

**4. Detalhes da oferta** — Exibir referências, composição e link original. Reusar a classificação F05 e conservar o contexto de retorno.

**Verificação da etapa** — Conferir valores contra as consultas de F06/F07, links e estados de dados ausentes. Exercitar classificação, falha de gravação e retorno aos filtros no navegador.

## Etapa 3 — Atualizações e aceite

**5. Atualização explícita e verificação final** — Ligar a detecção de mudanças ao aviso e aplicar a publicação no clique. Exercitar os fluxos de concorrência, expiração, falhas e retomada e registrar evidências por item.

**Verificação da etapa** — Publicar dados enquanto uma página filtrada permanece aberta. Confirmar a estabilidade da lista até a ação do usuário, a preservação do recorte e o progresso independente do worker e do consumo de eventos. Executar os gates e as jornadas do contrato.
