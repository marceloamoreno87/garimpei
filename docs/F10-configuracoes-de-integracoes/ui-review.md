# F10 — Revisão visual

Driver: `playwright-cli`, Chromium headless em ambiente descartável próprio. Referências: `docs/design/PRODUCT.md`, `DESIGN.md`, `MASTER.md` e critérios da skill frontend-ui-design. Todas as entradas são sintéticas. Nenhuma captura da sessão real do usuário.

| Dimensão | Nota | Evidência |
|---|---:|---|
| Design (peso 2) | 8 | Papel claro, verde mineral, tipografia e navegação existentes; seções editoriais Facebook/WhatsApp em vez de novos padrões visuais. Desktop com margem e formulário alinhados. |
| Originalidade (peso 2) | 7 | Linguagem específica do garimpo e composição coerente com o produto; controles e fluxo de conexão são convencionais. |
| Acabamento (peso 1) | 8 | Sem overflow em 1440/390 px, ajuda expandida e seleção visíveis, foco e altura de ações adequados. Aviso âmbar com contraste medido 6,19:1. Tela longa exige rolagem. |
| Funcionalidade (peso 1) | 8 | Menu, cookies, feedback, grupo/ativação e renovação compreensíveis. Ajuda abre por Space; erro recebe foco. Copiar cookies ainda exige as ferramentas de desenvolvedor. Pareamento real pendente. |

Média ponderada: `(8×2 + 7×2 + 8 + 8) / 6 = 7,67`. Nenhuma dimensão ≤3. Esse julgamento não substitui as verificações observáveis do contrato.

## Evidências observadas

- `evidence/integrations-initial-desktop.png`: menu e estado inicial.
- `evidence/pairing-desktop.png`: instrução e mídia carregada; imagem sintética de 1 px, sem prova de escaneabilidade.
- `evidence/group-selected-desktop.png`, `group-selected-mobile.png`: seleção salva e ativação explícita, ações visíveis sem clipping.
- `evidence/integrations-mobile.png`, `help-expanded-mobile.png`: layout de 390×844, ajuda aberta inspecionada antes da ação seguinte, sem overlays.
- `evidence/expired-session-notice-mobile.png`: aviso em Ofertas, ação de renovação e dados anteriores disponíveis; cores finais medidas.
- `evidence/cookie-error-mobile.png`: erro legível, sem reapresentar entrada e com foco em `form-error`.
- `evidence/browser-checks.json`: dimensões, carregamento, contraste, privacidade e limites da observação.

O campo fica vazio após salvar e a entrada sintética não aparece no HTML posterior. A navegação e a tipografia Manrope carregam. A seleção do grupo não é descartada a cada polling de status. O aviso Facebook é atualizado por polling sem exigir navegação.

Limitações acionáveis: importar cookies ainda depende de uma ação técnica do operador, explicada na ajuda; acompanhar esse ponto no teste humano. O favicon 404 preexistente e o 400 intencional da entrada inválida aparecem no console; não se declara console inteiramente limpo. Não houve reprodução com tecnologias assistivas nem teste de QR real.
