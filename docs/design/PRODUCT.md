# Briefing do produto para design

Atualização de 2026-11-13: o briefing e os cenários abaixo explicam o laboratório original. A aplicação implementada e os limites de cada feature estão no [estado atual](../status-atual.md); as convenções atuais estão em [implementation.md](implementation.md).

Fonte: [PRD](../PRD.md), [stack aprovada](../stack.md) e direção visual escolhida na conversa. O usuário autorizou a criação destes artefatos visuais após a etapa de documentação da arquitetura.

O Garimpei atende inicialmente o próprio idealizador, começando na compra de usados para revenda. Ele seleciona categorias e produtos por nome/modelo, explora anúncios, avalia funcionamento e compara referências e custos antes de abrir a oferta na plataforma de origem. A negociação acontece fora do sistema.

O MVP será local, com Django/templates/HTMX, PostgreSQL e worker, somente neste computador, via localhost e sem login. A prioridade visual é leitura confortável no navegador de desktop. A adaptação a janelas estreitas permite avaliar a interface; não adiciona acesso em rede ou aplicativo móvel ao escopo.

## Pergunta que o protótipo resolve

Qual composição ajuda a encontrar uma oferta e compreender sua estimativa com menos esforço: exploração editorial por produto, tabela comparativa ou lista com prévia? As três usam as mesmas ofertas fictícias e o mesmo cálculo demonstrativo para tornar a comparação útil.

## Requisitos que orientam as telas

- Três abas de condição, com classificação manual de ofertas incertas.
- Nenhum corte por lucro mínimo; valores zero/negativos e estimativa indisponível permanecem visíveis.
- Referências de usados separadas da referência de novo, sem tratar anúncio como venda realizada.
- Trio financeiro obrigatório na evolução F20: preço de compra, preço de venda estimado e lucro estimado juntos, nessa ordem, com maior destaque visual para o lucro e compra/venda próximas e legíveis. Cards/detalhes usam hierarquia tipográfica; novas mensagens destacam rótulo/valor do lucro em negrito. Taxa provisória configurável explicada nos detalhes. Retirar frete/transporte dos campos, filtros, rótulos e novas mensagens.
- Interesses por categorias e por nome/modelo; configuração de CEP e percentual de taxa, sem custo logístico.
- Exemplos de alertas individuais, carga inicial silenciosa e confirmação incerta de envio.

Os protótipos preservam cenários históricos e não comprovam a nova apresentação F20. Os produtos, preços, CEP, distâncias, tempos, amostras e mensagens são fictícios. Não demonstram integração, viabilidade econômica ou disponibilidade de entrega. A taxa de 12% e frete de R$ 35 são dados do cenário, não padrões aprovados do produto. A interface de histórico de alertas é uma proposta de visibilidade operacional, sem decisão de armazenamento, retenção ou novas ações de envio.

As decisões de primeiro uso, classificação, atualização e volume estão no [PRD](../PRD.md). A [versão 0.2](flows-reference.md) demonstra fluxo guiado com custos em branco, correção, gravação pendente/falha, atualização ao clicar, paginação e dados ausentes. São simulações em memória; durabilidade e integrações precisam da implementação.
