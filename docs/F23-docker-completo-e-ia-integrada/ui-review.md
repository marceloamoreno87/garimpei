# F23 — revisão visual e jornadas de assistência

Avaliação em 2026-11-13 UTC, ambiente isolado `eval_f23_runtime`, web em `http://127.0.0.1:34524`. Sessão própria `f23-assistance-ui` pelo **playwright-cli no contêiner quality**; Chromium, 1440×1100 e 390×844. Direção consultada: Mineral, `docs/design/MASTER.md` e `implementation.md`; critérios de `frontend-ui-design`. Todas as imagens abaixo foram copiadas ao host e examinadas com `view_image`.

As duas ofertas e o interesse são sintéticos; as revisões exibidas já estavam persistidas pela prova GPU coordenada. Esta jornada não iniciou inferência. O único POST acionado foi interceptado no navegador e respondeu 503 controlado, sem alcançar o servidor. A revisão visual não substitui os relatórios do modelo, o corpus humano ou o aceite F21.

## Contrato e evidências

| Item | Observado | Limite do veredito |
|---|---|---|
| UI-EVIDENCIA-01 | Página 200; identidade/comparáveis sustentados e identidade anterior aparecem distintos. Modelo, data, revisão, referências, trechos literais e consumidores estão visíveis; o disclosure de material abre e fecha por Enter com foco de 3 px. Retorno à oferta e link ao comparável estão disponíveis. | **Parcial/BLOCKED para aceite integral:** esta semente não contém conflito manual, análise pendente/falha, parcialidade de fotos nem galeria de hashes não vazia. A preservação manual e as exclusões têm regressões PostgreSQL separadas; isso não equivale a observar esses estados no navegador. |
| UI-COBERTURA-01 | Página 200 em ambas as larguras; um interesse, quatro finalidades, data e unidades explícitas. Há duas ofertas/pares atuais: identidade e comparáveis mostram 1 solicitado/1 sustentado; investigação tem denominador 1. Zero resultados não é anunciado como análise suficiente. Política ainda não adotada está explícita. | **Parcial/BLOCKED para aceite integral:** falta observar um segundo interesse e o estado sem dados nesta jornada. O denominador acima de dez pares foi corrigido e verificado em PostgreSQL, não extrapolado desta semente de duas ofertas. |
| UI-DIAGNOSTICO-01 | Após reparo da semente, acompanhamento 200 com diagnóstico determinístico e explicação anterior. Um 503 interceptado no POST de explicação insere erro somente no feedback da explicação; URL/filtro, contagens e revisão anterior permanecem. Foco retorna ao feedback. A sugestão diz explicitamente que nenhuma ação foi executada. | **PASS na dimensão de resposta 503 controlada do frontend.** Não foi provocado erro real de banco nem falha nova de inferência. As variantes de backend pertencem à avaliação API/worker. |

As capturas finais são [evidência desktop](evidence/ui/evidence-desktop.png), [evidência estreita](evidence/ui/evidence-narrow.png), [cobertura desktop](evidence/ui/coverage-desktop.png), [cobertura estreita](evidence/ui/coverage-narrow.png), [menu aberto](evidence/ui/coverage-mobile-menu.png), [falha controlada desktop](evidence/ui/diagnostic-controlled-failure-desktop.png), [falha controlada estreita](evidence/ui/diagnostic-controlled-failure-narrow.png) e [acompanhamento recuperado](evidence/ui/tracking-recovered-desktop.png). A [captura estreita recuperada](evidence/ui/tracking-recovered-narrow.png) preserva navegação e ações legíveis.

## Responsividade e interação

- Nenhum scroll horizontal observado: `scrollWidth=1440` no desktop e `390` na tela estreita. Referências longas quebram linha.
- Disclosure de evidências funciona por teclado. O menu estreito foi aberto e examinado antes de fechá-lo; Tab para a navegação seguido de Escape fecha o menu e devolve foco a “Menu”.
- Nenhum modal ou overlay cobre o conteúdo. O menu expandido ocupa espaço no fluxo.
- Texto principal medido: `rgb(27,43,35)` sobre `rgb(246,248,243)`, razão de contraste **13,87:1**. Isso não constitui auditoria de todos os pares de cor. Botão de explicação: altura **44 px**.
- Após os reparos coordenados não havia erro de recurso HTTP no carregamento final do acompanhamento. A coleta permanece indisponível por falta de conexão Facebook, explicitamente informada, sem transformar isso em prontidão de automação.

## Defeitos encontrados e correções verificadas

A primeira navegação encontrou `/integracoes/facebook/status/` 500 e acompanhamento 500. Ambos foram comunicados imediatamente ao coordenador. Ele corrigiu a capacidade de rede interna do gateway e a semente de investigação inválida; a repetição retornou 200. A [captura anterior ao reparo da semente](evidence/ui/tracking-before-seed-repair-500.png) permanece histórica e não representa a página final.

A orientação das quatro novas rotas apontava para Configurações. A regressão adicionada a `test_navigation_shell.py` produziu **4 FAIL/12 PASS** antes do reparo e **16 PASS** depois: evidências/reavaliação → Ofertas; cobertura → IA local; explicação → Acompanhamento. As capturas finais conferem a seleção correta.

O teto de dez unidades de admissão era indevidamente aplicado ao denominador acumulado de comparáveis. A regressão com mais de dez exclusões revisadas falhou com `denominator used admission budget instead of current pair universe`; a consulta agora mede todos os pares atuais. O orçamento de admissão permanece separado. Regressões PostgreSQL e orientação juntas: **18 PASS em 14,76 s**.

## Notas de design

| Dimensão | Nota | Evidência concreta |
|---|---:|---|
| Design | 7/10 | Mineral, Manrope/Bricolage, contraste e ritmo editorial coerentes com a aplicação; títulos e decisões ficam separados das referências. |
| Originalidade | 6/10 | Vocabulário e organização atendem ao exame de usados, com evidências e decisões ligadas; cobertura repete blocos semelhantes e exige rolagem longa. |
| Acabamento | 5/10 | Reflow e foco funcionam, mas a grade aninhada do diagnóstico desktop estreita demais alguns títulos e quebra “Diagnóstico” no meio da palavra. |
| Funcionalidade | 6/10 | Estados atuais/anteriores e recuperação contextual são claros; campos como `price_kind`, `none_detected` e limitações em inglês ainda exigem interpretação técnica. |

Média ponderada: **6,17/10** = `(7×2 + 6×2 + 5 + 6) / 6`. Nenhuma dimensão aciona o piso de reprovação ≤3; essa nota subjetiva não aprova os itens contratuais ainda parciais.

Melhorias de acabamento: traduzir nomes/resultados técnicos na apresentação, reduzir o aninhamento da grade do diagnóstico e oferecer caminho mais direto da cobertura às ofertas correspondentes. Não foram feitas alterações de CSS ou de prompts nesta avaliação.

## Proveniência e encerramento

Comandos principais: `playwright-cli -s=f23-assistance-ui open`, `goto`, `resize`, `snapshot`, `click`, `press`, `eval`, `route`, `unroute`, `screenshot` e `close`, executados via `docker exec -e TMPDIR=/tmp/g23tmp -w /app garimpei-eval_f23_runtime-quality-journey`. A rota controlada foi removida antes de terminar. Somente esta sessão de navegador foi encerrada.

O [manifesto sanitizado](evidence/ui/ui-observations.json) registra observações, limites, dimensões, tamanhos e SHA256 das imagens. Nenhum cookie, CSRF, segredo ou estado de autenticação foi copiado. Não houve nova conta Facebook, envio WAHA ou chamada GPU iniciada por esta jornada. Leitor de tela, outros motores e aparelho físico não foram verificados.
