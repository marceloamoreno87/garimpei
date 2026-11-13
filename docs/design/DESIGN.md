# Regras visuais e de interação

Leia [MASTER.md](MASTER.md) para a direção e [tokens.json](tokens.json) para os valores. A [referência de fluxos](flows-reference.md) detalha a versão 0.2 e sua [verificação](verification-v02.md) registra evidências atuais. A [avaliação inicial](review.md) permanece como histórico da versão 0.1.

## Composição

Desktop usa navegação lateral, faixa de contexto e área de leitura com largura limitada. A navegação agrupa exploração/interesses/alertas e separa configurações. “Design system” e a barra de comparação pertencem ao laboratório, não ao menu final do MVP.

Na composição editorial, a primeira oferta segue a ordenação por lucro e recebe foto e painel de resumo lado a lado. O destaque é hierarquia de leitura, sem recomendação comercial adicional. As seguintes formam uma grade de três, duas ou uma coluna conforme o espaço. A tabela oferece comparação densa; a mesa de análise usa seleção e prévia. Abaixo de 720 px, a navegação recolhe e a composição editorial empilha imagem e conteúdo. Em 1100 px, detalhes e formulários passam a uma coluna. A tabela mantém sua própria rolagem horizontal.

A composição editorial foi escolhida para o MVP. As outras duas composições permanecem estudos. Primeiro uso guiado, aplicação de novos dados ao clicar e correção de classificação já estão no protótipo, conforme [PRD](../PRD.md) e [referência de interação](flows-reference.md). Em janelas estreitas, as três abas quebram texto para permanecer inteiramente visíveis. A largura da navegação acompanha a escala de texto.

Títulos usam Bricolage Grotesque, com peso 600 e espaçamento compacto. Corpo e controles usam Manrope. O corpo base é 16 px; informação secundária usa as escalas menores. Texto auxiliar de 10–12 px fica restrito a metadados do laboratório e etiquetas. Preços usam numerais tabulares, alinhamento consistente e formatação pt-BR. Valores com centavos preservam duas casas quando necessário.

## Componentes

| Componente | Regras |
|---|---|
| Botão | Primário mineral para ação principal; secundário com contorno; rótulo com verbo; loading impede novo acionamento |
| Campo | Rótulo visível, ajuda associada e erro junto ao campo; resumo de erros recebe foco e aponta para os campos |
| Aba de condição | Texto e quantidade; selecionada com marca inferior; setas/Home/End movem o foco e a seleção |
| Filtro | Busca preserva foco ao atualizar resultados; categoria informa estado pressionado; modalidade tem rótulo acessível |
| Oferta | Foto ilustrativa, condição quando pertinente e ação de detalhes; na F20, compra → venda estimada → lucro juntos, com lucro em maior destaque tipográfico e os demais valores próximos e legíveis; preservar sinal e indisponibilidade |
| Detalhes | Comparáveis e referência de novo separados; na F20, compra → venda estimada → lucro juntos, com lucro em maior destaque tipográfico e taxa explicada na composição; ação de origem ao fim da avaliação |
| Nova mensagem F20 | Compra → venda estimada → lucro em sequência, com rótulo e valor do lucro em negrito; preservar qualificação de estimativa e sinal |
| Aviso | Título específico, motivo e recuperação; cor acompanha o significado sem substituir texto |
| Confirmação | Descreve apenas a ação simulada realizada; anúncio original e mensagens identificam a demonstração |

## Estados e conteúdo

| Estado | Apresentação proposta |
|---|---|
| Carregando | Skeleton com `aria-busy` e descrição textual, sem valores inventados |
| Sem interesses/ofertas | Explicação e ação para configurar interesses |
| Filtros sem resultados | Recuperação por “Limpar filtros” |
| Falha de coleta | Aviso mantém última informação disponível; tentativa é explicitamente simulada |
| Carga inicial | Indicação de preenchimento silencioso, sem alertas |
| Estimativa indisponível | Oferta preservada; revenda e lucro não viram zero; custos conhecidos continuam visíveis |
| Lucro zero/negativo | Valor visível, sinal e texto; não remove oferta |
| Funcionamento incerto | Terceira aba e ação de classificação nos detalhes |
| Defeito/reparo/peças | Aba separada, sem alerta e sem custo de reparo presumido |
| Envio com resultado incerto | Estado “A conferir”, sem afirmar entrega nem oferecer reenvio automático |

O painel de cenários altera a exploração. Gravação pendente, falha e recuperação são simuladas nos formulários e na classificação, mantendo a entrada e o último estado confirmado. O laboratório não possui I/O de gravação; persistência real e falhas do servidor precisam da implementação. Os estados incluem coleta parcial, acompanhamento parado, consulta indisponível e fallback de imagens.

## Acessibilidade e responsividade

Use HTML semântico, landmarks, um h1 por superfície e link para pular ao conteúdo. A navegação informa a página atual; abas e filtros expõem estado. Foco visível usa o token semântico e deve permanecer perceptível em fundos claros e escuros. Controles principais têm altura mínima de 44 px. A barra flutuante contém alguns controles compactos de avaliação e deve ser removida ao implementar o produto.

Feedback usa região viva; formulários inválidos recebem resumo focável, `aria-invalid` e mensagens associadas por `aria-describedby`. Ícones decorativos ficam fora da árvore acessível. Fotografias têm texto alternativo e indicação de imagem ilustrativa. Redução de movimento desativa animações e transições. Rolagem local da tabela preserva a largura da página.

O gerador verifica pares semânticos de texto em cada tema com mínimo de 4,5:1; isso é uma verificação parcial, não uma certificação WCAG. Leitor de tela, ampliação e cenários com dados reais precisarão de avaliação adicional na implementação.

## Passagem para Django/HTMX

Levar o CSS de tokens e componentes para os estáticos do produto; traduzir a marcação para includes de templates e extrair parciais para abas/resultados/detalhes. Rotas, validação do servidor, CSRF, falhas de I/O, concorrência e persistência pertencem aos contratos das features. O JavaScript demonstrativo não deve ser promovido como lógica de negócio: suas fixtures, fórmula ilustrativa e alternador são instrumentos de design. O laboratório HTML/Storybook pode continuar documentando os componentes enquanto o produto usa renderização Django.

## Aplicação Django — harmonização de 2026-11-13

A direção visual acima foi preservada no refinamento da aplicação. As [convenções de implementação](implementation.md) documentam menu por rota, navegação adaptável, foco após HTMX, estados financeiros e recuperação. O [relatório de auditoria](audit-2026-11-13/README.md) registra inventário, correções, capturas e limites da validação. Esses resultados dizem respeito à aplicação atual; as seções do protótipo continuam como histórico do laboratório.

A [verificação após integrar a master](audit-2026-11-13/integration-master.md) complementa essa rodada com o controle global do robô e a apresentação ouro, preservando os aceites e a pendência real de F21.
