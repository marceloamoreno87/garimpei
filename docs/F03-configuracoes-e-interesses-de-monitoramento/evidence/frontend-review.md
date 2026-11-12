# Revisão visual — F03

Aplicação Django real, instância descartável, Chromium via `playwright-cli`. A direção Mineral aparece nas fontes Bricolage Grotesque/Manrope, no fundo papel, no verde de ação e na separação entre formulário e orientação. As capturas têm dados sintéticos da avaliação e não usam a interface do laboratório.

| Dimensão | Nota | Evidência |
|---|---:|---|
| Design (peso 2) | 8 | O [primeiro uso](region-1440.png) ordena título, progresso, etapa e ação com clareza. A orientação fica separada do formulário. |
| Originalidade (peso 2) | 7 | A composição do Garimpei e o contexto de compra e revenda aparecem no conteúdo e no sistema Mineral; a navegação e os controles usam padrões convencionais para facilitar o primeiro uso. |
| Acabamento | 8 | [360 px](interests-360.png), [768 px](interests-768.png), [1440 px](interests-1440.png) e [reflow equivalente a 200%](interests-zoom200.png). As fontes carregaram; botões empilhados no menor viewport, rótulos completos, sem rolagem horizontal, corte ou sobreposição. |
| Funcionalidade | 9 | Fluxo e edição exercitados com e sem JS; [erro de nome](product-error.png) aponta ao campo; [envio](edit-saving.png) bloqueia repetição; [falha](edit-save-failed.png) mantém entrada, informa o problema e permite tentar novamente. |

Média ponderada: **7,8/10**. Nenhuma dimensão abaixo do limiar. O problema inicial de rótulos fragmentados em 360 px foi corrigido e recapturado. Na tela estreita, o texto de orientação fica depois do formulário, o que mantém o fluxo de entrada acessível pela rolagem da página.

O DOM confirmou rótulos, etapa corrente, resumo `role=alert` focado, `aria-invalid`, vínculo com ajuda e controles de envio com pelo menos 44 px. O gerador de tokens passou com texto de pelo menos 5,32:1 e borda de controle de 3,05:1 no tema editorial. A captura a 200% usou 720 CSS px a 2×; a prova é de reflow/escala, não um teste de todos os controles de zoom ou leitores de tela. Nenhum overlay da aplicação foi necessário nas jornadas. Ver [observações automatizadas do navegador](browser-results.json).
