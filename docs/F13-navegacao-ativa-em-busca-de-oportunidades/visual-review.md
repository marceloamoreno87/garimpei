# Avaliação visual — F13

A avaliação aplicou `frontend-ui-design` e suas quatro dimensões, com exame das imagens produzidas por `playwright-cli`, além do DOM e dos efeitos persistidos. As imagens representam somente dados sintéticos de laboratório próprio. O design segue `docs/design/DESIGN.md`: verdes escuros, fundo claro, tipografia existente e ações explícitas, sem introduzir outra biblioteca de componentes.

| Dimensão | Nota | Evidência e limite |
|---|---:|---|
| Design Quality (2×) | 7 | Cabeçalho, títulos, texto de contexto e ações mantêm identidade visual comum. Estados e evidência usam a mesma hierarquia; o painel extenso exige rolagem. |
| Originality (2×) | 6 | Original/alias, revisão, pendências e orçamento apresentam decisões específicas do Garimpei. O uso de blocos e links continua convencional. |
| Craft (1×) | 7 | Imagens desktop e 360 px mostram texto legível, espaçamento consistente e ações sem sobreposição. Dez evidências tornam a página longa, preservando cada link. Não foi feita certificação formal de contraste/WCAG. |
| Functionality (1×) | 8 | Atualização explícita por Enter, erro recuperável com leitura preservada, suspensão com recuperação e prévia editável sem adoção implícita foram exercitados. |

Pontuação ponderada: `(7×2 + 6×2 + 7 + 8) / 6 = 6,83/10`. Nenhuma dimensão atingiu o limiar de reprovação ≤3. Não há pretensão de originalidade excepcional; a interface é sóbria e adequada ao acompanhamento operacional.

## Imagens examinadas

- [Progresso desktop](evidence/progress-desktop.png): original PlayStation 5 Slim e termo PS5 Slim aparecem separados; revisão, contagem e avanço útil são visíveis.
- [Progresso 360 px](evidence/progress-360.png): ação de atualização, parciais e próxima ação permanecem acessíveis sem overflow horizontal.
- [Espera da fonte 360 px](evidence/suggestions-wait-360.png): motivo traduzido e próxima tentativa, orçamento 45 s/300 s e consumo são apresentados.
- [Teto 100 registros/10 evidências](evidence/suggestions-caps-360.png): limite é explicitado, dez links persistidos continuam visíveis e a ação de configurar não desaparece.
- [Suspensão 360 px](evidence/suspended-360.png): texto de recuperação manual substitui retomada indevida; progresso anteriormente confirmado permanece.

Os logs `ui-before`, `ui-backend-change`, `ui-before-action` e `ui-after-action` comprovam um contador real no PostgreSQL passando de duas para três páginas: a leitura permaneceu em duas após a alteração de backend e passou a três somente após Enter em Atualizar percurso. A URL `?pagina=2&q=slim` foi preservada. `ui-refresh-failure.txt` registra quatro blocos antes/depois de erro 503, com erro recuperável sem substituir a leitura anterior.

A sequência `ui-adoption-before`, `ui-adoption-after-failure`, `ui-adoption-after-save` confirma dois interesses na prévia e após falha SQL, e três somente depois de salvar. A proposta continua editável após erro; o teste integrado atual comprova coleta e origem ativa após a gravação. Os controles foram usados por teclado. A ausência de clipping observada é limitada aos tamanhos/cenários capturados, sem afirmar cobertura de todos os dispositivos.
