# Auditoria e refinamento da interface Django

Data: 2026-11-13. Escopo: interface implementada em `apps/backend/src/garimpei/infra/http/`, com a direção Mineral aprovada em [MASTER.md](../MASTER.md). Modo de uso: operar um produto local, com prioridade para encontrar ofertas, entender estimativas e acompanhar a execução.

Foram examinados os **38 templates** atuais, seus estilos e scripts autorais. A verificação renderizada percorreu **20 telas/estados em quatro larguras**, além de testes de interação e adaptação. O [inventário](inventory.md) distingue páginas, fragmentos e caminhos legados. Os protótipos históricos não foram redesenhados.

## Diagnóstico original

A identidade já era coerente: papel claro, verde mineral, Bricolage Grotesque para títulos e Manrope para leitura. O principal problema era a expansão da aplicação sem uma estrutura compartilhada igualmente completa. Algumas páginas ficavam sem indicação no menu; informações fixas pareciam configuração real; filtros, avisos e estados operacionais competiam com a tarefa principal.

Havia também defeitos de continuidade: a troca de condição perdia o foco, erros de consulta podiam ser tratados como falhas de gravação em outro formulário e uma oferta inexistente não apresentava título principal. Esses problemas aumentavam o esforço de orientação, apesar de cada tela isolada parecer utilizável.

## Avaliação heurística e correções

P1 indica dificuldade significativa; P2, fricção com alternativa disponível. Frequência e custo são estimativas pela presença dos componentes e pela jornada, sem pesquisa quantitativa com usuários.

| ID | Prioridade / frequência / custo | Problema e impacto original | Refinamento realizado | Princípios aplicados |
|---|---|---|---|---|
| UX01 | P1 / global / alto | Acompanhamento e páginas secundárias não identificavam a localização atual. Sugestões e IA tinham acesso indireto. | Menu com seis destinos, agrupados por tarefa, seleção derivada da rota e contexto no cabeçalho. | Nielsen: consistência e visibilidade; Jakob; reconhecimento; information scent; wayfinding. |
| UX02 | P1 / global / médio | “São Paulo · SP” era texto fixo, inclusive antes de configurar a região. | Remoção da informação geográfica sem origem; indicação verdadeira de execução neste computador. | Correspondência com o mundo real; prevenção de interpretação incorreta. |
| UX03 | P1 / troca de condição / alto | Após o HTMX substituir a lista, o foco ficava no `body`. | Foco na aba selecionada; busca preserva texto e cursor; filtragem e paginação levam ao resumo dos resultados. | Controle do usuário; continuidade; reconhecimento; acessibilidade por teclado. |
| UX04 | P1 / falhas de rede / alto | Um erro de polling podia inserir mensagem de gravação no primeiro formulário da página. Timeout não tinha o mesmo tratamento. | Tratamento limitado ao formulário responsável, feedback focável e preservação dos campos; timeout com recuperação equivalente. | Nielsen: diagnóstico e recuperação; feedback imediato; tolerância a erros. |
| UX05 | P1 / estados de erro / alto | Oferta inexistente sem `h1`, com mensagem de alteração e recarga sem saída útil; erro de Sugestões era fragmento sem página. | Título contextual, ação para explorar outras ofertas e página completa de erro em Sugestões/configuração. | Orientação; informação acionável; liberdade e recuperação. |
| UX06 | P2 / primeiro uso / médio | Lista vazia ainda mostrava filtros, ordenação e paginação redundantes. | Primeiro uso concentrado na configuração; filtros aparecem quando existe uma revisão publicada; paginação só quando necessária. | Hick-Hyman; carga cognitiva; progressive disclosure; Tesler. |
| UX07 | P2 / filtros / médio | Grade previa quatro colunas para três controles; limpeza aparecia apenas depois de chegar ao vazio. | Proporção busca/categoria/ações e limpeza junto aos filtros ativos. | Gestalt: proximidade e agrupamento; Fitts; custo de interação. |
| UX08 | P2 / páginas longas / médio | Detalhes e acompanhamento exigiam percorrer todo o conteúdo para localizar uma seção. | Atalhos locais para estimativa, referências, identidade, alertas, funcionamento e etapas operacionais. | Information foraging; hierarquia; reconhecimento; navegação contextual. |
| UX09 | P2 / global / médio | Estilos genéricos de `nav a` afetavam navegação principal, abas, paginação e links locais. | Estilos do menu limitados à navegação principal; linguagem explícita para abas e navegação de seções. | Consistência de interação; similaridade; Prägnanz. |
| UX10 | P2 / valores financeiros / médio | Regras sucessivas podiam reduzir números para menos que o corpo; lucro negativo e indisponível recebiam verde de sucesso. | Tipos estáveis, compra/venda alinhadas e lucro destacado. Perda usa vermelho sem remover o sinal; indisponibilidade usa texto neutro; zero continua visível. | Hierarquia perceptual; semântica de cores; legibilidade; efeito estética-usabilidade. |
| UX11 | P2 / telas estreitas / alto | O menu completo consumia muito espaço antes da tarefa principal. | Menu recolhível com `aria-expanded`, abertura por toque/teclado, fechamento por Escape e restauração do foco. Sem JavaScript, os destinos continuam disponíveis. | Adaptação por prioridade; Fitts; controle e liberdade. |
| UX12 | P2 / global / médio | Variações de foco, token inexistente na IA, avisos deslocados e seções de texto sem agrupamento uniforme. | Foco compartilhado, token Mineral correto, avisos proporcionais e ritmo comum de seções, formulários, leitura e estados selecionados. | Fluência perceptual; figura-fundo; alinhamento; ritmo espacial; consistência. |
| UX13 | P2 / acompanhamento / médio | Falha no carregamento inicial do percurso podia deixar “Carregando…” sem recuperação. | Mensagem específica, botão de nova tentativa e manutenção da leitura anterior quando já existe. | Visibilidade do estado; recuperação; responsividade percebida. |

As regras de negócio, os cálculos, a ordem compra → venda estimada → lucro e a aplicação explícita das atualizações permanecem os mesmos. A classificação de perda/indisponibilidade acrescentada à apresentação usa o resultado já calculado.

## Harmonização incorporada

- **Navegação:** um destino atual por rota; grupos estáveis; menu adaptável; navegação local para conteúdo longo; títulos de navegador específicos para configuração e oferta.
- **Composição:** grade proporcional de filtros, alinhamento de valores e ações dos cards, separação de grupos e avisos globais mais compactos. Os avisos dentro de Integrações seguem a largura da própria seção.
- **Tipografia e cores:** famílias existentes, escala em `rem`, numerais tabulares, cores semânticas existentes e ausência de redução automática dos valores para fontes minúsculas.
- **Componentes:** controles principais de pelo menos 44 px, estados de seleção em escolhas, foco comum, contraste de placeholders e affordance de `summary`.
- **Feedback:** mensagens associadas à operação correta; erros focáveis; campos preservados; status de resultados anunciado; polling de Facebook/WhatsApp suspenso em aba oculta e enquanto o usuário interage com a área correspondente.
- **Semântica:** relação entre abas e painel, lista de definições operacional corrigida, título e recuperação em erros, atributos de preenchimento obrigatório em CEP/taxa e destino correto após falha de CSRF.

Os valores de cor, família, escala e raios continuam em [tokens.json](../tokens.json), sem uma paleta paralela. As convenções para a aplicação estão em [implementation.md](../implementation.md).

## Validação e evidências

| Verificação | Resultado e limite |
|---|---|
| Inventário | 38 templates examinados no código; estado renderizado e cobertura por família no [inventário](inventory.md). |
| Navegador | 80 combinações: 20 telas/estados × 1440, 768, 375 e 320 px. Um `h1`, um destino atual e nenhum overflow horizontal em todas. |
| Acessibilidade automatizada | Axe com tags WCAG 2 A/AA, 2.1 A/AA e 2.2 AA: zero violações e zero verificações incompletas nas 80 combinações. Isso não certifica conformidade integral. |
| Interações | 22 checks: abas, setas/Home, foco, busca, filtros, paginação, contexto de detalhes, erros de formulário/rede, divulgação de campos avançados, skip link, funcionamento sem JavaScript e estados financeiros. |
| Adaptação | 25 checks: menu, Escape, toque sintetizado no Chromium, texto a 200% em oito páginas/duas larguras, nova tentativa do percurso, cores forçadas e redução de movimento. |
| Unidade e regressões rápidas | 499 testes aprovados na execução final: 486 unitários + 13 HTTP de navegação, formulário e recuperação. |
| Suíte HTTP ampla | 22 aprovados e um inicialmente impedido pela reserva mínima de armazenamento para backup. O teste restante passou ao usar diretório privado fora do checkout e com espaço disponível. |
| Financeiro | Teste HTTP de apresentação financeira reexecutado e aprovado após ajustar os estados visuais; valores, sinais e indisponibilidade preservados. |
| Gates Python | Seis grupos aprovados: tipos, lint/templates, limites de dependências, arquitetura, ciclos e código/dependências não utilizados. Sintaxe dos scripts alterados verificada com `node --check`. |

O diagnóstico da falha de backup confirmou `archive_storage_limit`: `/tmp` dispunha de aproximadamente 694 MiB, abaixo da reserva de 1 GiB. Nenhuma proteção de armazenamento foi reduzida. A repetição aprovada usou um diretório privado no disco com espaço disponível.

Resultados completos: [matriz](browser-results.json), [interações](interaction-results.json), [adaptação](adaptive-results.json) e [registro de validação](validation.json). Screenshots em [evidence/](evidence/), com dados sintéticos, sem autenticar contas reais, coletar novas ofertas reais ou enviar mensagens ao usuário.

Comparações úteis:

| Área | Antes | Depois |
|---|---|---|
| Integrações | [Desktop original](evidence/before-integrations.png) | [Desktop refinado](evidence/after-integrations-1440.png) |
| Ofertas | [Primeiro uso original](evidence/before-offers.png) | [Primeiro uso refinado](evidence/after-setup-offers-1440.png), [ofertas em desktop](evidence/after-offers-desktop-viewport.png), [ofertas em janela estreita](evidence/after-offers-mobile-viewport.png) |
| Detalhes | A avaliação inicial registrou a estrutura no código; não há captura anterior comparável com os mesmos dados. | [Detalhes em janela estreita](evidence/after-detail-375.png) |
| Recuperação | Falta de contexto/foco observada em navegador e código. | [Erro de rede ao salvar](evidence/after-save-network-error.png), [erro de consulta](evidence/after-offer-error-375.png) |

## Avaliação qualitativa

Notas de design review, baseadas nas capturas e no comportamento observado. São julgamento profissional, sem estudo de satisfação ou tempo de tarefa. Design e originalidade têm peso 2; acabamento e funcionalidade, peso 1.

| Dimensão | Antes | Depois | Evidência |
|---|---:|---:|---|
| Design | 7 | 8 | Identidade Mineral preservada; menu, seções e apresentação financeira agora seguem hierarquia comum. |
| Originalidade | 7 | 7 | Composição editorial já era uma decisão própria do Garimpei. Preservá-la foi mais adequado que introduzir outra estética. |
| Acabamento | 6 | 8 | Estados visuais, alvos, foco, agrupamento e reflow corrigidos; capturas e medições nas quatro larguras. |
| Funcionalidade | 6 | 8 | Fluxos de filtro/retorno/recuperação verificados; testes de usuário e integrações reais continuam fora desta avaliação. |
| **Média ponderada** | **6,67** | **7,67** | Não representa aprovação de contratos de feature. |

O resultado é uma interface mais previsível e coesa, com menos esforço para localizar tarefas e retomar uma operação. O refinamento aparece principalmente na continuidade e na precisão dos estados, preservando a linguagem editorial original.

## Pendências e limites

- Leitor de tela real, Safari/Firefox, dispositivo físico e sessões de usabilidade com o usuário não foram exercitados. O toque foi sintetizado no Chromium; 200% foi verificado por ampliação do tamanho-base do texto, não por todos os mecanismos de zoom dos navegadores.
- A rodada usou fontes e dados controlados. Pareamento real por QR, conta/grupo real do WhatsApp, desafios reais do Facebook e uma inferência na GPU não foram acionados por esta auditoria. Os testes HTTP usam integrações controladas.
- A galeria, o detalhamento multimodal e os estados históricos/raros foram avaliados no código e pela estrutura compartilhada. A matriz não cobre cada combinação possível de foto disponível/removida, evidência de IA e conflito de classificação com dados reais. A inspeção presencial e a comprovação de funcionamento do produto continuam sendo informações do domínio, sem mudanças nesta rodada.
- As capturas de configuração com muitas categorias continuam longas; a hierarquia foi organizada, sem alterar o catálogo ou esconder opções existentes.
- Não foram medidos Core Web Vitals nem melhorias quantitativas de desempenho, produtividade ou conversão.
- O launcher do Impeccable não executou por permissão do arquivo. O contexto foi lido diretamente; o detector dessa ferramenta não foi executado. A evidência técnica vem do navegador, axe, testes e gates efetivamente executados.
- A documentação/protótipos históricos mantêm seus próprios avisos de versão. Esta entrega registra a aplicação atual sem atribuir implementação nova ao histórico nem alterar o progresso das features.

## Reproduzir

Use duas instâncias próprias e descartáveis: uma configurada com as ofertas sintéticas de `tests.factories.exploration` e outra no primeiro uso. Execute `./scripts/init.sh` conforme a configuração privada de cada instância e abra uma sessão própria com `playwright-cli -s=garimpei-ux open URL`.

Na raiz, substituindo as portas pelas resolvidas para suas instâncias:

```bash
python3 docs/design/audit-2026-11-13/run-verification.py --app-origin http://127.0.0.1:PORTA_APP --setup-origin http://127.0.0.1:PORTA_SETUP --check matrix
python3 docs/design/audit-2026-11-13/run-verification.py --app-origin http://127.0.0.1:PORTA_APP --setup-origin http://127.0.0.1:PORTA_SETUP --check interactions
python3 docs/design/audit-2026-11-13/run-verification.py --app-origin http://127.0.0.1:PORTA_APP --setup-origin http://127.0.0.1:PORTA_SETUP --check adaptive
```

Os roteiros são executados pelo `playwright-cli`; não criam um projeto paralelo de E2E. A verificação de formulário envia uma entrada inválida e simula falha de rede apenas na instância de primeiro uso. Não execute as verificações em uma instalação de uso real. Encerre as sessões/processos próprios com o CLI e os scripts do projeto.

Referências normativas consultadas: [padrão de abas WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/), [WCAG 2.2 — tamanho mínimo de alvos](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum). O mínimo AA de alvos é 24 × 24 CSS px, com exceções; 44 px foi mantido como padrão ergonômico do design do Garimpei.
