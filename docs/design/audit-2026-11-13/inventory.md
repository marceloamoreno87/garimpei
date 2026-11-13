# Inventário da interface implementada

Leitura dos 38 templates atuais e dos módulos de estilos/scripts correspondentes. “Renderizada” significa observação pelo Chromium do laboratório próprio; “código” não equivale a exercício de todos os estados em uma conta real.

A matriz contém configuração em três etapas, primeiro uso sem ofertas, lista normal, defeitos, condição incerta, busca vazia, última página, detalhes normais/incertos, configuração salva, acompanhamento, sugestões, erro de sugestões, backups, integrações, IA e erros 400/404 de ofertas. Cada cenário foi verificado em 1440, 768, 375 e 320 px.

| Template | Papel | Formulários / disclosures | Avaliação e cobertura |
|---|---|---:|---|
| `base.html` | Estrutura compartilhada | 0 / 0 | Renderizada nas páginas da matriz. |
| `inference/error.html` | Página de erro | 0 / 0 | Código e shell examinados; erros de formulário/CSRF/consulta exercitados pelos testes HTTP aplicáveis. Nem todas as combinações foram capturadas. |
| `inference/status.html` | Página | 1 / 0 | Renderizada na matriz ou no fluxo de recuperação. |
| `integration/error.html` | Página de erro | 0 / 0 | Código e shell examinados; erros de formulário/CSRF/consulta exercitados pelos testes HTTP aplicáveis. Nem todas as combinações foram capturadas. |
| `integration/facebook_notice.html` | Fragmento / componente | 2 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `integration/settings.html` | Página | 3 / 1 | Renderizada na matriz ou no fluxo de recuperação. |
| `integration/whatsapp_status.html` | Fragmento / componente | 1 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. Estados com fotos, conflitos, resultados multimodais e conta real exigem rodada complementar. |
| `listing/alert_diagnostic.html` | Fragmento / componente | 0 / 1 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `listing/assessment.html` | Fragmento / componente | 0 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. Estados com fotos, conflitos, resultados multimodais e conta real exigem rodada complementar. |
| `listing/detail.html` | Página legada / recuperação | 1 / 1 | Código examinado; detail renderizado no erro 404; list preservado como caminho legado. |
| `listing/exploration.html` | Página | 0 / 0 | Renderizada na matriz ou no fluxo de recuperação. |
| `listing/exploration_error.html` | Página | 0 / 0 | Renderizada na matriz ou no fluxo de recuperação. |
| `listing/financial_values.html` | Fragmento / componente | 0 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `listing/layout.html` | Estrutura compartilhada | 0 / 0 | Renderizada nas páginas da matriz. |
| `listing/list.html` | Página legada / recuperação | 0 / 0 | Código examinado; detail renderizado no erro 404; list preservado como caminho legado. |
| `listing/offer_detail.html` | Página | 1 / 1 | Renderizada na matriz ou no fluxo de recuperação. |
| `listing/results.html` | Fragmento / componente | 1 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `listing/updates.html` | Fragmento / componente | 0 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `media/gallery.html` | Fragmento / componente | 1 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. Estados com fotos, conflitos, resultados multimodais e conta real exigem rodada complementar. |
| `monitoring/cost_fields.html` | Fragmento / componente | 0 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `monitoring/csrf_error.html` | Página de erro | 0 / 0 | Código e shell examinados; erros de formulário/CSRF/consulta exercitados pelos testes HTTP aplicáveis. Nem todas as combinações foram capturadas. |
| `monitoring/error.html` | Página de erro | 0 / 0 | Código e shell examinados; erros de formulário/CSRF/consulta exercitados pelos testes HTTP aplicáveis. Nem todas as combinações foram capturadas. |
| `monitoring/form.html` | Página | 1 / 0 | Renderizada na matriz ou no fluxo de recuperação. |
| `monitoring/interest_fields.html` | Fragmento / componente | 0 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `monitoring/layout.html` | Estrutura compartilhada | 0 / 0 | Renderizada nas páginas da matriz. |
| `monitoring/region_fields.html` | Fragmento / componente | 0 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `monitoring/tracking.html` | Página | 0 / 0 | Renderizada na matriz ou no fluxo de recuperação. |
| `navigation/error.html` | Fragmento / componente | 0 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `navigation/error_page.html` | Página | 0 / 0 | Renderizada na matriz ou no fluxo de recuperação. |
| `navigation/progress.html` | Fragmento / componente | 1 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `navigation/suggestions.html` | Página | 0 / 1 | Renderizada na matriz ou no fluxo de recuperação. |
| `operations/backups.html` | Página | 1 / 0 | Renderizada na matriz ou no fluxo de recuperação. |
| `operations/error.html` | Página de erro | 0 / 0 | Código e shell examinados; erros de formulário/CSRF/consulta exercitados pelos testes HTTP aplicáveis. Nem todas as combinações foram capturadas. |
| `operations/feedback.html` | Fragmento / componente | 0 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `operations/status.html` | Fragmento / componente | 1 / 0 | Código examinado; observado na composição da página quando há dados no laboratório. |
| `valuation/identity.html` | Fragmento / componente | 1 / 2 | Código examinado; observado na composição da página quando há dados no laboratório. Estados com fotos, conflitos, resultados multimodais e conta real exigem rodada complementar. |
| `valuation/identity_error.html` | Página de erro | 1 / 0 | Código e shell examinados; erros de formulário/CSRF/consulta exercitados pelos testes HTTP aplicáveis. Nem todas as combinações foram capturadas. |
| `valuation/research.html` | Fragmento / componente | 0 / 2 | Código examinado; observado na composição da página quando há dados no laboratório. Estados com fotos, conflitos, resultados multimodais e conta real exigem rodada complementar. |

## Componentes e estados

| Família | Componentes e estados inventariados | Refinamento / evidência |
|---|---|---|
| Shell | Marca, navegação global, página selecionada, cabeçalho, skip link, menu estreito | Matriz, testes de rota, teclado e toque sintetizado. |
| Configuração | Etapas, campos, ajuda/erro, escolhas, produtos, salvar/continuar, loading, conflito de revisão, erro de rede, configuração confirmada | Formulários reais, erro 422, transporte abortado, foco e retenção de valores. |
| Ofertas | Abas, busca, categoria, limpar, cards editorial/grade, dados financeiros, paginação, primeiro uso, coleta pendente, recorte vazio, atualizações | Matriz, fluxo HTMX e navegação sem JavaScript. |
| Detalhes | Referências, fotos, origem, custos, identidade/atributos, classificação, diagnóstico de alerta, avaliação multimodal | Matriz com dados sintéticos; código e testes existentes para caminhos condicionais. Não equivale a validação visual de cada estado raro. |
| Integrações | Facebook ausente/expirado/em confirmação, importação avançada, WhatsApp desconectado/pareamento/conectado, grupo/alertas, IA disponível/indisponível/pausada | Ausência/indisponibilidade e disclosure observados; conta real e inferência não acionadas. |
| Operação | Coleta/etapas, contagens, retomada, percurso carregando/erro/retentativa, pesquisa, sugestões vazias/preenchidas, catálogo de backups/exportação | Matriz, recuperação do carregamento e testes HTTP, incluindo criação/exportação de backup. |
| Feedback global | Hover, foco, seleção, disabled, loading, aviso, falha, recuperação, valores ausentes/zero/negativos | Vocabulário comum, testes de interação e ampliação de texto. |

Não foram encontrados modais, painéis sobrepostos, dropdowns autorais ou tabelas complexas na interface Django atual. Os selects/disclosures são controles nativos. Não foi criado um novo padrão de overlay para preencher esse inventário. O laboratório histórico de protótipos/Storybook possui superfícies de demonstração próprias e permanece fora da implementação auditada.
