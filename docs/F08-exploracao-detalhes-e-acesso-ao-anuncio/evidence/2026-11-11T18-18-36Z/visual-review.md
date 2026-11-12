# Avaliação visual — frontend-ui-design

Referência: docs/design/DESIGN.md e MASTER.md; observado em Django real via playwright-cli. Capturas: f08-1440.png, f08-768.png, f08-360.png, f08-detail.png, f08-classification-failure.png, f08-state-*.png. Fotos são insumos ilustrativos interceptados da massa, não prova de mídia real.

| Dimensão | Nota | Evidência |
|---|---|---|
| Design (peso 2) | 8 | Papel claro, tinta mineral, fontes locais aprovadas; foto e composição financeira separadas no destaque; hierarquia consistente com o design. |
| Originalidade (peso 2) | 7 | Composição editorial própria do Garimpei e leitura do lucro por modalidade. Grade e controles nativos são convencionais; massa repete a mesma foto. |
| Acabamento | 8 | Sem rolagem horizontal em 360/768/1440; tablet empilha destaque para impedir sobreposição; abas quebram rótulos e preservam contagens; tokens sincronizados e foco visível. |
| Funcionalidade | 8 | Filtros, vazio recuperável, valores/ausências, referências e origem acessíveis; confirmação e foco após atualização; erro mantém leitura; correção manual confirma apenas após persistência. |

Média ponderada: (16+14+8+8)/6 = **7,67/10**. Nenhuma dimensão ≤3.

Teclado: setas, Home e End selecionam e focam a aba; controles nativos navegáveis. Capturas abertas de correção e erro conferidas; não há menus ou diálogos sobrepostos. Imagens visíveis carregaram com naturalWidth>0; CAM42 usou fallback textual. Largura scroll/viewport: 360/360, 768/768, 1440/1440. Reflow de zoom 200% foi emulado como 720 CSS px e DPR 2, sem overflow. Contraste dos tokens: texto ≥5,32:1 no tema claro, verificação parcial sem alegação de certificação WCAG. Nenhum defeito visual bloqueador remanescente observado.
