# F11 — Revisão da interface

Interface observada via playwright-cli em ambiente descartável próprio, com login/contas sintéticos. Referências Mineral existentes preservadas. Capturas e verificações em `evidence/`.

| Dimensão | Nota | Evidência |
|---|---:|---|
| Design, peso 2 | 8 | Layout, navegação, papel claro e verde do produto conservados; Facebook e WhatsApp seguem a mesma composição. |
| Originalidade, peso 2 | 7 | Fluxo próprio de conexão com perfil local e microcopy contextual, utilizando controles convencionais. |
| Acabamento, peso 1 | 7 | DocWidth=viewport em 1440/390 px; mensagens e ações sem sobreposição. Texto de instrução é longo no celular e exige rolagem. |
| Funcionalidade, peso 1 | 8 | Ação principal evidente, verificação explícita e recuperação após desafio. Ajuda avançada abre com Space. Login real depende de alternar para outra janela. |

Média ponderada: `(8×2 + 7×2 + 7 + 8)/6 = 7,50`. Nenhuma dimensão ≤3. As notas não substituem critérios observáveis do contrato.

Capturas examinadas: `desktop-initial.png`, `mobile-waiting.png` e `mobile-challenge.png`; os estados verificado e opção avançada também foram capturados e inspecionados por DOM. A ajuda aberta foi inspecionada antes da ação seguinte. O campo de cookies permaneceu vazio. Não há overlays, mídia falsa de login ou material de sessão real nas capturas.

Limitações: não houve leitor de tela. O favicon 404 preexistente aparece no console. Teste visual não comprova que o Facebook aceite a sessão. O texto sobre pausa diante de bloqueios responde ao incidente relatado e não implica eficácia contra detecção.
