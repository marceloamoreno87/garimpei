# F15 — Verificação visual controlada

Navegação por `playwright-cli` nas sessões exclusivas `f15-final-list` e `f15-final-detail`, laboratório eval próprio em 22712. Evidências em `evidence/ui-*.txt`, quatro screenshots e `ui-check-summary.json`. Originais controlados carregaram com 640×480 naturais. Nenhum perfil da fonte foi aberto.

Foram observados: espera com cobertura 0 de 1; resultado completo com declaração literal separada de aparência/limitações e modelo/data secundários; Enter no link “Foto 1 da avaliação” levando ao original correto; análise anterior explicitamente histórica enquanto entrada nova aguardava; formulário manual operado por teclado; escolha manual boa preservada diante de dano automático, com aviso e foto de suporte; ausência de fotos sem data fictícia de execução. Texto, preço e link de origem permaneceram acessíveis. Resultado fake é identificado na própria interface.

Em lista filtrada, a consulta de atualização mostrou aviso e manteve revisão, filtros, foco, ordem e conteúdo até clicar “Atualizar lista”. O clique explícito manteve os filtros e aplicou a nova condição. Screenshots de espera, conclusão, divergência e ausência foram inspecionadas visualmente. O console não apresentou erro de aplicação; houve apenas favicon inexistente.

Verificados 1440 px, 390 px e reflow em 195 px CSS, equivalente à largura disponível de 390 px com ampliação de 200%. Este último método verifica reflow, não simula zoom nativo do navegador. Não houve overflow horizontal nas páginas exercitadas; foto/ações e origem permaneceram acessíveis. O foco de link de foto tinha contorno visível de 3 px. Não se declara auditoria completa de acessibilidade.

A direção Mineral existente foi mantida: tipografia e espaçamento consistentes, hierarquia de evidências, citação com borda e avisos com superfície discreta. Avaliação visual: design 7/10, originalidade 6/10, acabamento 7/10 e funcionalidade 7/10; composição simples e legível, com rolagem vertical longa em telas pequenas como limite conhecido. Aprovação visual destes estados controlados não substitui qualidade real do modelo.
