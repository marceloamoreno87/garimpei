# Plano de implementação — F15 Avaliação conjunta de imagens e descrição

**Pré-requisitos:** F05/F06 avaliadas; F14 com manifesto e cópias locais versionadas; F19 com inferência assíncrona, revisões fixadas, limites técnicos e prova da GPU. Aplicação Python 3.13/Django 5.2, PostgreSQL e worker da stack existente. Nenhum novo runtime ou broker.

Os caminhos e formatos estão em [spec.md](spec.md); os observáveis em [contract.md](contract.md). Esta especificação não inicia a implementação nem altera `pending`.

## Fase 1 — Fronteiras e política

**1. Integrações e ambiente** — Conciliar as entradas de F06/F14 e a submissão/consulta de F19 com as fronteiras da especificação. Preparar ambiente isolado, perfil limitado de avaliação e lab reproduzível com proveniência das fotos.

**2. Condição e evidências** — Consolidar proteção textual, rubrica por categoria e resolução da condição com precedência manual. Definir abstenção e suficiência como regras de domínio compartilhadas pelos consumidores.

**Verificação da fase:** contratos de entrada comprovados; três regressões protegidas sem IA; tabela de casos de desgaste/dano/suspeita/foto ausente com resultados esperados e rubrica revisada com autoria/método explícitos.

## Fase 2 — Avaliações persistentes

**3. Histórico e ativação** — Adicionar persistência de avaliações e vínculo vigente com migração dos dados existentes. Preparar adoção por lotes retomáveis que preserve decisões manuais e histórico de alertas.

**4. Processamento e publicação** — Integrar preparação, reaproveitamento e conclusão ao trabalho persistente de F19. Publicar somente resultados aplicáveis, com recuperação limitada, rejeição de resposta ultrapassada e evidências rastreáveis.

**Verificação da fase:** migration com anúncios anteriores; retomada e concorrência em PostgreSQL; mudança de texto/foto/modelo/política; resposta inválida; perda de processo; ausência de foto; inferência lenta sem bloquear coleta independente.

## Fase 3 — Consumidores e experiência

**5. Condição compartilhada** — Integrar consulta de condição, projeção de exploração e decisões de alertas à mesma avaliação aplicável. Preservar o significado de eventos e recibos históricos, sem antecipar a reabertura de estoque prevista em F16.

**6. Evidências nos detalhes** — Exibir aparência, declaração do vendedor, limitações, conflitos e cobertura de fotos com a linguagem da especificação. Conservar navegação, formulário manual e atualização mediante clique.

**Verificação da fase:** HTTP e jornada por navegador; nenhuma promoção/envio automático sem avaliação suficiente; revisão manual e aviso de conflito; lista antiga estável; recibos inalterados. Registrar evidências visuais em ambiente isolado.

## Fase 4 — Qualidade e entrega

**7. Corpus e medição real** — Executar o conjunto reservado com F19 real e publicar resultados contra a referência assistida por IA aprovada, concordâncias/divergências, abstenções e consumo/latência. Distinguir prova sintética de integração e qualidade observada em fotos reais autorizadas.

**8. Consolidação** — Preparar relatório de implementação, operação do lab e mapa dos itens do contrato para suas evidências. Registrar pendências reais de dependência/qualidade e manter o ciclo de avaliação sem declarar conclusão antecipada.

**Verificação da fase:** `node scripts/run-gates.mjs`, suites aplicáveis da spec, migrations, navegador e corpus real. Conferir Coverage Manifest completo; gate ausente/falho ou dependência não comprovada mantém entrega pendente.

## Atualização aprovada — 2026-11-13

Preservar IDs, DAG e verificações determinísticas. A fase 7 usa referência assistida por IA aprovada, congelada antes das predições; registrar ausência de validação humana independente. Exercitar pré-condições reais de prontidão do transporte e GPU com prazo finito, além dos controles. A falha inicial de aquecimento não deve ser escondida nem resolvida com bypass de pins/GPU. Somente resultados físicos vinculados ao corpus e gates aprovados permitem concluir o aceite revisado.
