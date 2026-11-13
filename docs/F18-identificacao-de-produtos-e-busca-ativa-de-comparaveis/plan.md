# Plano — F18 Identificação de produtos e busca ativa de comparáveis

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-13T13-37-52Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

**Pré-requisitos:** F06/F12 avaliadas; F13 implementada/avaliada com pesquisa complementar, contexto e exclusividade de perfil. Base Python 3.13/Django 5.2/PostgreSQL/Procrastinate do lock atual, ambiente eval isolado, configuração privada e acesso Facebook autorizado. Base textual independente de F15/F19; integração F16 condicional.

Este plano descreve trabalho futuro. A especificação não executa outra feature nem autoriza envio real ao WhatsApp. Detalhes em [spec.md](spec.md), comportamentos em [contract.md](contract.md), decisões de produto em [design.md](design.md).

## Fase 1 — Recorte e limites

**1. Corpus dos interesses existentes** — Materializar o recorte datado e anotar suporte, atributos, aliases e lacunas por interesse. Separar corpus real e fixture controlada, conforme spec §7.

**2. Fronteira F13 e orçamento medido** — Alinhar navegação, comprovação geográfica e compartilhamento do acesso com coleta. Medir e fixar limites/espera/prioridade antes da ativação automática, conforme spec §3.

**Verificação:** recorte sanitizado, F13 disponível e manifesto completo com evidências numéricas; ausência de acesso/medição mantém a fase pendente.

## Fase 2 — Identidade e correção

**3. Identificação explicável** — Diferenciar ausência, falta de suporte, exclusão e conflito, preservando origem de cada atributo e compatibilidade dos consumidores. Seguir spec §3–§5.

**4. Correção manual e revisão** — Permitir edição opcional e resolução explícita nos detalhes, conservando evidência e histórico e bloqueando avaliação/novo envio diante de contradição. A adoção em dados existentes preserva escolhas e recibos, conforme spec §6.

**Verificação:** origem manual não fabrica trecho; ausência posterior conserva correção; divergência bloqueia; edição concorrente retorna 409; fonte/correção/condição ficam independentes.

## Fase 3 — Investigação persistente

**5. Pesquisa em fatias** — Integrar páginas/detalhes e publicação incremental, com contexto geográfico comprovado, limites e retomada. Compartilhar somente pesquisas compatíveis e preservar progresso independente, conforme spec §2–§3.

**6. Estimativa e composição aplicáveis** — Submeter candidatos à política única F06, publicar evidências/decisões e permitir recálculo F07 apenas para identidade/revisão válidas. Não gerar descoberta por finalidade de pesquisa, conforme spec §3 e §6.

**Verificação:** completar cinco retidos em cenário suficiente; exclusões e contexto inválido não inflam amostra; fonte falha não vira vazio; lease/resposta antigos não publicam; outra coleta/interesse progride.

## Fase 4 — Jornadas e autorização

**7. Diagnóstico e cobertura** — Apresentar motivos consistentes, pesquisas, candidatos e lacunas nos fluxos existentes de ofertas/Acompanhamento. Manter filtros, revisão apresentada e atualização por clique, conforme spec §5.

**8. Proteção de alerta e integração condicional** — Consultar bloqueio de identidade na autorização vigente e preservar intenções/recibos incertos. Quando F16 estiver disponível, integrar correção de identidade à primeira elegibilidade sem alterar a exceção da condição manual, conforme spec §3.

**Verificação:** lista/detalhe/diagnóstico concordam; conflito não autoriza novo envio; transmissão incerta segue reconciliação; integração de 48 horas é comprovada separadamente com F16 disponível.

## Fase 5 — Evidências e avaliação

**9. Prova controlada e real** — Consolidar trajetória da insuficiência à composição e a pesquisa real limitada, com cobertura/limitações explícitas. Distinguir fonte real, fixture e integrações condicionais, conforme spec §7.

**10. Encerramento verificável** — Consolidar gates, regressões, jornadas e evidências por item/critério, preservando pendências reais. Atualizar apenas artefatos e metadados cabíveis ao fluxo de implementação/avaliação.

**Verificação:** seis gates por `node scripts/run-gates.mjs`, pytest aplicável/suíte completa, navegador `playwright-cli`, avaliação `frontend-ui-design`, corpus/limites/prova real presentes. Nenhum desses checks foi executado nesta entrega de especificação; F18 continua `pending`.

## Retomada — orientação de cidade de2026-11-13

1. Registrar a aprovação São Paulo/SP+20km e a observação nativa com24resultados; preservar IDs e decisões históricas.
2. Reproduzir em testes a perda da primeira página nativa compatível e a dependência indevida do CEP na localização da busca.
3. Injetar a origem nativa na composição, preservar CEP/cobertura existentes e versionar o escopo. Reutilizar somente página nativa compatível; filtros divergentes mantêm guard de contexto.
4. Testar fonte/continuação/retomada, persistência/contexto e primeira elegibilidade; executar seis gates e regressões pertinentes.
5. Exercitar a fonte real em perfil exclusivo sem publicar dados ou enviar mensagens reais; medir requisições e conservar metadados sanitizados. Reavaliar todos os itens; somente avaliação limpa conclui F18.
