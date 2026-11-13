# Contrato — F18 Identificação de produtos e busca ativa de comparáveis

*Gerado por spec-writer a partir do PRD. Alterações manuais são substituídas na regeneração.*

## Prerequisites

Condições futuras para exercer os itens; produzi-las integra a entrega. Ausência impede executar o item correspondente e não equivale a aprovação. Esta geração não declara pré-requisitos já satisfeitos.

### Runtime services

Django/worker/PostgreSQL isolados iniciados pelos scripts F02, Python 3.13 e dependências do lock, migrations e navegador disponíveis. F06/F12 e F13 entregues/avaliadas; a navegação complementar F13 é obrigatória para avaliar a base F18. Worker deve consumir efetivamente trabalho de pesquisa.

### Persistent state

- **Recorte ativo:** configuração e interesses já cadastrados, observações/revisões e cobertura correspondentes ao manifesto real. Usado por: UI-COVERAGE-01, E2E-VALUATION-02.
- **Estado controlado:** alvos/interesses/observações/correções/pesquisas/checkpoints dos casos SUFFICIENT, UNKNOWN, MISSING, CONFLICT, EXCLUSIONS, AGE_BOUNDARY, DISPERSION, NO_RESULTS, SOURCE_FAILURE, RETENTION, RACE, SHARED, GEOGRAPHY, MANUAL, NON_INTERFERENCE. Usado por todos os itens que nomeiam esses casos.
- **Histórico protegido:** configuração, condição manual e recibos confirmados/incertos com identidade/corpo conhecidos anteriores à pesquisa. Usado por: WRK-PRESERVATION-01, WRK-MANUAL-02, E2E-READING-01, E2E-IDENTITY-ALERT-01.

Criar estado em instância eval por migrations e factories existentes `tests/factories/runtime.py`, `listing.py`, `valuation.py`, estendidas por `comparable_research.py`; verificar os atributos declarados antes dos itens. O corpus controlado deve ser reproduzível sem dados privados implícitos.

### Static inputs

- `apps/backend/tests/fixtures/valuation/research_cases.json`: corpus versionado com os handles acima, relógio, campos/páginas/contextos, revisões, resultados e falhas. Usado por todos os itens com estado controlado.
- `docs/F18-identificacao-de-produtos-e-busca-ativa-de-comparaveis/evidence/interest-corpus.json`: recorte real sanitizado com data/revisão/hash e anotações humanas por interesse. Usado por: UI-COVERAGE-01, E2E-VALUATION-02.
- `docs/F18-identificacao-de-produtos-e-busca-ativa-de-comparaveis/evidence/limits.json`: todos os limites numéricos medidos de spec §3, perfis real/controlado e caminhos de evidência. Usado por: WRK-RESEARCH-01, WRK-BUDGET-01, WRK-BUDGET-02, WRK-RESUME-01, E2E-VALUATION-02.

Esses arquivos são entregáveis futuros. Produzir segundo spec §7 e conferir schema/hash/consistência; nenhum deles é pressuposto já criado pela especificação.

### Configuration

Usar `GARIMPEI_ENV_FILE` privado, `GARIMPEI_ENV=eval`, instância exclusiva e relógio controlado em UTC. Configuração de pesquisa/limites é central; manifesto ausente/inválido desabilita ativação automática e deixa F18-AC06 pendente. Rede fake somente loopback/eval segundo restrições existentes. Segredos/perfil/cookies não entram em relatórios.

### External dependencies

Facebook com perfil dedicado autorizado e contexto F11/F13 para prova real. Fakes nomeados de navegação/relógio/canal nas regressões, sem envio real implícito. F16 é pré-requisito somente de E2E-IDENTITY-ALERT-01: o item verifica integração condicional F18/F16, não amplia o DAG da base textual. Sem F16, registrar essa dimensão pendente, nunca sucesso simulado da política de envio.

## Quality gates

Cada gate deve passar para a feature ser considerada pronta; estes comandos não foram executados nesta geração.

- **Seis grupos Python** — `node scripts/run-gates.mjs` na raiz — tipos, lint, limites, arquitetura, ciclos e não utilizados, usando o runner Python real.
- **Regressões e integração** — `uv run --frozen --no-sync pytest tests/unit tests/http tests/integration tests/quality` em `apps/backend` — regras/HTTP e PostgreSQL isolado quando aplicável.
- **Suíte completa** — `uv run --frozen --no-sync pytest` em `apps/backend` — regressões com pré-requisitos de lifecycle disponíveis.
- **Navegador** — `playwright-cli`, segundo a skill do projeto — jornadas desktop/390 px e preservação de contexto.
- **Avaliação visual** — `frontend-ui-design`, segundo a skill do projeto — evidências das superfícies alteradas no design existente.

## Coverage Manifest

Texto dos critérios reproduzido literalmente do PRD. Cobertura define verificações futuras, não resultados aprovados. A dimensão F16 é condicional à integração disponível e permanece explicitamente pendente até sua execução; não é necessário instalar IA para a base textual.

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F18-AC01**: o conjunto de avaliação parte dos interesses já cadastrados, registra versão/data do recorte e apresenta por interesse famílias examinadas, atributos determinantes, reconhecimentos, lacunas de suporte/evidência e amostras insuficientes. Inclui casos positivos, ausentes e contraditórios; categoria disponível e capacidade de estimar são apresentadas distintamente, sem alegar suporte a toda categoria. | UI-COVERAGE-01, SVC-IDENTITY-01 |
| **F18-AC02**: quando faltam comparáveis para produto identificável, navegação complementar no Facebook obtém candidatos rastreáveis e os submete à mesma política F06 de equivalência, observação até 14 dias, filtro de discrepantes, mínimo de cinco retidos e dispersão. Sem dados suficientes, mantém indisponibilidade com motivo; a janela de publicação de 48 horas do primeiro alerta não é aplicada como idade máxima dos comparáveis. | WRK-RESEARCH-01, SVC-SAMPLE-01, WRK-RESEARCH-02 |
| **F18-AC03**: produto sem identidade não recebe mensagem de variante divergente; atributo ausente, incompatibilidade real, pendência de avaliação e falha de fonte têm motivos distintos e consistentes na lista, nos detalhes e no diagnóstico de alertas. | SVC-IDENTITY-01, UI-DIAGNOSTIC-01, UI-DIAGNOSTIC-02 |
| **F18-AC04**: acessórios, lotes, peças, parcelas/entradas e variantes incompatíveis não inflam a amostra; o próprio anúncio e repetições da mesma identidade são excluídos da contagem. Republicações seguem a política explícita disponível, sem prometer deduplicação entre IDs ainda não comprovada. | SVC-SAMPLE-02 |
| **F18-AC05**: em cenário controlado, uma oferta identificável inicialmente sem amostra suficiente recebe comparáveis pela busca complementar, produz estimativa F06 e composição F07 rastreáveis e pode habilitar primeira elegibilidade F16 quando disponível, sem duplicação. A prova real registra fonte, percurso, resultados, cobertura e limitações separadamente da fixture; acesso indisponível deixa a verificação externa pendente. | E2E-VALUATION-01, E2E-VALUATION-02, E2E-IDENTITY-ALERT-01 |
| **F18-AC06**: contrato fixa limites medidos de consultas, detalhes, duração, tentativas e prioridade e os exercita. Busca limitada, fonte indisponível ou entrada contraditória não causa repetição infinita nem bloqueia outros candidatos; orçamento, último progresso confirmado, motivo e próxima ação são consultáveis. Falha de acesso ou página inesperada não vira busca concluída sem resultados. | WRK-BUDGET-01, WRK-BUDGET-02, WRK-RESEARCH-02 |
| **F18-AC07**: família/modelo e atributos determinantes extraídos automaticamente apontam para a observação e trechos que os sustentam; valores corrigidos pelo usuário identificam origem manual, momento e observação examinada, sem inventar trecho de suporte. Atributo sem evidência nem correção permanece desconhecido, e conflito explícito não recebe correspondência forçada. O cenário textual funciona com F15/F19 indisponíveis; a configuração do interesse continua exigindo apenas os campos existentes. | SVC-IDENTITY-01, API-IDENTITY-01, UI-DIAGNOSTIC-02, E2E-VALUATION-01 |
| **F18-AC08**: repetir entrada idêntica ou retomar após queda reutiliza progresso válido sem duplicar candidatos/eventos nem repetir consultas sem respeitar a próxima tentativa. Se uma revisão nova mudar variante durante uma pesquisa, resultado antigo não substitui a identidade/avaliação vigente nem fornece amostra incompatível ao cálculo. | WRK-RESUME-01, WRK-RESUME-02 |
| **F18-AC09**: pesquisas e candidatos aceitos/rejeitados conservam termos, filtros solicitados/contexto observado, fonte/ID, link, preço conhecido, disponibilidade, data e motivos. O resultado calculável pode ser reproduzido a partir dessas evidências, sem seleção por lucro desejado; referência de novo não completa o mínimo de usados. Falha de atualização conserva avaliação anterior apenas enquanto aplicável e válida; vencimento propaga indisponibilidade sem apagar histórico. | SVC-SAMPLE-03, WRK-VALIDITY-01, SVC-SAMPLE-01 |
| **F18-AC10**: pesquisa complementar preserva interesses, configuração, decisões manuais e recibos existentes. Resultado obtido apenas como comparável não gera alerta por esse fato; se corresponder a interesse ativo, segue o fluxo normal. Com F16 disponível, oferta recente que se torna elegível é reavaliada e ofertas fora das 48 horas ou sem publicação confiável permanecem sem autorização de primeiro envio; reinício não duplica recibo ou transmissão incerta. | WRK-PRESERVATION-01, E2E-IDENTITY-ALERT-01 |
| **F18-AC11**: busca complementar conserva o mesmo contexto geográfico do monitoramento e registra parâmetros solicitados/contexto observado. Amostra insuficiente não amplia a região automaticamente; resultados de contexto divergente ou não comprovado não são apresentados como amostra local validada e a pesquisa conserva sua limitação explícita. | WRK-GEOGRAPHY-01, SVC-GEOGRAPHY-20-01, WRK-GEOGRAPHY-20-01, WRK-GEOGRAPHY-20-02 |
| **F18-AC12**: correção manual opcional de modelo/atributos fica vinculada à identidade do anúncio, mantém a observação original, registra autoria manual/momento/revisão e provoca reavaliação com a política F06. Não exige campos novos para cadastrar interesse, não altera condição manual nem se aplica automaticamente a outros anúncios. | API-IDENTITY-01, API-IDENTITY-02, WRK-MANUAL-01 |
| **F18-AC13**: coleta posterior contraditória conserva a correção e mostra os atributos em conflito; venda estimada/lucro aplicáveis e autorização de novos alertas ficam suspensos até revisão. Histórico e recibos permanecem consultáveis; resultado antigo não desbloqueia a oferta. Revisão explícita permite reavaliar a identidade resolvida, sujeita a dados suficientes e validade. | WRK-MANUAL-02, API-IDENTITY-03, WRK-RESUME-02 |
| **F18-AC14**: com F16 integrada, correção manual de identidade que complete a primeira elegibilidade pode autorizar primeiro envio dentro das 48 horas da publicação confiável, sem conflito e com todas as demais condições satisfeitas. Sem data confiável, fora da janela, com conflito, recibo confirmado ou transmissão incerta não autorizar novo primeiro envio. Correção apenas da condição conserva a regra F05/F16 de não alertar por essa ação isolada. | E2E-IDENTITY-ALERT-01 |

## Service

**Verification mode:** Consultar identidade, investigação, avaliação e bloqueio públicos consumidos por F06/F07/F08/alertas; observar resultados publicados, sem testar helpers isolados.

### Identificação explicável

#### `SVC-IDENTITY-01` — Origem e estados distintos
- given: casos SUFFICIENT, UNKNOWN, MISSING e CONFLICT do corpus controlado com revisões publicadas.
- when: consultar os resultados de identidade.
- then:
  - Atributos automáticos apontam para campo, trecho e revisão corretos.
  - Atributo ausente permanece desconhecido e identificado pelo nome.
  - Falta de identidade/suporte não é apresentada como variante divergente.
  - Conflito mostra valores explícitos incompatíveis e suas evidências.
  - Nome do interesse/categoria não completa atributo ausente.

### Política de comparáveis

#### `SVC-SAMPLE-01` — Política preservada
- given: casos SUFFICIENT, AGE_BOUNDARY e DISPERSION processados no relógio controlado.
- when: consultar a avaliação aplicável.
- then:
  - Mediana usa filtro inclusivo de 50% a 150%, mínimo de cinco retidos e razão máxima/mínima até 1,5.
  - Observações de até 14 dias participam quando elegíveis; futuras/vencidas não participam.
  - Publicação com mais de 48 horas não exclui, por si só, comparável com observação válida.
  - Novo permanece separado e não completa os cinco usados.
  - Insuficiência/dispersão/vencimento conservam motivo e não viram preço/lucro zero.

#### `SVC-SAMPLE-02` — Exclusões e identidade distinta
- given: caso EXCLUSIONS com alvo, repetições, variantes, acessórios, lotes, peças, defeitos/incerteza, entrada, parcela, troca e preço ausente.
- when: consultar candidatos e decisões.
- then:
  - O alvo não participa da própria amostra.
  - Cada fonte/ID contribui no máximo uma vez com a observação aplicável.
  - Os candidatos inelegíveis conservam motivos e não aumentam a amostra retida.
  - IDs diferentes não são fundidos apenas por título/foto semelhantes.
  - Preço ausente não é completado por IA ou referência de novo.

#### `SVC-SAMPLE-03` — Cálculo reproduzível
- given: caso SUFFICIENT com pesquisa e avaliação confirmadas.
- when: consultar o pacote de evidências.
- then:
  - Pesquisas conservam termos, filtros solicitados e contexto observado.
  - Candidatos conservam fonte/ID/link/preço conhecido/disponibilidade/revisão/data.
  - Decisões registram aceitação/rejeição e motivos em cada estágio.
  - O conjunto permite reproduzir preço e validade pela política publicada.
  - A seleção não depende do lucro desejado do alvo.

## HTTP API

**Verification mode:** Enviar requisições ao Django local; observar status, HTML/redirect e estado persistido diretamente pela ação.

### Correção e resolução de identidade

#### `API-IDENTITY-01` — Salvar correção opcional
- given: caso MANUAL com anúncio existente, revisão examinada atual e CSRF válido.
- when: enviar POST de correção válida a /ofertas/<id>/identidade/.
- then:
  - Retorna 303 para detalhes atualizados.
  - Registra revisão manual, valores, momento e observação examinada, sem sobrescrever a observação.
  - Não altera a condição manual nem outros anúncios/interesses.
  - A revisão salva fica disponível para reavaliação, sujeita à política F06.

#### `API-IDENTITY-02` — Entrada inválida não produz mutação parcial
- given: caso MANUAL e entradas com formato inválido, combinação inválida, revisão obsoleta ou CSRF ausente, em requisições independentes.
- when: enviar cada requisição inválida de identidade.
- then:
  - Formato inválido retorna 400; combinação inválida, 422; revisão obsoleta, 409; CSRF inválido, 403.
  - A resposta identifica o impedimento sem expor segredos.
  - A correção vigente e a evidência original permanecem intactas.
  - Família sem suporte não recebe identidade financeira fictícia.

#### `API-IDENTITY-03` — Resolver conflito explicitamente
- given: caso MANUAL com conflito vigente, revisão examinada atual e escolha válida de resolução.
- when: enviar POST de resolução a /ofertas/<id>/identidade/.
- then:
  - Registra a decisão e evidências examinadas numa nova revisão.
  - A identidade resolvida fica disponível para reavaliação.
  - Histórico de conflito e escolhas anteriores é preservado.
  - A ação não revalida amostra vencida nem autoriza envio sem os demais critérios.

#### `API-IDENTITY-04` — Ausência e falha de persistência
- given: caso MANUAL, com variantes de anúncio removido do ambiente de teste e falha de persistência injetada, em requisições independentes.
- when: enviar a correção de identidade para cada variante.
- then:
  - Anúncio ausente retorna 404 sem criar um anúncio pela edição.
  - Falha de persistência retorna 503 sem gravação parcial.
  - A resposta não apresenta falso sucesso nem expõe detalhes privados da falha.

## UI

**Verification mode:** Navegar em ofertas/detalhes/Acompanhamento e observar conteúdo e estados da revisão apresentada.

### Cobertura e diagnóstico

#### `UI-COVERAGE-01` — Recorte verificável
- given: recorte ativo do manifesto de corpus, com resultados processados e lacunas conhecidas.
- when: abrir o Acompanhamento.
- then:
  - Recorte informa versão/data e famílias/atributos examinados por interesse.
  - Reconhecimentos, lacunas de suporte/evidência e amostra insuficiente têm contagens explícitas.
  - Categoria selecionável não é apresentada como garantia de estimativa.
  - Interesse sem evidência não recebe cobertura fictícia.

#### `UI-DIAGNOSTIC-01` — Motivos coerentes
- given: casos UNKNOWN, MISSING, CONFLICT e SOURCE_FAILURE e pendência de avaliação, na mesma revisão publicada.
- when: abrir a lista de ofertas.
- then:
  - Produto não reconhecido, atributo ausente, incompatibilidade, pendência e falha de fonte têm motivos distintos.
  - O motivo coincide com o diagnóstico da mesma revisão entregue aos consumidores.
  - Compra conhecida permanece e venda/lucro indisponíveis não viram zero.

#### `UI-DIAGNOSTIC-02` — Evidência, correção e próxima ação
- given: casos SUFFICIENT, MISSING ou MANUAL com pesquisa/histórico disponíveis.
- when: abrir os detalhes da oferta.
- then:
  - Atributos automáticos mostram trechos e manuais mostram sua origem sem trecho inventado.
  - Correção é opcional e conflito oferece revisão explícita com ambos os valores.
  - Pesquisas/candidatos mostram links, preços pedidos, datas e razões de decisão.
  - Último progresso, teto/consumo, interrupção e próxima ação são consultáveis.
  - Texto externo é conteúdo escapado, sem autoridade para acionar ferramentas.

## Worker

**Verification mode:** Disparar trabalho persistente, processar com fonte controlada e observar publicações, percurso, fila e efeitos independentes.

### Pesquisa complementar

#### `WRK-RESEARCH-01` — Amostra além do catálogo inicial
- given: caso SUFFICIENT com identidade completa, menos de cinco no catálogo e limites medidos fixados.
- when: processar a investigação complementar.
- then:
  - Obtém candidatos adicionais pela navegação Facebook no contexto autorizado.
  - Persiste lotes confirmados com proveniência antes de concluir toda a busca.
  - Submete candidatos à política única F06.
  - Término informa suficiência válida ou motivo concreto de indisponibilidade.

#### `WRK-RESEARCH-02` — Vazio e falha distintos
- given: casos NO_RESULTS e SOURCE_FAILURE com vazio comprovado, timeout, página inesperada e acesso negado.
- when: processar uma fatia de cada caso.
- then:
  - Vazio confirmado mantém amostra insuficiente, sem afirmar cobertura integral.
  - Timeout/página inesperada conservam falha ou parcialidade, sem sucesso vazio fictício.
  - Acesso negado suspende navegação com recuperação manual.
  - Percurso confirmado e próxima ação permanecem consultáveis.

### Orçamento e prioridade

#### `WRK-BUDGET-01` — Limites medidos vinculantes
- given: manifesto de limites completo e casos controlados que excedem consultas/páginas/detalhes/duração/tentativas.
- when: processar uma rodada de investigação.
- then:
  - Cada unidade respeita os tetos fixados e o prazo restante antes de nova chamada.
  - Esgotamento preserva consumo/checkpoint/motivo/próxima ação.
  - Tentativa respeita próxima execução e espera maior pedida pela fonte.
  - Reiniciar processo/cursor não restaura orçamento da mesma entrada.
  - Tentativas esgotadas não são recriadas indefinidamente pelo reconciliador.

#### `WRK-BUDGET-02` — Progresso independente
- given: caso SHARED com interesses independentes, candidato sem resolução e coleta pronta para avançar.
- when: processar rodadas até o limite de espera fixado no manifesto.
- then:
  - Interesse independente avança dentro do limite, segundo rodízio/envelhecimento documentados.
  - Recentes identificáveis recebem a prioridade definida sem excluir outros indefinidamente.
  - Coleta confirma progresso durante demora/falha exclusiva da pesquisa.
  - Espera externa não mantém trava global de publicação ocupada.

### Retomada e atualidade

#### `WRK-RESUME-01` — Entrada repetida após queda
- given: caso SHARED com checkpoint confirmado e entrada/políticas/contexto ainda compatíveis.
- when: retomar a investigação persistida.
- then:
  - Reaproveita trabalho válido sem duplicar candidatos, observações ou eventos.
  - Consultas respeitam próxima tentativa e orçamento acumulado.
  - Pesquisa compartilhada conserva vínculos alvo separados.
  - Mudança de posse não gera nova descoberta.

#### `WRK-RESUME-02` — Revisão ou posse ultrapassadas
- given: caso RACE com resposta antiga e alteração de variante/correção ou perda de lease.
- when: entregar a resposta antiga para publicação.
- then:
  - Não substitui identidade/avaliação vigente.
  - Amostra incompatível não alimenta o cálculo atual.
  - Progresso histórico confirmado permanece identificado como anterior.
  - Trabalho vigente continua independentemente da resposta rejeitada.

#### `WRK-VALIDITY-01` — Atualização falha e vencimento
- given: caso RETENTION com avaliação aplicável e falha de atualização, relógio antes do vencimento.
- when: avançar o relógio controlado para além da validade.
- then:
  - Antes de vencer, avaliação e falha de atualização permanecem identificadas separadamente.
  - Após vencer, venda estimada e lucro vigentes tornam-se indisponíveis.
  - Histórico e percurso confirmados permanecem consultáveis.
  - Falha não estende artificialmente validade.

### Geografia e identidade manual

#### `WRK-GEOGRAPHY-01` — Região preservada
- given: caso GEOGRAPHY com contexto vigente, resposta divergente/não comprovada e amostra insuficiente local.
- when: processar a investigação.
- then:
  - Não amplia automaticamente a região.
  - Conserva parâmetros solicitados e contexto observado.
  - Contexto não comprovado/divergente mantém parcialidade e não sustenta amostra local validada.
  - Limitação e próxima ação são consultáveis.

#### `WRK-MANUAL-01` — Correção persiste sem contradição
- given: caso MANUAL com correção salva e nova coleta sem atributo divergente.
- when: publicar a observação nova e retomar o worker.
- then:
  - Correção persiste para a mesma identidade após reinício.
  - Ausência de atributo não produz conflito fictício.
  - Reavaliação usa política F06 com origem manual visível.
  - Outros anúncios e condição manual permanecem independentes.

#### `WRK-MANUAL-02` — Contradição bloqueia até revisão
- given: caso MANUAL com correção vigente, avaliação disponível e novas intenções possíveis no canal fake.
- when: publicar coleta com atributo explicitamente contraditório.
- then:
  - Preserva correção/histórico e mostra conflito com a nova evidência.
  - Venda/lucro aplicáveis ficam indisponíveis até revisão explícita.
  - Nenhuma nova autorização de envio usa identidade conflitante ou resposta antiga.
  - Recibos e transmissões incertas seguem preservados para reconciliação.

### Preservação de efeitos

#### `WRK-PRESERVATION-01` — Pesquisa não cria elegibilidade fictícia
- given: caso NON_INTERFERENCE com configuração/interesses/decisões/recibos existentes e resultado somente de referência.
- when: publicar o lote de pesquisa.
- then:
  - Configuração/interesses e decisões existentes permanecem iguais.
  - Recibos e corpos de transmissões incertas permanecem intactos.
  - Finalidade de pesquisa não cria match/descoberta fictícios nem autoriza envio por si só.
  - Candidato com match real segue as regras vigentes de coleta/elegibilidade.

## E2E

**Verification mode:** Sistema isolado completo com navegador, PostgreSQL, worker e canal fake; correlacionar identidade, pesquisa, avaliação e efeitos. Prova real e integração F16 são identificadas separadamente.

### Oferta avaliável

#### `E2E-VALUATION-01` — Da insuficiência à composição
- given: caso SUFFICIENT, interesse salvo com campos atuais, F15/F19 indisponíveis e canal fake.
- when: executar a investigação do alvo inicialmente sem amostra.
- then:
  - Pesquisa produz avaliação F06 e composição F07 da mesma identidade/revisão aplicáveis.
  - Lista e detalhes apresentam motivos coerentes após atualização explícita.
  - Comparáveis usados explicam o cálculo apresentado.
  - Cadastro não exige atributos novos ou serviço de IA.
  - Identidade/eventos permanecem estáveis sem forçar primeiro envio fora da política vigente.

#### `E2E-VALUATION-02` — Prova real distinta da fixture
- given: manifesto do corpus real e perfil dedicado autorizado com acesso Facebook funcional.
- when: executar pesquisa limitada de um alvo desse recorte.
- then:
  - Evidência sanitizada registra fonte/horários/contexto/percurso/resultados/interrupções.
  - Distingue candidatos obtidos de retidos e cobertura observada de lacunas.
  - Insuficiência real não é substituída por cinco candidatos fictícios.
  - Acesso ausente mantém esta prova pendente, sem atribuir sucesso à fixture.

### Consulta e correção

#### `E2E-READING-01` — Navegação e atualização preservadas
- given: oferta com pesquisa publicada, filtros/paginação/revisão fixada, nova pesquisa em andamento e decisão manual salva.
- when: percorrer lista, detalhes e retorno em desktop e largura de 390 px.
- then:
  - Conserva contexto até atualização explícita, identificando avaliação anterior quando necessário.
  - Abas e decisão manual de condição conservam significado.
  - Pesquisa/coleta continuam sem depender de página aberta.
  - Novos motivos, correção e evidências são legíveis sem overflow horizontal.

### Primeira elegibilidade integrada

#### `E2E-IDENTITY-ALERT-01` — Correção de identidade com F16
- given: F16 integrada, caso MANUAL com variantes de publicação confiável recente/antiga/ausente, conflito, recibo confirmado, transmissão incerta e correção apenas de condição; canal fake.
- when: salvar a correção ou resolução de identidade elegível e processar a reavaliação.
- then:
  - Identidade completada sem conflito pode produzir um primeiro envio nas 48 horas da publicação confiável, satisfeitos os demais critérios.
  - Data ausente ou fora da janela e conflito não autorizam primeiro envio.
  - Recibo confirmado ou transmissão incerta não autoriza novo primeiro envio.
  - Reinício preserva identidade de envio e recibos, sem duplicação.
  - Correção somente de condição mantém a exceção F05/F16 e não envia por essa ação isolada.
- notes: integração condicional; ausência de F16 mantém este item pendente nessa integração e não altera as dependências da base textual.

### Adendo de produto — raio fixo de 20 km (2026-11-12)

- **SVC-GEOGRAPHY-20-01:** coleta e pesquisa solicitam São Paulo/SP como localização nativa e raio de20km, independentemente do raio salvo na fonte; parâmetros solicitados não são tratados como prova de aplicação.
- **WRK-GEOGRAPHY-20-01:** pesquisa anterior com contexto de raio diferente é superada antes de retomar ou publicar. Resultado sem confirmação da região permanece parcial e não produz amostra local validada; histórico é preservado.

Esses itens complementam `WRK-GEOGRAPHY-01` e não convertem uma verificação controlada em prova real.
- **WRK-GEOGRAPHY-20-02:** resposta sem confirmação do contexto geográfico efetivo resulta em diagnóstico parcial, sem registrar candidatos ou novos anúncios/eventos daquela página; a condição não dispara repetição automática ilimitada.

### Esclarecimento de contexto aprovado — 2026-11-13

A instrução do usuário substitui o centro de busca postal pela cidade São Paulo/SP, conservando o raio20km e todos os IDs/aceites. O CEP continua nas demais regras do cadastro/cobertura/entrega; nenhum campo CEP é exigido na interface do Facebook. SVC-GEOGRAPHY-20-01 inclui verificar que CEPs distintos não mudam a origem nativa da pesquisa. WRK-GEOGRAPHY-20-01 inclui superar assinaturas anteriores do centro postal.

Uma página nativa recebida com seus próprios resultados e metadados compatíveis pode comprovar o contexto do mesmo documento. Dados observados de outra navegação não comprovam filtros de um POST modificado. WRK-GEOGRAPHY-20-02 continua bloqueando resultados divergentes/não comprovados. Usar cidade na requisição ou exibir um rótulo isolado não substitui a prova integrada.
