# Convenções da interface Django

A implementação usa a direção [Mineral](MASTER.md) e os [tokens existentes](tokens.json). Esta página complementa os documentos dos protótipos com as convenções verificadas na [auditoria de 2026-11-13](audit-2026-11-13/README.md).

| Responsabilidade | Convenção |
|---|---|
| Shell | `monitoring/layout.html` compartilha marca, navegação e contexto. `shell_context.py` deriva a seleção da rota, inclusive nas páginas de erro. |
| Navegação global | Ofertas, Acompanhamento e Sugestões no primeiro grupo; Configurações, Integrações e IA local no segundo. Apenas um destino tem `aria-current="page"`. |
| Telas estreitas | Menu com `aria-controls`/`aria-expanded`; Escape restaura o foco no controle. Desktop exibe os destinos diretamente. Sem JavaScript, o menu permanece disponível. |
| Navegação local | `.section-navigation` em páginas longas, com links para títulos existentes. Abas de condição usam semântica de tabs e painel associado. |
| Tipografia | Manrope no corpo/controles/números; Bricolage nos títulos. Escala estável em `rem`. Valores podem quebrar linha sem diminuir para texto minúsculo. |
| Espaço e superfícies | Tokens de 4–64 px; proximidade entre dados relacionados e separação entre seções. Superfície/borda existente, sem nova camada ornamental de sombras. |
| Controles | Alvos principais de pelo menos 44 px; foco global de 3 px com separação de 4 px; rótulos visíveis, seleção com borda/fundo e estado exposto por HTML/ARIA. |
| Financeiro | Compra → venda estimada → lucro. Lucro maior, preservando sinal/zero/indisponibilidade. Perda usa `color-danger`; indisponibilidade usa `color-muted`. Esses estados não recalculam valores. |
| Avisos | Confirmação/informação e advertência usam papéis semânticos. Texto explica o estado; a cor não é o único indicador. O aviso global se adapta à largura; dentro de uma seção segue a própria coluna. |
| Formulários | Erros recebem foco e mantêm campos. Falhas de rede pertencem ao formulário que iniciou a requisição; consultas em segundo plano não inserem erros de gravação em outro formulário. |
| HTMX | Restaurar foco depois de substituir conteúdo. Busca mantém cursor; abas mantêm seleção/foco; filtros e paginação anunciam o resumo. Leitura publicada só muda quando o usuário aplica a atualização. |
| Polling | Não substituir a área enquanto o usuário está interagindo com ela. Pausar consultas de status em aba oculta. Falha conserva leitura válida e oferece recuperação. |
| Estados vazios | Primeira configuração mostra o próximo passo; recorte sem resultados permite limpar filtros. Paginação não aparece para uma única página. |
| Erros de página | Preservar shell, `h1`, orientação e recuperação adequada. Oferta inexistente oferece outras ofertas; erro de página de Sugestões não é apresentado como fragmento solto. |

As regras compartilhadas ficam em `static/monitoring/style.css`; estilos específicos permanecem nos módulos. Limite seletores de navegação ao componente responsável: um seletor global de `nav a` não deve definir simultaneamente menu, abas e paginação.

A evidência automatizada não substitui leitor de tela, teste com pessoas nem verificação de cada estado de uma integração real. Novas telas devem reutilizar as convenções e repetir as jornadas afetadas no navegador.

## Composição com F21/F22

Após integrar a master publicada, a orientação por rota coexiste com os context processors de integração e do robô. As ações do robô pertencem a Acompanhamento, inclusive em erros. Controle global, resumo nas ofertas e diagnóstico ouro são preservados. A [verificação integrada](audit-2026-11-13/integration-master.md) complementa a auditoria original; F21 conserva sua pendência real e F22 seu aceite registrado.
