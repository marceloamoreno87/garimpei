# Garimpei — Mineral

Status: direção visual clara/editorial e composição editorial escolhidas pelo usuário. O laboratório histórico é a versão 0.2; a aplicação Django foi implementada e refinada seguindo esta direção. Consulte [implementation.md](implementation.md) e a [auditoria](audit-2026-11-13/README.md) para o estado aplicado. Os fluxos e estados estão na [referência de interação](flows-reference.md), com [verificação própria](verification-v02.md).

## Intenção

O produto ajuda um iniciante a avaliar eletrônicos usados para revenda. A interface deve favorecer comparação e entendimento dos custos, sem transformar estimativa em promessa de ganho. Fotografias dão contexto; preço de compra, preço de venda estimado e lucro estimado aparecem juntos e com rótulos próprios na evolução F20. A taxa configurada é explicada nos detalhes; frete/transporte sai da apresentação financeira por decisão do usuário. Os protótipos históricos não comprovam essa atualização da aplicação.

A assinatura visual combina papel claro, tinta verde escura, verde mineral e títulos em Bricolage Grotesque. A oferta principal é dividida entre fotografia e leitura financeira. O restante mantém ritmo editorial com espaço entre grupos e alinhamento dos valores. Manrope sustenta controles, descrições e números. Ícones SVG compartilham traço e proporção.

## Autoridade e consumo

| Fonte | Responsabilidade |
|---|---|
| [PRD](../PRD.md) e [stack](../stack.md) | Comportamento confirmado, escopo e tecnologia do produto |
| Este documento | Direção visual e motivos |
| [tokens.json](tokens.json) | Valores de cores, tipografia, escalas, raios, temas e movimento |
| [generate_tokens.py](generate_tokens.py) → [tokens.css](tokens.css) | Exportação determinística e verificação de sincronização/contraste |
| [components/](components/) | Aparência e marcação compartilhadas entre galeria, protótipos e Storybook |
| [DESIGN.md](DESIGN.md) | Regras para combinar componentes e estados |

Altere tokens na fonte JSON e gere novamente o CSS. A implementação futura em templates deverá consumir o mesmo CSS; a conversão para Django não cria outra paleta. Geometria específica de uma composição fica nos templates `.css.in`; valores reutilizáveis que precisem virar uma regra devem ser promovidos a tokens. O gerador compila os breakpoints a partir do JSON e verifica drift nos três arquivos CSS gerados. Storybook executa essa verificação antes de dev/build.

Protótipos e Storybook compartilham também as funções que geram componentes HTML. Essa reutilização valida o vocabulário visual; a implementação futura deve reescrever interações e renderização em templates/HTMX com contratos e testes do produto.

## Decisões desta rodada

- Usar a composição editorial escolhida: produtos e compreensão dos custos têm prioridade sobre densidade de tabela para o usuário inicial.
- Reservar verde para ações e estimativas calculáveis; textos, sinais e ícones explicam os estados independentemente da cor.
- Na F20, dar maior destaque visual ao lucro estimado. Manter compra e venda estimada próximas e legíveis no mesmo grupo, na ordem compra → venda estimada → lucro; preservar rótulos, sinal e estados indisponíveis. Cards/detalhes usam hierarquia tipográfica, e novas mensagens destacam rótulo e valor do lucro em negrito.
- Manter lucro zero e negativo visíveis. Estimativa indisponível recebe explicação e preserva custos conhecidos.
- Usar uma página completa para detalhes: comparáveis e composição exigem leitura, não uma interrupção em modal.
- Separar incerteza de condição, indisponibilidade de estimativa e confirmação incerta de envio; são problemas diferentes.
- Manter duas composições alternativas para comparação. Tema escuro e alternador são recursos de estudo, sem requisito de entrega no MVP.

## O que esta rodada não decide

O [PRD](../PRD.md) já define o primeiro uso guiado, os custos inicialmente em branco e obrigatórios, a preservação e correção da classificação manual, a ausência de alerta pela classificação/correção e a aplicação de atualizações da lista ao clicar em um aviso. A tela preenchida do protótipo representa um cenário demonstrativo depois da configuração; não é a experiência de primeiro uso aprovada.

Continuam abertas integração, categorias reais, método/amostra de comparação, validações detalhadas e política de envio. A posição de ofertas sem estimativa no fim, o desempate pela identificação mais recente e as páginas de 20 foram escolhidos pelo usuário. Fluxo guiado, correção de classificação, aviso de atualizações e falhas recuperáveis agora são demonstrados em memória. Isso não comprova persistência, coleta, envio ou integração implementados no produto.
