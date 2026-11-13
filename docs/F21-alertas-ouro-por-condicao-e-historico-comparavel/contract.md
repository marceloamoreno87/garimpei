# Contrato — F21 Alertas ouro por condição e histórico comparável

*Gerado por spec-writer a partir do PRD. Regeneração substitui o documento; resultados e relatórios ficam em arquivos próprios.*

## Prerequisites

Condições futuras para exercer o contrato. Sua preparação integra a implementação. Ausência de dependência, dado ou evidência impede executar o item afetado; não equivale a aprovação e não autoriza flexibilizar a qualificação. Este contrato não declara nada implementado nesta geração.

### Runtime services

Web, worker e PostgreSQL próprios preparados pelo harness F02, Python 3.13 e dependências do lock. F06/F07/F15/F16/F18/F20 implementadas e avaliadas, com análise de fotos F15/F14 e inferência local F19. Verificar progresso, migrations, prontidão e um caso controlado antes dos itens. A ausência de F15/F18 impede o percurso real de F21; fixtures não comprovam entrega dessas dependências.

### Persistent state

- **BASE:** oferta no interesse ativo, análise textual/visual suficiente, identidade PS5 Slim disco 1TB, cinco comparáveis válidos a 2800/2900/3000/3100/3200, compra 1900, taxa 10%, mediana 3000, lucro 800, publicação confiável há uma hora e destino fake ativado. Usado por API-OURO-01, UI-EVIDENCIAS-01, WRK-QUALIFICA-01, WRK-QUALIFICA-02, WRK-HISTORICO-01 e WRK-MENSAGEM-01.
- **ALIASES/HISTORY/PROFIT/CONDITION:** variantes declaradas em spec §7, com anúncios/observações/atributos, fotos/análises, histórico e composições positivos e negativos. Usados por WRK-IDENTIDADE-01/02, WRK-HISTORICO-01/02, WRK-LUCRO-01, WRK-CONDICAO-01, UI-OFERTAS-01 e E2E-PERCURSO-01.
- **QUEUED/AGE_MANUAL/LEGACY/RACE_FAILURE:** intenções em fila, prazos, escolhas manuais, alterações antes de autorização, corpos/recibos históricos, transmissão incerta e falhas/concorrência dos handles da spec. Usados por WRK-FILA-01/02, WRK-VERSAO-01, WRK-JANELA-01, WRK-MANUAL-01, WRK-CONCORRENCIA-01, WRK-LEGADO-01/02, WRK-INCERTO-01, WRK-FALHA-01, UI-FALHA-01 e API-OURO-02.

Criar por migrations e factories do lab F21 definido em spec §7, em instância eval exclusiva. `prepare --case <handle>` materializa estado; `status --manifest <arquivo>` confere IDs/revisões, valores, escopo e contador fake antes de avaliar o item. Mudanças de entrada usam ações declaradas do mesmo lab. O procedimento é entrega futura, sem dependência de seed ou credencial implícita.

### Static inputs

- `apps/backend/tests/fixtures/alert/gold_cases.json`: casos, relógio UTC, entradas, revisões, evidências de análise/identidade, comparáveis e ações de spec §7. Produzir e validar por schema e pelas factories `gold_alerts.py`; usado por todos os itens controlados.
- Fotos sintéticas identificadas e manifestos de avaliação F15, com hashes, cobertura e rótulos de referência assistida por IA, identificados e congelados antes das saídas do modelo local; usados por WRK-CONDICAO-01, UI-EVIDENCIAS-01 e E2E-PERCURSO-01. Materializar conforme F15 e verificar integridade, sem apresentar resultado fake como análise real.
- `docs/F21-alertas-ouro-por-condicao-e-historico-comparavel/evidence/real-corpus.json`: manifesto sanitizado com anúncios/fotos autorizados, origem, datas/contexto e referência de revisão assistida por IA, com autoria/método/hashes e ausência de validação humana independente explícitos. Produzir a partir de pesquisas reais e conferir cada evidência; usado por E2E-REAL-01. É entrega futura, sem dados reais pressupostos nesta especificação.

### Configuration

`GARIMPEI_ENV_FILE` privado e ambiente `eval` com recursos próprios, relógio controlado nos casos sintéticos, taxa/destino fake e política F21 ativa no estado persistente. Verificar a barreira e versão dos consumidores no status do lab. LEGACY começa na política anterior somente para testar a transição. Segredos, perfis e cookies ficam fora de corpus, mensagens e relatórios.

### External dependencies

Fakes nomeados de fonte/pesquisa, fotos/análise, relógio e WAHA conforme spec §7; o WAHA fake registra POSTs, corpos, destino e recibos, inclusive resposta incerta. Criar por factories do lab e verificar prontidão e contador inicial conhecido. E2E-REAL-01 usa inferência local real F19/F15 e pesquisas autorizadas, com postagem ainda em canal fake. Nenhum item requer envio ao grupo real do usuário; acesso externo ausente mantém prova real pendente.

## Quality gates

Cada gate deve passar antes de considerar a implementação pronta. Estes comandos são requisitos de avaliação futura; não foram executados nesta geração documental.

- **Seis grupos Python** — `node scripts/run-gates.mjs` na raiz — tipos, lint/templates, limites, arquitetura, ciclos e não utilizados pelo runner atual.
- **Regras e integrações** — `uv run --directory apps/backend --frozen --no-sync pytest tests/unit tests/http tests/integration tests/quality` — regras, páginas, PostgreSQL, autorização, migração e falhas com recursos próprios.
- **Regressão completa** — `uv run --directory apps/backend --frozen --no-sync pytest` — integração completa sem omitir pré-requisitos de lifecycle.
- **Navegador** — `playwright-cli`, conforme skill do projeto — jornadas UI/E2E desktop e 390 px com snapshots/screenshots.
- **Acabamento das superfícies alteradas** — avaliação `frontend-ui-design`, conforme skill do projeto — evidência visual no design existente.
- **Prova real** — procedimento de spec §7 e E2E-REAL-01 — distinguir corpus real, rótulos humanos, resultado local e envio fake; ausência continua pendente.

## Coverage Manifest

Cada linha reproduz literalmente o aceite F21 do PRD; todos os itens descrevem verificações futuras.

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F21-AC01**: nova autorização de alerta exige conjuntamente análise aplicável de título/descrição/fotos com condição suficiente, identidade normalizada sem conflito, amostra histórica equivalente válida e lucro estimado estritamente positivo após a taxa; falta de qualquer requisito impede envio. | WRK-QUALIFICA-01, WRK-CONDICAO-01, WRK-IDENTIDADE-02, WRK-HISTORICO-02, WRK-LUCRO-01 |
| **F21-AC02**: nomes equivalentes validados produzem a mesma identidade de produto e permitem comparação, preservando atributos determinantes. Modelo/variante incompatível, peça, acessório, lote, atributo obrigatório ausente ou conflito não são equivalentes; anúncios diferentes preservam fonte/ID e histórico próprios. | WRK-IDENTIDADE-01, WRK-IDENTIDADE-02 |
| **F21-AC03**: estimativa histórica é reproduzível pelos comparáveis persistidos e segue F06: última observação por fonte/ID, exclusão do alvo/repetições/incompatíveis, mínimo de cinco retidos, observação até 14 dias, corte de discrepantes, dispersão e mediana. Referência de novo e preço da própria oferta não completam a amostra; ausência/insuficiência/vencimento não vira preço ou lucro fictício. | WRK-HISTORICO-01, WRK-HISTORICO-02, E2E-REAL-01 |
| **F21-AC04**: lucro em centavos maior que zero após taxa pode satisfazer o requisito financeiro; lucro zero, negativo ou indisponível bloqueia alerta sem ocultar a oferta. Não há margem percentual ou valor mínimo adicional, custo logístico ou garantia de venda/lucro. | WRK-LUCRO-01, UI-OFERTAS-01 |
| **F21-AC05**: ausência de fotos, análise pendente/falha/inconclusiva, defeito relevante, conflito ou análise antiga não autorizam alerta, mesmo com frase positiva ou escolha manual boa. Desgaste cosmético leve é aceito com ressalva somente quando a evidência de funcionamento e a análise são suficientes. | WRK-CONDICAO-01, WRK-MANUAL-01, E2E-REAL-01 |
| **F21-AC06**: dados relevantes são conferidos novamente antes de nova transmissão para primeiro alerta e redução, inclusive após espera na fila. Revisão de identidade/condição/amostra/configuração incompatível ou vencida suspende a autorização e provoca reavaliação; comparação com histórico de outra variante nunca sustenta envio. | WRK-FILA-01, WRK-FILA-02, WRK-VERSAO-01, WRK-QUALIFICA-02 |
| **F21-AC07**: detalhes e mensagem nova explicam produto normalizado, compra, venda estimada, lucro e base histórica com datas/quantidade/método, ressalvas e acesso às evidências. Diagnóstico distingue falta de análise, identidade, amostra e lucro não positivo, conserva revisão/data e separa situação atual de recibos históricos; falha de atualização preserva leitura e filtros. | API-OURO-01, API-OURO-02, UI-EVIDENCIAS-01, UI-OFERTAS-01, UI-FALHA-01, WRK-MENSAGEM-01, WRK-LEGADO-02 |
| **F21-AC08**: chegada de evidências suficientes pode completar a primeira elegibilidade dentro de 48 horas da publicação confiável; repetição, concorrência e troca de política não duplicam primeiro alerta ou redução. Classificação manual isolada não gera intenção adiada; reduções continuam exigindo primeiro envio confirmado e não ganham nova janela de publicação nesta revisão. | E2E-PERCURSO-01, WRK-JANELA-01, WRK-MANUAL-01, WRK-CONCORRENCIA-01, WRK-QUALIFICA-02 |
| **F21-AC09**: adoção e reinício preservam corpos/recibos e reconciliação anteriores; intenção comprovadamente não transmitida só segue após qualificação F21. Transmissão incerta não repete POST, e ausência/falha de dependência suspende novas autorizações sem recorrer à política anterior. Provar percurso completo e casos adversos em recursos isolados, distinguindo teste controlado de análise real. A comparação do corpus real usa referência assistida por IA, identificada e congelada antes das saídas do modelo local; declarar a ausência de validação humana independente, sem apresentar concordância entre IAs como precisão contra verdade humana. | WRK-LEGADO-01, WRK-LEGADO-02, WRK-INCERTO-01, WRK-FALHA-01, E2E-PERCURSO-01, E2E-REAL-01 |

## HTTP API

**Verification mode:** Requisitar os GET HTML existentes e observar status e conteúdo/links da resposta. Efeitos assíncronos e ausência de transmissão são verificados nas superfícies Worker/E2E.

### Consulta HTML

#### `API-OURO-01` — Diagnóstico completo da oferta
- given: BASE qualificada com histórico e evidências conhecidos.
- when: GET /ofertas/<id>/ com aba/filtros/página/versão válidos.
- then:
  - Resposta 200 apresenta nome normalizado e atributos aplicáveis.
  - O conteúdo informa compra, venda estimada, lucro e taxa da composição correspondente.
  - O histórico informa método, quantidade retida e datas, com links das evidências e ressalvas.
  - A política/momento e a revisão da qualificação ficam identificáveis.

#### `API-OURO-02` — Falha de projeção e oferta inexistente
- given: RACE_FAILURE com falha exclusiva de leitura da qualificação; uma identidade inexistente como variação independente.
- when: GET /ofertas/<id>/ para cada variação.
- then:
  - Falha exclusiva da qualificação mantém dados da oferta e mensagem recuperável, sem afirmar ouro.
  - Identidade inexistente recebe o tratamento 404 existente.
  - Nenhuma resposta declara confirmação de envio sem recibo.

## UI

**Verification mode:** Navegar nas páginas pelo usuário, observar texto, evidências, estado da leitura e navegação; incluir desktop e 390 px.

### Evidências e leitura estável

#### `UI-EVIDENCIAS-01` — Explicação da qualificação
- given: BASE com evidências e produto normalizado conhecidos.
- when: Abrir os detalhes da oferta.
- then:
  - Nome normalizado, atributos e título original podem ser conferidos.
  - Sinais textuais/fotos e ressalvas da análise estão associados à oferta.
  - Comparáveis usados exibem preço, origem e datas, com a mediana identificada como referência de preços pedidos.
  - Qualificação atual e estado histórico do envio aparecem separados.
  - Valores centrais são legíveis sem rolagem horizontal na largura de 390 px.

#### `UI-OFERTAS-01` — Oferta sem lucro permanece consultável
- given: PROFIT com ofertas de lucro 0.01/0.00/-100.00 e composição indisponível.
- when: Abrir a lista e consultar cada oferta.
- then:
  - Ofertas zero/negativas continuam disponíveis na aba aplicável.
  - O bloqueio de lucro não positivo é distinguido de lucro indisponível.
  - Não há indicação de ouro para oferta que falha no requisito financeiro.
  - Compra conhecida permanece visível quando venda/lucro são indisponíveis.

#### `UI-FALHA-01` — Atualização recuperável na mesma jornada
- given: RACE_FAILURE com lista/detalhe carregados, filtros/página/versão conhecidos e próxima atualização falhando.
- when: Solicitar a atualização.
- then:
  - Leitura anterior permanece identificada por versão/data.
  - Falha e ação de tentar novamente aparecem sem confirmação fictícia de atualização.
  - Rota, filtros, página e contexto permanecem preservados.
  - Dados de análise antiga não são promovidos a qualificação atual.

## Worker

**Verification mode:** Acionar o trabalho existente sobre o estado do caso e observar qualificação persistida, revisões, intenções e registros do canal fake após o processamento. Contraprovas são execuções independentes da mesma ação.

### Qualificação e despacho

#### `WRK-QUALIFICA-01` — Conjunção suficiente no primeiro alerta
- given: BASE sob política F21 ativa e sem primeiro envio anterior.
- when: Processar o ciclo de elegibilidade e despacho.
- then:
  - Decisão qualificada referencia análise, identidade, histórico e composição aplicáveis.
  - Uma única intenção lógica de primeiro alerta recebe autorização.
  - Canal fake registra exatamente um POST ao destino vinculado.
  - Recibo persistido aponta para a mesma intenção e corpo.

#### `WRK-QUALIFICA-02` — Mesma exigência nas reduções
- given: BASE com primeiro envio confirmado e um evento real de redução posterior; variações com condição/amostra inválidas ou lucro não positivo.
- when: Processar o evento de redução de cada variação.
- then:
  - Redução válida usa qualificação da sua observação/evento e mantém identidade própria.
  - Reduções que falham na qualificação não produzem POST.
  - Falta de primeiro confirmado impede envio de redução.
  - Publicação do anúncio há mais de 48 horas não exclui isoladamente redução com os demais requisitos válidos.

### Equivalência de produto

#### `WRK-IDENTIDADE-01` — Aliases agrupam produto sem fundir anúncios
- given: ALIASES com títulos equivalentes validados e observações distintas, incluindo o mesmo anúncio reaparecendo em outra consulta.
- when: Processar identificação, estimativa e qualificação.
- then:
  - Títulos equivalentes com atributos comprovados produzem a mesma chave de produto.
  - Anúncios distintos conservam suas próprias identidades e observações.
  - Repetição de fonte/ID não aumenta a quantidade da amostra nem cria outra descoberta.
  - Evidências da equivalência e dos atributos ficam rastreáveis.

#### `WRK-IDENTIDADE-02` — Nomes semelhantes incompatíveis
- given: ALIASES nas variantes de modelo/edição/capacidade divergentes, peça/acessório/lote, atributo obrigatório ausente e conflito.
- when: Processar a qualificação de cada variante.
- then:
  - Produtos incompatíveis não entram no grupo equivalente.
  - Ausência de atributo e conflito possuem motivos específicos sustentados por evidência.
  - Não há POST sustentado por comparação incompatível.
  - A identidade não é completada pelo nome do interesse ou pelo preço baixo.

### Histórico e estimativa

#### `WRK-HISTORICO-01` — Mediana reproduzível sobre histórico persistido
- given: HISTORY com BASE, registros antigos/repetidos e valores excluíveis conhecidos.
- when: Processar a avaliação e qualificação.
- then:
  - A amostra usa somente a última observação aplicável por fonte/ID e exclui o alvo.
  - Os retidos satisfazem mínimo, equivalência, idade, corte de discrepantes e dispersão F06.
  - Mediana, preços e datas reproduzem o preço de venda usado pela composição.
  - Preços da própria oferta e referências de novo não completam a amostra.
  - Origens e motivos de exclusão ficam consultáveis.

#### `WRK-HISTORICO-02` — Falta de histórico válido bloqueia
- given: HISTORY nas variações de ausência, quatro retidos, dispersão, duplicatas/alvo suficientes apenas na contagem bruta e fronteiras temporais.
- when: Processar a qualificação de cada variação.
- then:
  - Quantidade insuficiente/dispersão/vencimento mantêm ausência de qualificação com motivos distintos.
  - Observação com exatamente 14 dias pode ser retida se satisfizer os demais filtros.
  - Observação acima de 14 dias ou futura não completa a amostra.
  - Nenhum preço/lucro fictício é produzido para liberar alerta.
  - O canal fake não registra POST das variações inelegíveis.

### Lucro estimado

#### `WRK-LUCRO-01` — Lucro após taxa em centavos
- given: PROFIT com condições não financeiras válidas.
- when: Processar elegibilidade e despacho de cada variação.
- then:
  - Lucro 0.01 após taxa pode satisfazer o requisito financeiro.
  - Lucro 0.00 e -100.00 bloqueiam nova autorização.
  - Composição ausente/incompatível não recebe valor zero nem lucro fabricado.
  - Não é aplicado outro valor mínimo ou margem percentual.
  - Cálculo preserva taxa configurada e política sem custo logístico.

### Condição suficiente

#### `WRK-CONDICAO-01` — Texto e fotos suficientes são obrigatórios
- given: CONDITION com demais requisitos válidos.
- when: Processar a qualificação de cada variação.
- then:
  - Foto ausente, análise pendente/falha/inconclusiva e revisão antiga impedem autorização.
  - Frase positiva ou escolha manual boa não supera ausência de evidência, defeito ou conflito relevante.
  - Desgaste leve com evidência textual/visual suficiente pode qualificar com ressalva.
  - A análise aponta para as fotos e a observação efetivamente examinadas.
  - O canal fake não recebe POST de condição insuficiente.

### Revalidação e versões

#### `WRK-FILA-01` — Mudança durante espera invalida primeiro e redução
- given: QUEUED para ambos os tipos, com entrada alterada antes de liberar o canal.
- when: Retomar o despacho.
- then:
  - Condição, identidade, amostra e composição são conferidas na autorização final.
  - Mudança incompatível ou vencimento bloqueia o POST com motivo.
  - A revisão antiga não é apresentada como qualificação atual.
  - Reavaliação não mistura financeiro antigo com evidências de outra variante.

#### `WRK-FILA-02` — Conferência após consulta lenta do canal
- given: QUEUED com barreira controlada na consulta do canal e alteração confirmada de evidência antes da autorização.
- when: Concluir o processamento pausado.
- then:
  - A autorização observa a evidência alterada.
  - Qualificação obsoleta não autoriza transmissão.
  - A intenção conserva identidade e motivo de reavaliação sem criar outra descoberta.

#### `WRK-VERSAO-01` — Resultado atrasado não substitui revisão atual
- given: RACE_FAILURE com trabalho antigo e nova revisão de identidade/foto/amostra já publicada.
- when: Publicar o resultado atrasado.
- then:
  - Decisão antiga não vira a qualificação vigente.
  - A versão aplicável e suas evidências permanecem preservadas.
  - Não há autorização com histórico de outra variante.

### Conteúdo da mensagem

#### `WRK-MENSAGEM-01` — Justificativa no corpo recém-gerado
- given: BASE qualificada, com intenção ainda sem corpo congelado.
- when: Autorizar e despachar a mensagem.
- then:
  - Corpo contém nome do produto e os rótulos Preço de compra, Preço de venda estimado e Lucro estimado.
  - Resumo histórico identifica quantidade, método e data-base dos preços pedidos.
  - Ressalvas e links da oferta/evidências são preservados quando disponíveis.
  - Valores congelados correspondem à decisão de qualificação autorizada.
  - A mensagem não promete funcionamento comprovado, venda realizada ou lucro garantido.

### Prazo e gatilhos

#### `WRK-JANELA-01` — Prazo de primeiro envio preservado
- given: AGE_MANUAL nas variações exatamente 48 horas, acima de 48 horas, data futura e data sem confiança, com requisitos F21 satisfeitos.
- when: Processar o primeiro despacho de cada variação.
- then:
  - Exatamente 48 horas pode autorizar primeiro envio.
  - Idade superior, data futura ou sem confiança impedem primeiro POST.
  - Primeira coleta não substitui data da publicação.
  - Vencimento durante espera é considerado na autorização final.

#### `WRK-MANUAL-01` — Escolha manual não fabrica elegibilidade
- given: AGE_MANUAL com qualificação insuficiente e ação isolada de classificação manual boa; variante com identidade corrigida e condição suficiente independente.
- when: Processar a reavaliação após a alteração declarada de cada variante.
- then:
  - Classificação manual de condição isolada não cria intenção imediata nem adiada.
  - A escolha manual não supre análise visual ausente ou insuficiente.
  - Correção válida de identidade pode completar o conjunto somente com demais requisitos/prazo válidos.
  - A condição manual persistida não é apagada pela qualificação.

### Idempotência

#### `WRK-CONCORRENCIA-01` — Um envio lógico sob repetição e concorrência
- given: RACE_FAILURE com a mesma oferta elegível e duas execuções controladas; variante de redução com mesmo evento.
- when: Processar simultaneamente as execuções e retomar o trabalho.
- then:
  - Há no máximo um POST novo por primeiro alerta ou evento de redução.
  - Recebimento confirmado permanece ligado à intenção original.
  - Troca de política, entrada repetida e reinício não criam outro primeiro envio.

### Adoção e legado

#### `WRK-LEGADO-01` — Barreira de adoção com histórico
- given: LEGACY sob política anterior, com inventário de corpos, recibos e autorizações em voo.
- when: Ativar a política F21 pelo procedimento de adoção.
- then:
  - A barreira persistente identifica a nova política após drenagem/identificação das autorizações anteriores.
  - Contagens, vínculos, corpos e recibos históricos permanecem preservados.
  - Pendências não transmitidas passam a exigir qualificação antes do próximo despacho.
  - Registros antigos sem evidência não são marcados retroativamente como ouro.
  - Consumidor incompatível com a barreira não pode autorizar novo envio.

#### `WRK-LEGADO-02` — Corpo congelado e qualificação atual
- given: LEGACY com intenção comprovadamente não transmitida e corpo/financeiro congelados; variantes com composição ainda aplicável e com composição divergente.
- when: Processar o despacho sob F21.
- then:
  - A composição ainda aplicável só segue se satisfizer toda a qualificação F21.
  - Composição divergente fica suspensa sem reconstruir corpo com valores novos.
  - Textos financeiros e referências históricos conservam seus valores.
  - Diagnóstico distingue qualificação atual de situação histórica da intenção.

#### `WRK-INCERTO-01` — Incerteza mantém reconciliação
- given: LEGACY com uma transmissão possivelmente realizada e um primeiro alerta já confirmado.
- when: Reiniciar e retomar o processamento após adoção.
- then:
  - O POST incerto não é repetido automaticamente.
  - Corpo, destino e estado de reconciliação permanecem preservados.
  - O recibo confirmado impede outro primeiro envio.
  - Política nova não converte incerteza em nunca enviado.

### Indisponibilidade

#### `WRK-FALHA-01` — Dependência indisponível não libera política anterior
- given: RACE_FAILURE após barreira F21 ativa, com falha/ausência de F15, F18 ou leitura de histórico/composição como variações independentes.
- when: Processar elegibilidade e despacho.
- then:
  - Novas autorizações afetadas permanecem suspensas com motivo recuperável.
  - Texto positivo e estimativa antiga não liberam o caminho anterior.
  - Política persistente permanece ativa após falha/reinício.
  - Dados anteriores são preservados sem afirmação de atualidade falsa.
  - Trabalho independente saudável mantém progresso dentro dos limites existentes.

## E2E

**Verification mode:** Executar o sistema com dependências integradas, observar a jornada, evidências persistidas e registros do canal fake. Prova real de análise/pesquisa permanece identificada separadamente de fixtures.

### Percurso integrado

#### `E2E-PERCURSO-01` — Da investigação ao alerta sustentado
- given: HISTORY/CONDITION com alvo inicialmente sem fotos/análise e sem amostra, dentro da janela confiável, e resultado esperado conhecido.
- when: Concluir o fluxo de obtenção de evidências e processamento pelo sistema.
- then:
  - Antes de completar o conjunto, a oferta não recebe POST.
  - F15 e F18 fornecem evidências aplicáveis e o histórico produz mediana/composição rastreáveis.
  - A primeira elegibilidade completa autoriza exatamente um POST ao destino fake.
  - Detalhes e mensagem refletem a mesma qualificação/composição no momento da autorização.
  - Retomada preserva recibo e não repete envio.

#### `E2E-REAL-01` — Corpus real com histórico rastreável e análise local
- given: Manifesto real autorizado, fotos verificadas e rótulos de referência assistida por IA identificados e congelados antes das saídas do modelo local; F15/F18 efetivas e F19 local real; destino fake.
- when: Executar a avaliação integrada do corpus real documentado.
- then:
  - Condição tem sinais/fotos rastreáveis e diferenças frente à referência assistida por IA registradas, sem alegar revisão humana independente ou precisão contra verdade humana.
  - Nome normalizado e comparáveis reais equivalentes sustentam preço representativo reproduzível, ou a insuficiência fica explícita.
  - Relatório separa análise real, saída do modelo, composição e postagem fake.
  - Um caso real com conjunto suficiente demonstra qualificação positiva; sem esse caso, essa dimensão permanece pendente sem substituir pela fixture.
  - Casos insuficientes/contraditórios não ganham qualificação por afrouxamento de política.


## Alteração aprovada — referência F21

Em 2026-11-13 o usuário autorizou explicitamente a referência assistida por IA para esta feature, após receber a galeria real de oito anúncios/42 fotos. A referência tem autoria/método e hashes, é congelada antes da inferência local e não constitui validação humana independente. A alteração afeta somente a origem da referência; todos os requisitos de evidência, qualificação positiva real e demais itens permanecem obrigatórios.
