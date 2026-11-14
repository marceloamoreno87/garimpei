# F23 — complemento visual do ciclo 2

Verificação em **2026-11-13, 23:08–23:14 UTC**, no Docker `eval_f23_runtime`, URL local `http://127.0.0.1:34524`. Sessão exclusiva `f23-ui-cycle2`, **playwright-cli no contêiner quality**, Chromium, desktop **1440×1100** e tela estreita **390×844**. Todas as 12 capturas finais foram copiadas ao host e examinadas com `view_image`.

Este complemento preenche as variantes de apresentação ausentes na [primeira revisão](ui-review.md). Não representa novo corpus humano ou nova prova do modelo. O robô permaneceu **desligado, revisão 1, epoch 1**; `active_request=null`, política assistida inativa. Houve **zero POST no navegador, zero nova chamada GPU e zero envio**.

## Preparação e proveniência

Foram adicionados somente controles de engenharia ao banco próprio, sob lock de publicação: três anúncios novos de apresentação, quatro revisões e um interesse sem observações. Não se alteraram os dados da prova anterior.

| Controle | Origem e comportamento semeado |
|---|---|
| Conflito manual | Anúncio sintético com fonte textual **825GB**; correção manual válida de **1 TB**, revisão 1. Resultado de conflito identificado como controle de apresentação, sem chamada do modelo. |
| Pendente | Anúncio e revisão `pending`, sem resultado ou vínculo de nova inferência. A descrição identifica o controle de engenharia. |
| Falha | Revisão `failed`, explicitamente identificada como falha semeada, sem atribuir resultado ao modelo. |
| Parcialidade/mídia | Projeção de leitura adicional do **F15 parcial já persistido**: assessment `d1e2a794-52da-48ab-98e8-e0ccaa210275`, observação `b2cf50b5-1a12-5983-bf92-53ab38c9a17b`. Esse ensaio anterior executou inferência real sobre uma **foto de controle sintético autorizada**; não se trata de anúncio/foto real de mercado. A projeção não executou inferência novamente. |
| Sem dados | Segundo interesse, “iPhone 15 128GB — controle sem observações”, sem correspondências de anúncios. |

A mídia disponível mantém o hash original `f2be79e0ba14ca33ffc53972e2381f9766289545f974eeaa53eedf1df6b05a86`. Nenhum arquivo de imagem privado foi copiado ao repositório; a captura mostra apenas referências e hash que a interface apresenta.

## Veredictos por item

| Item | Veredito visual e evidência |
|---|---|
| **UI-EVIDENCIA-01** | **PASS na apresentação exercitada**, combinando os estados atual/anterior do primeiro ensaio com conflito, pendência, falha e parcialidade deste complemento. O conflito mostra **“Correção manual preservada · revisão 1”**, armazenamento **1 TB** e a fonte literal **825GB** juntos. O pendente diz “Aguardando análise local”, sem linha de execução atribuída. A falha diz “Análise indisponível”. A condição parcial aparece como **“Evidência insuficiente”**, com hash não vazio e limite explícito: não confirma funcionamento nem autoriza alerta. |
| **UI-COBERTURA-01** | **PASS na apresentação exercitada**: dois interesses, quatro finalidades por interesse, unidades e data do recorte. O PS5 tem **5 ofertas**, **4** com revisão de identidade solicitada, **1** sustentada, **1** conflito e **1** falha; comparáveis têm universo de **25 pares**, com **1** solicitado/sustentado. O iPhone mostra **“Sem dados de ofertas neste interesse”**, denominador de ofertas **0**; investigação conserva a unidade correta, **1 interesse**, sem solicitação. Isso distingue ausência de dados de zero aprovações numa frente com dados, como condição do PS5. |
| **UI-DIAGNOSTICO-01** | **PASS na dimensão de 503 controlado já exercitada** na [revisão anterior](ui-review.md): URL/filtro, contagens determinísticas, leitura anterior e foco foram preservados. O erro foi interceptado no navegador, sem inferência ou efeito no servidor. Não se repetiu POST neste ciclo; as alterações de apresentação manual não modificaram esse fluxo. |

Esses veredictos cobrem interface e renderização dos estados preparados. A qualidade semântica do modelo, corpus humano, cadeia positiva de alerta e aceite F21 conservam suas próprias exigências; nenhum controle de apresentação os substitui.

Capturas: [conflito desktop](evidence/ui-cycle2/manual-conflict-desktop.png), [conflito estreito](evidence/ui-cycle2/manual-conflict-narrow.png), [pendente desktop](evidence/ui-cycle2/pending-desktop.png), [pendente estreito](evidence/ui-cycle2/pending-narrow.png), [falha desktop](evidence/ui-cycle2/failed-desktop.png), [falha estreita](evidence/ui-cycle2/failed-narrow.png), [parcial com mídia desktop](evidence/ui-cycle2/partial-with-media-desktop.png), [parcial com mídia estreita](evidence/ui-cycle2/partial-with-media-narrow.png), [dois interesses desktop](evidence/ui-cycle2/coverage-two-interests-desktop.png), [dois interesses estreito](evidence/ui-cycle2/coverage-two-interests-narrow.png), [sem dados desktop](evidence/ui-cycle2/coverage-no-data-desktop.png) e [sem dados estreito](evidence/ui-cycle2/coverage-no-data-narrow.png).

## Defeito de apresentação corrigido durante a verificação

A primeira abertura do controle de conflito mostrava apenas o valor observado **825GB**; **1 TB** não existia no texto da página, mesmo com o material expandido. O banco preservava a correção. O defeito foi comunicado ao coordenador, sem alteração de código por este avaliador.

O coordenador registrou **RED: 1 FAIL em 21,43 s**, “manual value is hidden”; corrigiu a projeção e o template; depois registrou **GREEN: 4 PASS em 26,36 s**. Após o deploy próprio, a mesma página foi recapturada nas duas larguras: seção de correção manual, revisão 1, **1 TB** e fonte **825GB** visíveis. Nenhum cálculo ou registro de domínio foi modificado por esse reparo.

## Legibilidade e acabamento

Os disclosures foram abertos e examinados antes da próxima interação. Não houve corte horizontal observado: `scrollWidth=1440` no desktop e `390` no estreito; hash e referências quebram linha. Os estados usam texto explícito, além da cor. Nenhum menu, modal ou overlay foi aberto para encobrir o material. A preservação do foco/menu por teclado tem evidência na revisão anterior.

As notas subjetivas complementares são **design 7**, **originalidade 6**, **acabamento 5**, **funcionalidade 7**: Mineral e hierarquia permanecem coerentes; a correção manual agora pode ser confrontada na própria página. Persistem excesso de rolagem na cobertura e códigos técnicos em parte dos achados. Média ponderada **6,33/10**. Isso não amplia a conclusão dos testes para leitor de tela, outros motores, dispositivo físico ou validação com pessoas.

## Integridade, artefatos e encerramento

Os [hashes antes do navegador](evidence/ui-cycle2/before-browser.json) e a [auditoria posterior](evidence/ui-cycle2/after-browser.json) confirmam os mesmos **8 requests**, os **7 registros originais de revisão** e o assessment F15 original, sem alteração de conteúdo. As quatro revisões de apresentação adicionais ficam identificadas por `ui_cycle2_presentation_control`; o total de revisões passou de 7 para 11. Todos os controles permaneceram aplicáveis às suas observações. A capacidade manual persistida continua **1tb**.

O [manifesto das capturas](evidence/ui-cycle2/screenshot-manifest.json) registra SHA256, tamanho e inspeção de cada imagem. Nenhum cookie, CSRF, credencial ou estado de autenticação foi copiado. Somente a sessão `f23-ui-cycle2` foi encerrada; os serviços, a pausa e os controles foram preservados para o inventário/backup final coordenado.
