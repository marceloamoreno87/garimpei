# Contract: F01 — Discovery e viabilidade de integrações

*Gerado por spec-writer. Edições manuais serão substituídas na regeneração.*

## Prerequisites

Condições para a execução e revisão **futuras** deste contrato. Prepará-las faz parte da entrega da feature; condição ausente impede o cenário correspondente e não representa aprovação. A geração de spec/plano/contrato não satisfaz os itens abaixo por si só.

### Runtime services

- Git, Bash e Node disponíveis no checkout usado para as verificações do harness. Preparação: disponibilizar as ferramentas na execução autorizada, conforme ambiente do projeto; verificação: comandos de versão e os comandos de Quality gates. Registrar as versões efetivamente utilizadas. Serviços Django, PostgreSQL e WAHA não são necessários à revisão documental.

### Static inputs

- `docs/PRD.md`, `docs/stack.md`, `docs/harness.md`, `docs/architecture/` e `AGENTS.md`: requisitos e restrições canônicos. Preparação: disponibilizar os arquivos do checkout sem sobrescrever alterações existentes; verificação: leitura e confronto com as afirmações dos entregáveis. Usados por todos os itens.
- Documentação/evidência de investigação: produzir futuramente `report.md`, `evidence-index.md`, `environment.md` e `decisions.md` nesta pasta, conforme spec §§4–5. Verificação: arquivos legíveis, referências resolvíveis, matriz das quatro candidatas e separação entre recomendação/decisão. Usados por todos os itens; ausência indica entrega ainda incompleta, não dispensa de avaliação.

### Configuration

- Escopo de prova prática: criar registro de ações, plataformas, entradas, limites de duração/requisição/custo, recursos e limpeza em `environment.md`, quando uma prova for proposta. Verificar referência à autorização explícita antes da execução; sem ela somente investigação documental, com lacunas declaradas. Usado por DOC-COMPARACAO-03 e DOC-AMBIENTE-01–04.
- Não há segredo obrigatório para revisão documental. Quando uma prova autorizada depender de conta, CEP, sessão, chave ou destinatário, provisionar privadamente só as entradas requeridas e verificar presença/prontidão sem imprimir valores. Uma entrada faltante fica identificada no resultado da prova correspondente, nunca substituída silenciosamente por dado fictício.

### External dependencies

- Fontes primárias das candidatas e componentes, com URL/data de consulta e distinção entre informação documentada e observada. Preparação: pesquisar na execução de F01; verificação: abrir a referência ou evidência sanitizada e conferir o suporte da afirmação. Fonte indisponível gera lacuna com impacto e próximo passo; não exige serviço externo em funcionamento para reconhecer a lacuna.
- Provas externas, se autorizadas, exigem as contas/recursos definidos no escopo e evidência sanitizada de sua disponibilidade. Preparação e verificação seguem `environment.md`; falhas de acesso não comprovam capacidade. Mensagem real exige autorização específica e destinatário definido; não é pré-requisito para uma avaliação documental com limitações declaradas.

## Quality gates

Cada gate aplicável deve passar para a feature ser considerada pronta. Estes gates verificam o harness; o aceite documental depende também dos itens abaixo.

- **Estrutura do harness** — `node scripts/check-harness.mjs` — referências, configuração, sintaxe e progresso estruturalmente válidos.
- **Regressão do harness** — `node --test scripts/test/harness.test.mjs` — testes existentes aprovados, sem atribuir a eles validação de Django ou integrações reais.

Gates da aplicação têm entrada canônica `node scripts/run-gates.mjs`, cuja adaptação e execução Python pertencem à F02. Backend/dependências ausentes são pré-requisitos não atendidos; o erro atual de código 64 não é aprovação. F01 não entrega backend: nenhuma das seis coberturas Python é declarada aprovada aqui. O documento de passagem deve exigir comandos verificáveis para tipos, lint, dependências, arquitetura, ciclos e código/dependências não utilizados, mais testes/build pertinentes, antes da implementação da fundação.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F01-AC01**: a comparação documenta as candidatas citadas, acesso, autenticação, dados, custos, estabilidade, manutenção e limitações, com evidências ou lacunas explícitas por alternativa. | DOC-COMPARACAO-01, DOC-COMPARACAO-02, DOC-COMPARACAO-03 |
| **F01-AC02**: o relatório avalia categorias, produtos por nome/modelo, geografia/entrega, frete, acompanhamento de anúncios e recuperação após interrupção, além de referências de usados e novos. | DOC-COBERTURA-01, DOC-COBERTURA-02, DOC-COBERTURA-03, DOC-COBERTURA-04 |
| **F01-AC03**: o relatório avalia execução local, recursos do computador, WAHA, intervalo e latência viáveis, sem inventar compatibilidade, custo ou disponibilidade quando faltarem dados. | DOC-AMBIENTE-01, DOC-AMBIENTE-02, DOC-AMBIENTE-03, DOC-AMBIENTE-04 |
| **F01-AC04**: a recomendação identifica primeira plataforma e estratégia sugeridas, com limitações e decisões ainda necessárias; a escolha final é registrada separadamente da recomendação, sem credenciais ou cookies. | DOC-RECOMENDACAO-01, DOC-RECOMENDACAO-02, DOC-RECOMENDACAO-03 |

## Documentação

**Verification mode:** Abrir os entregáveis, seguir suas referências e comparar o conteúdo com o PRD. Conferir evidências sanitizadas e decisões registradas; a presença de uma lacuna pode ser verificada, mas não comprova a capacidade ausente. Não requer aplicação futura nem testes de produção para ler os documentos. Código de superfície: `DOC`.

### Comparação das alternativas

#### `DOC-COMPARACAO-01` — Quatro candidatas comparáveis

- given: comparação disponível para revisão.
- when: consultar a matriz de alternativas.
- then:
  - OLX, Facebook Marketplace, Enjoei e Mercado Livre estão identificados separadamente.
  - Cada alternativa apresenta acesso, autenticação, dados úteis, custos, estabilidade, manutenção e limitações.
  - Esforço inicial e condições para uso local estão identificados por alternativa.
  - Cada dimensão contém evidência referenciada ou lacuna explícita.

#### `DOC-COMPARACAO-02` — Estratégias de acesso e limites

- given: alternativas documentadas com as fontes disponíveis.
- when: consultar a avaliação das formas de acesso.
- then:
  - API, páginas públicas, sessões com cookies e scraping avançado são avaliados por candidata, inclusive quando indisponíveis ou não verificados.
  - Autenticação, mecanismos antirrobô e restrições conhecidas de cada modalidade estão descritos com seu suporte ou lacuna.
  - Informação documentada, observação prática e inferência são distinguíveis.

#### `DOC-COMPARACAO-03` — Evidência ausente ou acesso malsucedido

- given: dimensão não verificada ou tentativa autorizada com falha, autenticação exigida, timeout ou bloqueio.
- when: consultar a conclusão correspondente.
- then:
  - A lacuna ou falha aparece com contexto, data, impacto e próximo passo.
  - O resultado não é apresentado como acesso bem-sucedido, lista vazia comprovada ou impossibilidade definitiva sem suporte.
  - Uma prova citada permite localizar escopo autorizado, método e evidência sanitizada; quando não realizada, isso fica explícito.

### Cobertura do monitoramento e das referências

#### `DOC-COBERTURA-01` — Categorias e nome/modelo

- given: avaliação das candidatas disponível.
- when: consultar a cobertura dos interesses de monitoramento.
- then:
  - Obtenção de categorias/subcategorias e de anúncios associados é avaliada por alternativa.
  - Busca de produtos por nome/modelo é avaliada separadamente.
  - Limitações de correspondência e sobreposição de interesses estão identificadas, sem pressupor equivalência de produtos.

#### `DOC-COBERTURA-02` — Geografia, entrega e frete

- given: fontes com informação geográfica, de entrega ou lacunas identificadas.
- when: consultar a avaliação de cobertura geográfica.
- then:
  - A viabilidade de retirada em São Paulo (SP), até 20 km do CEP configurado, é avaliada com evidência ou lacuna.
  - A viabilidade de envio nacional com entrega no CEP é avaliada separadamente.
  - Origem, precisão e insuficiência dos dados de localização/entrega estão identificadas.
  - Disponibilidade de frete informado é distinguida de estimativa; frete estimado não comprova entrega.

#### `DOC-COBERTURA-03` — Acompanhamento e recuperação

- given: informações de identificação e atualização das fontes disponíveis ou lacunas registradas.
- when: consultar a avaliação do ciclo dos anúncios.
- then:
  - Identidade, link, preço, condição e localização disponíveis são descritos com limites por fonte.
  - Atualização, remoção, duplicatas e republicações têm possibilidades e incertezas identificadas.
  - A recuperação de publicações e mudanças após interrupção considera janela histórica, paginação e disponibilidade na origem.
  - O relatório não promete recuperar dados que a fonte deixou de disponibilizar.

#### `DOC-COBERTURA-04` — Usados semelhantes e referência de novos

- given: possíveis fontes de preço pesquisadas ou ausência de evidência identificada.
- when: consultar a avaliação das referências de preço.
- then:
  - Fontes e qualidade de usados semelhantes são avaliadas separadamente da referência de produto novo.
  - Equivalência, atualidade, tamanho de amostra, discrepantes e confiança têm dados disponíveis ou lacunas registrados.
  - Ausência de referência não é convertida em preço zero nem em estimativa confirmada.
  - Limiares e método ainda não decididos são destinados à especificação de F06.

### Viabilidade local e preparação da fundação

#### `DOC-AMBIENTE-01` — Recursos reais e compatibilidade

- given: inventário local realizado dentro do escopo autorizado ou impedimento registrado.
- when: consultar a avaliação da execução local.
- then:
  - CPU/arquitetura, RAM, disco e limites relevantes de WSL2/Docker têm origem, data e valores observados ou lacunas explícitas.
  - Recursos do host, recursos disponíveis ao ambiente e consumo observado são distinguíveis.
  - A operação considerada preserva web/worker no WSL2, PostgreSQL/WAHA em Docker, localhost sem login e ausência inicial de Redis.
  - Compatibilidade sem medição ou suporte não é afirmada como testada.

#### `DOC-AMBIENTE-02` — WAHA e limites da prova

- given: avaliação documental de WAHA e eventuais provas autorizadas disponíveis.
- when: consultar a conclusão de viabilidade do WAHA.
- then:
  - Versão/imagem/engine considerada, requisitos locais, configuração de sessão, persistência e custos têm evidência ou pendência identificada.
  - Disponibilidade de processo, autenticação da sessão e entrega de mensagem são resultados distintos.
  - Qualquer envio citado como realizado tem escopo autorizado e resultado observado sanitizado; envio não realizado não é apresentado como sucesso.

#### `DOC-AMBIENTE-03` — Intervalo, latência e custo

- given: estimativas documentais ou medições delimitadas disponíveis.
- when: consultar a proposta operacional.
- then:
  - Intervalo e latência viáveis ou ainda desconhecidos têm justificativa ligada ao acesso, recursos e custos.
  - Medição informa condições, duração e quantidade de observações; estimativa é identificada como estimativa.
  - Tempo da fonte, coleta, processamento/fila e envio são distinguidos, sem fabricar latência ponta a ponta.
  - Custos desconhecidos ou condicionados não aparecem como gratuidade confirmada.
  - O relatório não exige operação 24 horas nem promete disponibilidade enquanto o computador/processos estiverem parados.

#### `DOC-AMBIENTE-04` — Preparação e integração seletiva

- given: requisitos de ambiente e limitações da comparação consolidados.
- when: consultar o documento de passagem para F02.
- then:
  - Cada pré-requisito identifica forma de preparação, verificação e consequência da ausência.
  - O mapa prevê base Django em temporário e integração seletiva em F02, preservando arquivos canônicos e alterações existentes.
  - Lifecycle, isolamento, migrations, configuração e preservação de dados/sessão têm verificações de aceite propostas para a fundação.
  - As seis coberturas Python e testes/build pertinentes exigem comandos reais no contrato de F02, com entrada `node scripts/run-gates.mjs`.
  - Ausência de aplicação/validadores e resultados TypeScript não são apresentados como gates Python aprovados.

### Recomendação e decisão

#### `DOC-RECOMENDACAO-01` — Recomendação rastreável

- given: comparação, cobertura e viabilidade consolidadas.
- when: consultar a recomendação.
- then:
  - Primeira plataforma e estratégia sugeridas estão identificadas; insuficiência para recomendar sem condições está explícita quando aplicável.
  - A justificativa compara alternativas por cobertura, esforço, recursos, custos, estabilidade e manutenção, com referências às evidências.
  - Limitações e decisões ainda necessárias têm impacto e destino identificados.
  - Inviabilidade de requisito obrigatório é encaminhada à decisão explícita, sem reduzir o MVP implicitamente.

#### `DOC-RECOMENDACAO-02` — Escolha final separada

- given: decisão explícita do usuário sobre plataforma e estratégia disponível.
- when: consultar o registro da escolha final.
- then:
  - Plataforma, estratégia, condições, data e referência à decisão estão registradas separadamente da recomendação.
  - Aprovação não é inferida de preferência técnica ou de aprovação anterior da stack.
  - Impactos e pendências encaminhados a F02/F03/F04/F06/F09 estão identificados conforme o requisito afetado.
  - Documentos e evidências não incluem credenciais, cookies ou material de sessão privado.

#### `DOC-RECOMENDACAO-03` — Aprovação ainda ausente

- given: recomendação disponível, sem decisão explícita da primeira plataforma/acesso.
- when: consultar o estado da decisão.
- then:
  - O registro apresenta a escolha como pendente.
  - A passagem para F02 e o aceite final da escolha permanecem pendentes.
  - A recomendação continua identificada como sugestão, sem aprovação presumida.
- notes: Este cenário verifica o tratamento da pendência; não substitui a evidência positiva de DOC-RECOMENDACAO-02 para concluir F01.
