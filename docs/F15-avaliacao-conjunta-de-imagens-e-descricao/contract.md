# Contract: F15 — Avaliação conjunta de imagens e descrição

*Gerado por spec-writer. Regeneração substitui o documento; relatórios ficam em arquivos próprios.*

## Prerequisites

Estas condições descrevem o ambiente de exercício do contrato. Sua preparação integra a entrega. Condição ausente impede executar os itens afetados e permanece pendente; fakes não substituem a prova real exigida.

### Runtime services

- Web, worker e PostgreSQL próprios, com migrations e F15 ativa; preparação e parada por `scripts/init.sh`/`scripts/stop.sh` no ambiente descartável. Inferência é executada em capacidade separada de F19, sem bloquear o coletor. Verificar por prontidão, leitura dos detalhes e conclusão de trabalho controlado.
- F14 fornece manifesto e cópias locais versionadas. F19 fornece Qwen3.5 4B Q4_K_M/Ollama local com GPU real, imagem/modelo fixados e perfil limitado documentado. Verificar diagnóstico do runtime e uma inferência de texto/foto antes de E2E-QUALIDADE-01; indisponibilidade pode ser simulada somente nos itens de falha.
- Navegador disponível para itens UI/E2E, com sessão `playwright-cli` exclusiva do ambiente de avaliação.

### Persistent state

- **ofertas-corpus:** anúncios, observações e identidades/categorias correspondentes ao manifesto de avaliação; algumas ofertas com evidência suficiente e outras com fotos ausentes, inúteis, parciais ou conflitantes. Criação por migrations/factories do lab descrito na spec; `status` verifica IDs, revisões e hashes. Used by: SVC-AVALIACAO-01 a 05, SVC-TEXTO-01 a 03, API-CONSULTA-01, UI-AVALIACAO-01 a 03, WRK-IMAGENS-01 a 02, E2E-QUALIDADE-01.
- **oferta-manual:** anúncio incerto do corpus, com escolha manual confirmada e revisão conhecida; inclui resultado automático divergente e página anterior da escolha. Criação pela factory e pelo formulário existentes; leitura confirma revisão e escolha. Used by: SVC-MANUAL-01, API-MANUAL-01, UI-MANUAL-01, E2E-ALERTA-03.
- **oferta-versionada:** anúncio com análise anterior confirmada, nova entrada desejada, trabalhos atrasados/concorrentes e revisão de lista aberta. O lab produz cada variação e seu status verifica a ordem de revisões. Used by: UI-ATUALIZACAO-01, WRK-VERSAO-01 a 04, WRK-FALHA-01 a 03, E2E-OPERACAO-01.
- **eventos-alerta:** eventos novos e pendentes do fluxo existente, configuração de interesse/taxa/destino fake válida, composições calculáveis e casos com recibo confirmado, transmissão incerta ou exclusão terminal anteriores. Factory de alertas prepara o estado e `status` fornece IDs/estados e contador de transmissões fake. Used by: E2E-ALERTA-01 a 04.

### Static inputs

- `apps/backend/tests/fixtures/listing/assessment_cases.json` — casos com ID, categoria/atributos, texto original, fotos/hashes, proveniência, autorização, rótulo de referência com autoria explícita, sinais esperados, limites e divisão ajuste/avaliação reservada. É entrega futura; revisão de referência precede execução do modelo local. Used by: SVC-AVALIACAO-01 a 05, SVC-TEXTO-01 a 03, UI-AVALIACAO-01, WRK-IMAGENS-01 a 02, E2E-QUALIDADE-01.
- `apps/backend/tests/fixtures/listing/assessment_images/` — imagens sintéticas identificadas e fotos reais autorizadas do manifesto, com integridade verificável. Imagens reais indisponíveis impedem a prova real, sem promover imagens sintéticas a evidência de qualidade. Used by: WRK-IMAGENS-01 a 02, E2E-QUALIDADE-01.

### Configuration

- Configuração central de F19 com revisão exata do modelo, cloud desabilitado, endpoint local, concorrência/contexto/imagens/saída/fila/timeout/tentativas finitos e comprovados. Nenhuma credencial é entrada do modelo. Configuração de teste usa `GARIMPEI_ENV=eval`, instância própria e arquivo privado fora do repositório.
- Política/rubrica e prompt/schema versionados, F15 ativa. Lab produz e verifica configuração sem segredos pelo protocolo definido na spec; valores de teste não são metas do produto.

### External dependencies

- Fakes nomeados de fotos, inferência e WAHA do lab fornecem resultados completos, atraso, timeout, JSON inválido, referência inexistente e contador de transmissão; esses cenários não usam serviços reais do usuário. Used by: WRK-FALHA-01 a 03, WRK-VERSAO-01 a 04, E2E-OPERACAO-01, E2E-ALERTA-01 a 04.
- E2E-QUALIDADE-01 usa F19 real e fotos autorizadas já disponíveis, sem inferência externa no motor F19 avaliado. A origem de IA da referência é identificada separadamente. Downloads de preparação pertencem a F19. Nenhum item exige novo envio ao grupo real ou acesso ao perfil pessoal.

## Quality gates

Cada gate deve passar para considerar a implementação pronta. Comandos são executados a partir da raiz, em ambiente isolado conforme spec; esta geração documental não os declara executados.

- **Seis gates Python** — `node scripts/run-gates.mjs` — tipos, lint/templates, limites de dependências, arquitetura, ciclos e não utilizados.
- **Regras e HTTP** — `uv run --directory apps/backend --frozen --no-sync pytest tests/unit tests/http` — regras novas e regressões existentes.
- **Persistência e integração** — `uv run --directory apps/backend --frozen --no-sync pytest tests/integration` — migrations, concorrência, falhas, alertas e regressões com recursos próprios; separar partições se houver disputa de recursos, sem omitir casos.
- **Navegador** — `playwright-cli` — jornadas UI/E2E documentadas com screenshots e snapshots; avaliação visual conforme skill `frontend-ui-design`.
- **Corpus real** — lab e procedimento de `spec.md`, seção 7 — executar E2E-QUALIDADE-01 com GPU real, rótulos de referência assistida por IA aprovados e relatório de concordâncias/divergências/abstenções/recursos. Prova ausente permanece pendente.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F15-AC01**: o conjunto de avaliação documentado inclui produto aparentemente conservado, dano visível, contradição texto/foto, foto insuficiente e foto ausente; cada resultado mostra sinais rastreáveis e distingue aparência, declaração de funcionamento e incerteza. | SVC-AVALIACAO-01, SVC-AVALIACAO-02, SVC-AVALIACAO-03, SVC-AVALIACAO-04, UI-AVALIACAO-01, E2E-QUALIDADE-01 |
| **F15-AC02**: ausência de dano visível, foto genérica ou falta de resposta do modelo não comprova funcionamento nem promove automaticamente condição boa; conflito relevante segue regra conservadora e revisão definida no contrato. | SVC-AVALIACAO-03, SVC-AVALIACAO-04, SVC-AVALIACAO-05, WRK-FALHA-01, WRK-FALHA-02 |
| **F15-AC03**: decisão manual salva sobrevive a reanálise e reinício; conflito com nova evidência permanece visível, sem sobrescrever a escolha ou enviar alerta pela ação manual. | SVC-MANUAL-01, API-MANUAL-01, UI-MANUAL-01, WRK-FALHA-03, E2E-ALERTA-03 |
| **F15-AC04**: texto/fotos/política novos permitem reanálise versionada e entrada idêntica reutiliza resultado aplicável; falha técnica conserva histórico e não bloqueia coleta. | WRK-VERSAO-01, WRK-VERSAO-02, WRK-VERSAO-03, WRK-VERSAO-04, WRK-FALHA-02, WRK-FALHA-03, E2E-OPERACAO-01 |
| **F15-AC05**: usar Qwen3.5 4B Q4_K_M em inferência local F19; comparar com uma referência de revisão assistida por IA, identificada e congelada antes de consultar as saídas do modelo local, no corpus de texto/fotos. Publicar concordâncias, divergências, abstenções, consumo de GPU e latência; declarar que a validação humana independente não foi executada. Não inventar meta de precisão ou percentual de certeza nem apresentar concordância entre IAs como precisão contra verdade humana. | E2E-QUALIDADE-01, UI-AVALIACAO-01 |
| **F15-AC06**: as três sondagens textuais contraditórias registradas no relatório deixam de ser promovidas automaticamente a boa condição; controles positivo/negativo continuam corretos e a proteção funciona sem depender de resposta da IA. Ressalvas preservam seu trecho e motivo. | SVC-TEXTO-01, SVC-TEXTO-02, SVC-TEXTO-03 |
| **F15-AC07**: desgaste cosmético leve é mostrado como ressalva e não exclui sozinho uma oferta com evidências suficientes; falha funcional ou dano relevante claramente identificado produz condição automática com defeito. Suspeita visual sem conclusão e conflito relevante não resolvido mantêm condição não confirmada, com critérios e exemplos por categoria documentados. | SVC-AVALIACAO-01, SVC-AVALIACAO-02, SVC-AVALIACAO-03, SVC-AVALIACAO-05, UI-AVALIACAO-01, E2E-QUALIDADE-01 |
| **F15-AC08**: com F15 ativa, declaração positiva sem fotos ou enquanto a análise está pendente, falhou ou é inconclusiva não autoriza alerta automático; análise visual aplicável concluída e evidência textual suficiente permitem reavaliar o requisito de condição. Uma escolha manual não fabrica análise concluída nem cria envio por si só; demais requisitos e recibos continuam sendo verificados pelo fluxo de alertas. | SVC-AVALIACAO-04, SVC-MANUAL-01, WRK-IMAGENS-02, E2E-ALERTA-01, E2E-ALERTA-02, E2E-ALERTA-03, E2E-ALERTA-04 |

## Service

**Verification mode:** consultar a fronteira pública de condição usada por exploração/alertas sobre observações persistidas e avaliações preparadas; observar DTO de condição, evidências, motivo, prontidão e versões. Não invocar helpers internos como substituto da integração.

### Avaliar condição

#### `SVC-AVALIACAO-01` — Funcionamento declarado e desgaste leve
- given: ofertas-corpus com declaração explícita de funcionamento do item principal e análise aplicável suficiente com apenas desgaste cosmético leve.
- when: consultar a condição da oferta.
- then:
  - A condição automática é boa.
  - O desgaste consta como ressalva com foto identificada.
  - A declaração do vendedor está separada da aparência observada.
  - Não é afirmado funcionamento comprovado por inspeção.

#### `SVC-AVALIACAO-02` — Defeito claro prevalece
- given: ofertas-corpus com falha funcional explícita ou dano relevante claro em evidência aplicável, inclusive com frase positiva genérica.
- when: consultar a condição da oferta.
- then:
  - A condição automática é com defeito.
  - O sinal negativo conserva trecho/foto e motivo.
  - O requisito de condição para alerta não é satisfeito sem escolha manual prevalecente e avaliação suficiente.

#### `SVC-AVALIACAO-03` — Suspeita e conflito não resolvido
- given: ofertas-corpus com suspeita de dano visual ou divergência relevante entre texto e fotos, sem defeito inequívoco.
- when: consultar a condição da oferta.
- then:
  - A condição automática é não confirmada.
  - O resultado aponta a evidência e o que requer revisão.
  - Não há acusação de fraude ou certeza fabricada.

#### `SVC-AVALIACAO-04` — Evidência insuficiente
- given: ofertas-corpus com declaração positiva, mas sem fotos, fotos inúteis/genéricas, análise pendente, falha ou conclusão insuficiente.
- when: consultar a condição da oferta.
- then:
  - A condição automática é não confirmada.
  - O motivo distingue ausência, pendência, falha e insuficiência.
  - O requisito de condição para envio automático não é satisfeito.

#### `SVC-AVALIACAO-05` — Aparência não prova funcionamento nem identidade
- given: ofertas-corpus com fotos conservadas sem declaração de funcionamento, ou com conflito de identidade/critério de categoria insuficiente.
- when: consultar a condição da oferta.
- then:
  - A condição automática é não confirmada.
  - A avaliação explicita funcionamento desconhecido ou o conflito aplicável.
  - Atributo não comprovado não é apresentado como identificado.

### Proteger ressalvas textuais

#### `SVC-TEXTO-01` — Três regressões sem modelo
- given: ofertas-corpus com os três textos das sondagens históricas e sem resposta da IA; o caso de tomada identifica aparelho portátil com bateria.
- when: consultar a condição de cada caso.
- then:
  - Desligamento intermitente e restrição anormal de energia não recebem condição automática boa.
  - “Não foi testado. Funciona perfeitamente.” permanece não confirmado.
  - Cada ressalva conserva trecho original e motivo sem depender da IA.

#### `SVC-TEXTO-02` — Controles preservados
- given: ofertas-corpus com o controle positivo e fotos suficientes sem conflito, e o controle “O aparelho não liga” sem depender de IA.
- when: consultar a condição dos controles.
- then:
  - O positivo recebe boa condição automática.
  - O negativo recebe condição automática com defeito.

#### `SVC-TEXTO-03` — Escopo da restrição
- given: ofertas-corpus com TV normalmente ligada à tomada, defeito declarado apenas em acessório e casos de contexto desconhecido.
- when: consultar a condição de cada caso.
- then:
  - Uso normal de energia da TV não é rotulado como falha de bateria.
  - Defeito do acessório não comprova defeito do item principal.
  - Ausência de contexto relevante produz abstenção em vez de correspondência forçada.

### Preservar classificação manual

#### `SVC-MANUAL-01` — Escolha prevalece sem fabricar avaliação
- given: oferta-manual com escolha salva, avaliação automática divergente e variantes com avaliação ausente/inconclusiva.
- when: consultar a condição vigente.
- then:
  - A condição efetiva e a aba respeitam a escolha manual salva.
  - A divergência automática conclusiva permanece identificável.
  - Avaliação ausente/inconclusiva não se torna suficiente por causa da escolha.
  - O requisito de envio automático permanece bloqueado sem análise suficiente.

## HTTP API

**Verification mode:** enviar requisições às rotas HTML existentes e observar status, corpo, redirecionamento e efeito imediato de gravação, sem inferência síncrona.

### Consultar avaliação

#### `API-CONSULTA-01` — Falha de IA é estado da oferta
- given: ofertas-corpus legíveis, com modelo indisponível e histórico de avaliação conservado.
- when: acessar `GET /ofertas/<id>/`.
- then:
  - A resposta é 200 com os dados conhecidos do anúncio.
  - A falha local é identificada sem mostrar avaliação anterior como atual.
  - A leitura não inicia nem aguarda inferência.

### Preservar classificação manual

#### `API-MANUAL-01` — Revisão antiga não substitui escolha atual
- given: oferta-manual com revisão posterior à página aberta e token CSRF válido.
- when: enviar a revisão antiga para `POST /ofertas/<id>/condicao/`.
- then:
  - A resposta é 409 com orientação de revisar o estado atual.
  - A escolha manual confirmada permanece intacta.

## UI

**Verification mode:** navegar no ambiente isolado, observar textos/estados/evidências e operar os controles como usuário por teclado e a 390 px; registrar screenshots e snapshots.

### Consultar avaliação

#### `UI-AVALIACAO-01` — Evidências compreensíveis
- given: ofertas-corpus com avaliação completa e referências textuais/visuais válidas.
- when: abrir os detalhes da oferta.
- then:
  - Aparência, funcionamento declarado e limitações são apresentados separadamente.
  - Cada sinal permite identificar seu trecho ou foto de suporte.
  - Modelo e momento da análise ficam acessíveis em informação secundária.
  - Não há percentual de certeza ou garantia de funcionamento.

#### `UI-AVALIACAO-02` — Espera e ausência honestas
- given: ofertas-corpus sem fotos ou com análise pendente/falha/inconclusiva.
- when: abrir os detalhes da oferta.
- then:
  - A mensagem distingue a causa da condição não confirmada.
  - Fotos não examinadas não aparecem como analisadas.
  - Texto, preço conhecido e link da origem continuam consultáveis.

#### `UI-AVALIACAO-03` — Histórico não se apresenta como atual
- given: ofertas-corpus com análise anterior confirmada e entrada vigente alterada ainda sem análise concluída.
- when: abrir os detalhes da oferta vigente.
- then:
  - A avaliação anterior tem identificação de versão/data anterior.
  - A entrada vigente apresenta estado pendente ou insuficiente.
  - Não há promoção automática com base somente no resultado antigo.

### Preservar classificação manual

#### `UI-MANUAL-01` — Conflito visível e escolha preservada
- given: oferta-manual com nova avaliação automática conclusiva divergente.
- when: abrir os detalhes.
- then:
  - A escolha manual permanece ativa.
  - O aviso de divergência mostra a evidência correspondente.
  - O controle de correção existente continua acessível por teclado.

### Aplicar atualização

#### `UI-ATUALIZACAO-01` — Nova análise não interrompe leitura
- given: oferta-versionada na lista aberta, com nova avaliação já publicada em outra revisão.
- when: a página consulta o status de atualizações.
- then:
  - O aviso “Há atualizações” é apresentado.
  - A ordem e os dados da lista aberta permanecem na revisão anterior até o clique.
  - Os filtros em uso são preservados.

## Worker

**Verification mode:** acionar trabalho persistente com fontes controladas, aguardar a conclusão ou interrupção prevista e observar avaliações publicadas, filas e contadores de inferência. Fakes são identificados; esta superfície não prova qualidade real do modelo.

### Processar imagens

#### `WRK-IMAGENS-01` — Agregação e rastreabilidade
- given: ofertas-corpus com fotos válidas distintas e duplicadas por hash no manifesto.
- when: processar a avaliação completa.
- then:
  - A análise agrega as fotos distintas dentro dos limites por chamada.
  - Cada foto exibida tem vínculo com o anúncio/observação corretos.
  - Duplicatas não exigem inferência repetida dos mesmos bytes.
  - A cobertura permite identificar o material efetivamente examinado.

#### `WRK-IMAGENS-02` — Omissão não vira boa condição
- given: ofertas-corpus com declaração positiva e parte das fotos não analisada por limite ou falha.
- when: processar a avaliação possível.
- then:
  - O resultado identifica cobertura parcial e motivo das omissões.
  - A condição automática não é promovida a boa.
  - O requisito automático de condição para envio não é satisfeito.

### Versionar análises

#### `WRK-VERSAO-01` — Entrada idêntica reaproveita resultado
- given: oferta-versionada com resultado confirmado e a mesma entrada, política, prompt/schema e modelo.
- when: submeter novamente a entrada.
- then:
  - O resultado aplicável é reutilizado.
  - Não ocorre nova inferência para essa entrada confirmada.
  - O vínculo da observação atual é explícito quando seu conteúdo idêntico foi reobservado.

#### `WRK-VERSAO-02` — Mudança relevante permite reanálise
- given: oferta-versionada com resultado confirmado e mudança de texto, foto, política, prompt/schema ou revisão do modelo.
- when: submeter a entrada alterada.
- then:
  - A avaliação anterior permanece no histórico.
  - A entrada nova recebe revisão própria e não reutiliza resultado incompatível.
  - A decisão vigente não trata a análise anterior como atual enquanto aguarda a nova.

#### `WRK-VERSAO-03` — Resultado atrasado não substitui o atual
- given: oferta-versionada com análise nova publicada e resposta pendente para entrada anterior.
- when: concluir o trabalho antigo.
- then:
  - A avaliação mais recente continua vigente.
  - O resultado antigo fica identificado como superado.
  - Não surge nova promoção ou intenção de alerta pela publicação antiga.

#### `WRK-VERSAO-04` — Concorrência converge
- given: oferta-versionada com a mesma entrada submetida por trabalhos concorrentes.
- when: processar os trabalhos concorrentes.
- then:
  - Há uma avaliação aplicável para a chave idempotente.
  - Não há duplicação de publicação da condição.
  - Referências de entrada/modelo permanecem consistentes.

### Recuperar falhas

#### `WRK-FALHA-01` — Saída inválida e conteúdo hostil
- given: oferta-versionada com respostas controladas fora do schema, trecho/foto inexistente ou instrução hostil em texto/imagem.
- when: processar cada resposta de inferência.
- then:
  - Resposta sem evidência válida não promove boa condição.
  - O motivo de rejeição/abstenção é registrado.
  - Instruções do anúncio não executam ferramentas nem alteram configuração.
  - Não são encaminhados segredos ou dados de sessão ao modelo.

#### `WRK-FALHA-02` — Falha técnica limitada e histórico preservado
- given: oferta-versionada com histórico válido e inferência que excede timeout ou retorna indisponibilidade/OOM.
- when: processar a tentativa sob o perfil limitado.
- then:
  - Há diagnóstico específico e recuperação limitada ao perfil configurado.
  - O histórico confirmado permanece disponível.
  - A falha não produz condição automática boa.
  - Evidência insuficiente não gera repetição infinita da mesma análise.

#### `WRK-FALHA-03` — Retomada após interrupção
- given: oferta-versionada interrompida antes ou depois da publicação e oferta-manual com escolha confirmada.
- when: reiniciar os processos próprios.
- then:
  - Trabalho válido é retomado sem duplicar publicação confirmada.
  - A escolha manual e os resultados confirmados sobrevivem.
  - Resultado já disponível em F19 pode ser reaproveitado sem perda de vínculo.

## E2E

**Verification mode:** executar web, worker e PostgreSQL com dados preparados; usar navegador e fronteiras públicas, observando condição, composição, fila e recibos. WAHA é fake; inferência é real apenas onde explicitamente exigida.

### Integrar condição e alertas

#### `E2E-ALERTA-01` — Não enviar antes da avaliação suficiente
- given: eventos-alerta com os demais critérios válidos, mas sem fotos ou com análise pendente/parcial/falha/inconclusiva.
- when: processar a decisão do evento pelo fluxo existente.
- then:
  - Não há envio autorizado para o destino fake.
  - A decisão registra o motivo ligado à avaliação aplicável.
  - O contador de transmissões permanece inalterado.

#### `E2E-ALERTA-02` — Resultado completo alimenta o fluxo existente
- given: eventos-alerta ainda aguardando condição, com avaliação aplicável agora suficiente, condição efetiva boa e demais critérios atuais de F09/F12 satisfeitos.
- when: processar novamente a decisão ainda pendente.
- then:
  - A condição usada corresponde à mesma observação e revisão de avaliação.
  - O fluxo existente pode autorizar uma única intenção conforme suas regras.
  - A composição financeira vem de F06/F07, sem preço ou desconto inventado pela IA.
  - O conteúdo novo qualifica a avaliação como provável e preserva ressalvas relevantes.

#### `E2E-ALERTA-03` — Ação manual não fabrica elegibilidade
- given: oferta-manual nos eventos-alerta com avaliação incompleta e formulário atual válido.
- when: salvar a escolha manual boa.
- then:
  - A aba respeita a escolha confirmada.
  - A avaliação continua incompleta para o envio automático.
  - Nenhuma intenção ou transmissão é criada pela ação manual.

#### `E2E-ALERTA-04` — Adoção preserva histórico
- given: eventos-alerta com recibo confirmado, transmissão incerta ou exclusão terminal de antes da F15.
- when: ativar a avaliação versionada sobre esses anúncios.
- then:
  - Recibos e corpos históricos permanecem intactos.
  - Envio incerto continua sujeito à reconciliação existente.
  - Não há reabertura indiscriminada de exclusões nem segundo primeiro alerta.

### Operar com progresso independente

#### `E2E-OPERACAO-01` — Inferência lenta não bloqueia coleta e leitura
- given: oferta-versionada aguardando inferência lenta e outro anúncio independente disponível para coleta.
- when: executar um ciclo de trabalho do ambiente isolado.
- then:
  - O outro anúncio publica progresso sem esperar a inferência terminar.
  - A interface continua respondendo com dados confirmados e estado de espera.
  - A tarefa lenta respeita os limites e a coordenação de recursos de F19.

### Avaliar qualidade real

#### `E2E-QUALIDADE-01` — Corpus de referência e modelo local
- given: ofertas-corpus com `assessment_cases.json` e fotos autorizadas reservadas, rótulos de referência prévios com `reference_method=ai_assisted`, rubrica por categoria e F19 real na RTX 5070.
- when: executar a análise local do conjunto reservado.
- then:
  - O relatório identifica modelo Qwen3.5 4B Q4_K_M, revisões e IDs/hashes efetivamente avaliados.
  - A comparação publica matriz referência de IA × condição automática, concordâncias, divergências e abstenções, identificando a ausência de validação humana independente.
  - Erros de evidência e limitações por categoria são publicados.
  - Consumo de GPU/RAM e latência fria/quente são registrados com as condições da medição.
  - O motor F19 avaliado não usa inferência remota; a origem de IA da referência e a ausência de validação humana independente ficam explícitas, sem alegação de precisão aprovada sem meta definida.

## Revisão de método aprovada — 2026-11-13

A aprovação explícita do usuário substitui a revisão humana prévia pela referência assistida por IA em E2E-QUALIDADE-01/F15-AC05. O item conserva seu ID e continua exigindo execução física do Qwen fixado na GPU local, hashes/proveniência, comparação por caso e medidas reais. `independent_human_review=false` e `legacy_human_acceptance_satisfied=false` são esperados para esse método e não devem ser falsificados. O aceite atual decorre desta aprovação documentada e da avaliação observável, não de mudar esses campos históricos. A referência deve estar congelada antes das predições locais; origem sintética versus real das fotos permanece explícita. Sem meta de precisão aprovada, divergências e limitações não podem ser ocultadas. Relatórios anteriores e o requisito humano então vigente ficam preservados como histórico.
