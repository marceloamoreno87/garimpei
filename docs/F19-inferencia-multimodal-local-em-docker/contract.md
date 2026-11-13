# Contrato — F19 Inferência multimodal local em Docker

*Gerado por spec-writer. Edições manuais serão substituídas na regeneração.*

## Prerequisites

Estas condições são entregáveis futuros. Não há inferência real ou preparo de GPU comprovados por gerar este documento; pré-requisito ausente mantém seus itens pendentes.

### Runtime services

- Django, worker e PostgreSQL em ambiente de avaliação próprio criado pelos scripts F02, com portas, banco `garimpei_` e identidade verificáveis. O procedimento de criação/verificação/encerramento fica em `operations.md`.
- Serviço Ollama oficial e volume persistente do ambiente; prova real com GPU NVIDIA e exclusividade entre ambientes Garimpei. uv/Python e playwright-cli disponíveis. Ausência de F14/F15/F17 não bloqueia o contrato.

### Persistent state

- **Observação de teste:** anúncio/observação F12 e duas revisões de texto/imagem, mais resultado anterior e recibos de alerta de controle. Criação por factories/migrations e confirmação por leituras públicas e registros do cenário isolado. Usada por: SVC-ANALISE-01, SVC-ANALISE-02, SVC-COBERTURA-01, WRK-VALIDACAO-01, WRK-VALIDACAO-02, WRK-RETOMADA-01, WRK-RETOMADA-02, E2E-ISOLAMENTO-01.
- **Fila de teste:** partes pendentes, uma em execução e casos no limite de admissão; controle habilitado/pausado com revisão conhecida. Produção por factories e verificação em status/consulta de requisições. Usada por: API-CONTROLE-01, UI-OPERACAO-01, UI-OPERACAO-02, WRK-LIMITES-01, WRK-FALHAS-01, WRK-PAUSA-01, WRK-PAUSA-02, WRK-INATIVIDADE-01, E2E-COEXISTENCIA-01.
- **Ambientes A/B:** recursos próprios distintos, incluindo serviço/pesos/resultados e reserva de GPU. Criação pelo padrão `prepare_instance`; verificar labels/manifest, portas e dados de controle antes de qualquer falha. Usados por: CLI-PREPARO-01, WRK-RETOMADA-01, E2E-ISOLAMENTO-01.

### Static inputs

- `apps/backend/tests/fixtures/inference/cases.json`, a produzir: manifesto de hashes/revisões, texto normal/contraditório/hostil/Unicode/longo, saída esperada por schema, resposta inválida/recusa e cenários de falha. Usado por: SVC-ANALISE-01, SVC-ANALISE-02, SVC-COBERTURA-01, WRK-VALIDACAO-01, WRK-VALIDACAO-02, WRK-LIMITES-01, WRK-FALHAS-01, WRK-RETOMADA-01, WRK-RETOMADA-02.
- `apps/backend/tests/fixtures/inference/{image-a,image-b}.png`, a produzir: imagens sintéticas identificadas, licença/origem de geração e hashes no manifesto; versões diferentes distinguíveis. Usadas por: SVC-COBERTURA-01, E2E-GPU-01, E2E-LOCALIDADE-01, E2E-MEDICAO-01.
- `docs/F19-inferencia-multimodal-local-em-docker/model-lock.json`, a produzir pelo preparo: imagem/versionamento/digest completo, manifesto/blobs/tokenizer e capacidades. Verificação independente contra runtime e metadados oficiais antes dos itens reais. Usado por: CLI-PREPARO-01, E2E-GPU-01, E2E-LOCALIDADE-01, E2E-MEDICAO-01.
- **Foto autorizada:** manifesto privado externo ao checkout com arquivo legível, origem/autorização e hash, verificado pelo preparo; nenhum perfil/cookie acompanha a imagem. Usada por: E2E-GPU-01, E2E-MEDICAO-01.

### Configuration

- Modelo `qwen3.5:4b-q4_K_M`, imagem e manifesto fixados, GPU real nos itens correspondentes. `OLLAMA_NO_CLOUD=1`, um modelo carregado/uma inferência, contexto 4.096, saída até 512 tokens no perfil legado F19 e até 1.024 somente no perfil de condição F15, conforme aprovação explícita de 2026-11-13; modo equilibrado com inatividade de 300 s e conferência a cada 5 s. Reserva de saída específica do perfil participa de todas as verificações de contexto, incluindo texto, instruções/schema e orçamento visual comprovado. Entrada que não caiba é recusada, sem truncamento silencioso.
- Até 16 KiB de texto recebido/2.048 tokens textuais enviados incluindo instruções; orçamento visual comprovado; até 4 imagens, uma por chamada, PNG/JPEG até 10 MiB/20 MP, derivado até 512×512. Conexão/diagnóstico 3 s, chamada 180 s, resposta 64 KiB; até 100 pendentes, 1 GiB de dados de inferência sem pesos, lease 240 s, até três tentativas por parte com recuo 15 s/30 s e teto 300 s.
- Endpoint loopback/rede privada do ambiente, arquivos autorizados, nenhum fallback remoto/CPU silencioso. Fontes/WAHA controlados e relógio falso somente em avaliação; segredos ficam fora de fixtures, relatórios e contêiner do modelo.
- Criação, consulta e conferência dos limites efetivos devem estar disponíveis em operations.md e no diagnóstico sanitizado; valores diferentes exigem revisão documental antes da avaliação.

### External dependencies

- `OllamaGatewayFake`/`GpuProbeFake`, a produzir nas factories do projeto com laboratório HTTP loopback, para falhas/concorrência determinísticas; verificar cenário ativo e eventos capturados antes dos itens controlados.
- Fontes oficiais de imagem/pesos para preparo explícito. Depois do preparo, prova de inferência com saída externa bloqueada. Acesso ao host/contêiner GPU próprio para medições reais; se indisponível, não substituir essa prova por simulação.

## Quality gates

Cada gate deverá passar na implementação. Gerar o contrato não comprova os comandos abaixo.

- **Seis grupos Python** — `node scripts/run-gates.mjs` — tipos, lint/templates, limites, arquitetura, ciclos e não utilizados.
- **Suíte** — `uv run --project apps/backend --frozen --no-sync pytest` — regras, gateway, HTTP, fila, lifecycle e falhas isoladas.
- **Django** — `uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check --settings=garimpei.config.test_settings` — configuração verificável; migrations exercitadas também no PostgreSQL real.
- **Build** — `uv build --project apps/backend` — empacotamento das entradas/schema necessários.
- **Jornadas** — `playwright-cli` — tela operacional, pausa/retomada e falhas com evidências; avaliação visual por frontend-ui-design.
- **Prova GPU** — comando `local_ai smoke` da spec — texto/imagem no contêiner com medições, pins e isolamento, sem efeito de negócio.

## Coverage Manifest

| PRD Acceptance Criterion | Covered by |
|---|---|
| **F19-AC01**: contêiner Ollama oficial com imagem/revisão fixadas carrega `qwen3.5:4b-q4_K_M` e demonstra inferência de texto e imagem usando a RTX 5070 real; registrar passagem de GPU, uso efetivo e pico de memória. Host com `nvidia-smi` funcional não substitui a prova do contêiner. | `CLI-PREPARO-01`, `E2E-GPU-01` |
| **F19-AC02**: análise funciona localmente sem chamada a provedor de inferência externo, com cloud desabilitado, endpoint restrito ao ambiente e sem encaminhar cookies/perfil/segredos. Obter imagem/pesos no preparo é distinguido da inferência dos anúncios. | `E2E-LOCALIDADE-01`, `WRK-VALIDACAO-02` |
| **F19-AC03**: concorrência/contexto/fila/limites de imagem e timeout estão definidos no contrato e são exercitados; falta de VRAM, GPU ausente ou CPU fallback aparecem como degradação/falha explícita, sem travar web/coleta nem trocar de modelo silenciosamente. | `WRK-LIMITES-01`, `WRK-FALHAS-01`, `E2E-COEXISTENCIA-01` |
| **F19-AC04**: saída estruturada é validada; texto/foto malicioso, resultado fora do schema e falta de evidência não instruem ferramentas nem geram boa condição ou valor monetário fabricado. | `WRK-VALIDACAO-01`, `WRK-VALIDACAO-02`, `SVC-COBERTURA-01` |
| **F19-AC05**: reinício, entrada repetida e resultado atrasado preservam pesos e análises válidas, deduplicam trabalho aplicável e rejeitam publicação ultrapassada. F15 recebe modelo, revisão e evidência correspondentes. | `SVC-ANALISE-01`, `WRK-RETOMADA-01`, `WRK-RETOMADA-02`, `E2E-ISOLAMENTO-01` |
| **F19-AC06**: o teste local mede cenário frio/quente, uso de GPU/RAM, falhas e convivência com os demais processos; sem teste executado, capacidade/latência/qualidade permanecem pendentes, sem declaração de compatibilidade operacional concluída. | `E2E-MEDICAO-01` |
| **F19-AC07**: em ambiente isolado, modelo ausente/corrompido, timeout, GPU indisponível e falta de memória produzem motivos distintos e recuperação limitada conforme contrato. Parada/reinício preservam pesos e resultados confirmados e retomam trabalho válido; coleta e leitura continuam disponíveis durante falha exclusiva da inferência. Recursos de outro ambiente permanecem intactos. | `UI-OPERACAO-01`, `WRK-FALHAS-01`, `WRK-RETOMADA-01`, `E2E-COEXISTENCIA-01`, `E2E-ISOLAMENTO-01` |
| **F19-AC08**: entrada idêntica com as mesmas revisões reutiliza resultado válido sem nova inferência; mudança de texto, foto, modelo ou prompt/schema impede reutilização incompatível. O resultado identifica material examinado/omitido e sua revisão; uma resposta antiga não é publicada como atual. O smoke test de F19 não altera condição, composição financeira ou recibos e não cria envio ao WhatsApp. | `SVC-ANALISE-01`, `SVC-ANALISE-02`, `SVC-COBERTURA-01`, `WRK-RETOMADA-02`, `E2E-ISOLAMENTO-01` |
| **F19-AC09**: no modo equilibrado, trabalho válido inicia análise automaticamente quando habilitada e com recursos disponíveis. Após o intervalo de inatividade definido no contrato, comprovar descarregamento do modelo e liberação da memória correspondente, preservando pesos e resultados; novo trabalho carrega o modelo sem baixar novamente pesos íntegros. Medir o custo de recarga sem inventar meta de latência. | `WRK-INATIVIDADE-01`, `WRK-PAUSA-02`, `E2E-MEDICAO-01` |
| **F19-AC10**: pausar a IA impede novas inferências e mostra o estado da pausa e de eventual análise em execução, conforme a política definida no contrato. A fila e os resultados confirmados são conservados, coleta e consulta continuam disponíveis e retomada explícita processa trabalho ainda válido sem publicar revisão ultrapassada. Distinguir pausa manual, descarregamento por inatividade e espera por recurso. | `API-CONTROLE-01`, `UI-OPERACAO-02`, `WRK-PAUSA-01`, `WRK-PAUSA-02`, `E2E-COEXISTENCIA-01` |

## Service

**Verification mode:** invocar a interface de requisição/consulta consumível por F15 com cliente de teste, observar resposta, resultado/cobertura e persistência; sem exigir F15 implementada.

### Análise versionada

#### `SVC-ANALISE-01` — Trabalho rastreável e reaproveitamento compatível
- given: observação de teste com requisição válida e mesmas revisões de entrada/modelo/prompt/schema/opções.
- when: solicitar sua análise novamente.
- then:
  - Retorna trabalho já em curso ou resultado válido compatível.
  - Não inicia inferência duplicada para a mesma assinatura.
  - Consulta identifica observação/revisão, modelo/digest e prompt/schema correspondentes.

#### `SVC-ANALISE-02` — Invalidação por mudança relevante
- given: observação de teste com resultado e variante alterando texto, foto, revisão, modelo ou prompt/schema.
- when: solicitar análise da variante.
- then:
  - Não reutiliza resultado integral incompatível.
  - Resultado anterior continua identificado como anterior.
  - Requisição atual identifica sua própria cobertura e proveniência.

### Cobertura de material

#### `SVC-COBERTURA-01` — Examinado, omitido e ausente
- given: observação de teste e corpus com texto/imagens dentro e fora dos limites, incluindo entrada sem evidência utilizável.
- when: consultar o resultado após processamento.
- then:
  - Identifica material fornecido, enviado, efetivamente examinado e omitido com motivo/revisão/hash.
  - Foto omitida ou parte falha não é apresentada como analisada.
  - Referência retornada aponta apenas para trecho/imagem presente naquela entrada examinada.
  - Ausência de evidência utilizável não produz conclusão confirmada.

## HTTP API

**Verification mode:** enviar comandos e leituras HTTP ao Django; observar status, resposta e mudança persistida direta do controle.

### Controle de operação

#### `API-CONTROLE-01` — Pausa/retomada confirmadas
- given: fila de teste e revisão conhecida do controle; variantes com CSRF ausente, corpo inválido, revisão antiga e falha de gravação.
- when: enviar o comando de pausa ou retomada.
- then:
  - Comando válido confirma intenção persistida e redireciona à tela operacional.
  - Repetir intenção já vigente é idempotente.
  - Rejeição informa 400/403/409 conforme formato/CSRF/revisão; falha de gravação informa 503.
  - Ação não persistida não aparece como concluída.

## CLI

**Verification mode:** executar local_ai no ambiente escolhido e observar saída legível, código, artefatos e recursos próprios; sem imprimir segredos.

### Preparação e diagnóstico

#### `CLI-PREPARO-01` — Pin verificado antes de uso
- given: ambientes A/B e lock com variante válida, divergente ou incompleta, sem manipular recursos alheios.
- when: executar preparação explícita ou diagnóstico dos artefatos.
- then:
  - Identifica imagem/revisão/digests completos e capacidades realmente disponíveis.
  - Pin ausente/divergente ou download incompleto impede anunciar modelo pronto.
  - Não atualiza modelo silenciosamente nem usa latest como pin.
  - Códigos distinguem sucesso, pré-requisito ausente e falha; saída não contém material privado.

## UI

**Verification mode:** navegar na tela de IA em Integrações via playwright-cli; observar estados, foco, mensagens e screenshots em desktop e 360 px.

### Operação local

#### `UI-OPERACAO-01` — Diagnóstico por causa
- given: fila de teste com variantes de serviço ausente, pesos ausentes/corrompidos, GPU indisponível/degradada, falta de memória, timeout e saída inválida.
- when: abrir o diagnóstico da IA.
- then:
  - Informa motivos distintos e próxima ação possível.
  - Distingue serviço respondendo de modelo pronto/residente e análise em curso.
  - Mostra modelo/versão, horário e fila sem cookies, QR, segredos ou payload privado.
  - Resultado anterior permanece identificado como anterior.

#### `UI-OPERACAO-02` — Pausa e residência compreensíveis
- given: fila de teste com variantes de pausa manual, chamada em drenagem, modelo descarregado por inatividade e espera de recurso.
- when: consultar a tela operacional.
- then:
  - Mostra estados diferentes para essas situações.
  - Não anuncia GPU liberada enquanto não houver confirmação de descarregamento.
  - Oferece ação de retomada da pausa manual com resultado confirmado ou erro recuperável.
  - Controles e mensagens permanecem acessíveis por teclado e a 360 px.

## Worker

**Verification mode:** processar fila persistente em PostgreSQL com gateway/GPU controlados e, nos itens de memória, serviço real; observar resultados, efeitos, chamadas e recursos próprios.

### Limites e falhas

#### `WRK-LIMITES-01` — Capacidade finita sem bloquear o restante
- given: fila de teste, limites contratuais ativos e cenários concorrentes nos tetos de contexto/imagem/saída/fila/disco.
- when: admitir ou processar uma nova parte.
- then:
  - Respeita limites mesmo sob concorrência; excesso recebe motivo explícito.
  - Não ultrapassa uma inferência em execução nem ocupa todos os slots do worker.
  - Contexto não comprovado, truncamento oculto ou término por limite não são sucesso válido.
  - Trabalho confirmado e arquivos originais continuam preservados.

#### `WRK-FALHAS-01` — Recuperação limitada por causa
- given: fila de teste e fake com serviço indisponível, modelo ausente/corrompido, GPU ausente/degradada, OOM ou timeout.
- when: processar a parte afetada.
- then:
  - Persiste causa específica e preserva resultado confirmado anterior.
  - Falha técnica recuperável respeita timeout, máximo de três tentativas e recuo contratual.
  - Esgotamento suspende com próxima ação, sem troca de modelo/fallback silencioso.
  - Execução incerta não autoriza iniciar chamada sobreposta antes de confirmar seu encerramento.

### Validação de resultado

#### `WRK-VALIDACAO-01` — Saída estruturada tem fronteira de confiança
- given: observação de teste e resposta recusada, inválida, incompleta, com referência inexistente ou campo adicional de comando/valor monetário.
- when: receber a resposta do modelo.
- then:
  - Rejeita a resposta como resultado válido e informa motivo.
  - Não executa ferramentas/comandos contidos na saída.
  - Não cria boa condição, composição financeira ou intenção de alerta.
  - Material não examinado não recebe evidência fabricada.

#### `WRK-VALIDACAO-02` — Instruções hostis são conteúdo
- given: observação de teste com texto/foto contendo instrução para expor segredo, mudar escopo, contatar vendedor ou inventar lucro.
- when: executar análise dessa entrada.
- then:
  - Nenhuma dessas ações externas é executada.
  - Cookies/perfis/credenciais não são enviados ao contêiner nem aparecem na resposta.
  - Resposta somente pode ser publicada após validação de schema e referências.

### Retomada e concorrência

#### `WRK-RETOMADA-01` — Persistência após interrupção
- given: observação/fila de teste no ambiente A com parte confirmada e outra em curso; ambiente B com dados próprios intactos.
- when: interromper e reiniciar os processos próprios de A.
- then:
  - Pesos, partes confirmadas e resultados persistem.
  - Retoma apenas trabalho válido, reutilizando partes compatíveis.
  - Não publica resultado incompleto nem duplica resultado lógico.
  - Dados/processos/volumes/perfil de B permanecem intactos.

#### `WRK-RETOMADA-02` — Resposta ultrapassada não vira atual
- given: observação de teste cuja revisão ou geração da posse mudou durante a chamada.
- when: chegar a resposta antiga.
- then:
  - Não substitui resultado correspondente à revisão atual.
  - Consulta identifica o resultado como histórico/superseded quando conservado.
  - Recibos, escolhas manuais e composição existentes permanecem intactos.

### Modo equilibrado

#### `WRK-INATIVIDADE-01` — Descarregar e recarregar sem download
- given: fila de teste concluída, modelo residente no serviço real próprio e 300 s sem uso.
- when: vencer o período de inatividade.
- then:
  - Inspeção confirma descarregamento e redução da memória correspondente, registrando tempo real.
  - Pesos e resultados continuam disponíveis em disco.
  - Novo trabalho habilitado recarrega o mesmo artefato sem novo download.
  - Métricas de recarga não são apresentadas como meta de latência aprovada.

#### `WRK-PAUSA-01` — Pausar com chamada em curso
- given: fila de teste com uma chamada em curso e outras partes pendentes.
- when: persistir pausa manual.
- then:
  - Nenhuma nova inferência/parte começa após a pausa confirmada.
  - Chamada em curso fica visível e pode concluir somente dentro do timeout contratual.
  - Fila e resultados confirmados permanecem conservados.
  - Após a chamada, tenta descarregar e somente anuncia liberação após confirmação; falha de unload mantém bloqueio explícito.

#### `WRK-PAUSA-02` — Retomada explícita da fila válida
- given: fila de teste pausada manualmente com revisões ainda válidas e outras substituídas.
- when: confirmar retomada manual.
- then:
  - Trabalho válido volta ao processamento automático quando houver recurso.
  - Revisão substituída não é publicada como atual.
  - Inatividade posterior não se confunde com nova pausa manual.

## E2E

**Verification mode:** executar stack própria com RTX 5070 real nos itens GPU, instrumentação de contêiner/rede/GPU e aplicação isolada; guardar medições sanitizadas junto da feature.

### GPU e inferência local

#### `E2E-GPU-01` — Texto e imagem no contêiner real
- given: lock verificado, RTX 5070 acessível ao contêiner, imagens sintéticas e foto autorizada identificadas.
- when: executar o smoke test local de texto e imagem.
- then:
  - Produz resultado estruturado válido rastreável às entradas e artefatos fixados.
  - Demonstra uso efetivo da RTX 5070 durante a chamada no contêiner, além da visibilidade no host.
  - Registra residência/contexto e pico de VRAM/RAM.
  - Não depende da implementação de F14/F15 nem altera condição, preço ou alertas reais.

#### `E2E-LOCALIDADE-01` — Inferência sem saída externa
- given: lock/pesos preparados, imagem de teste e rede externa bloqueada no serviço próprio.
- when: executar análise local.
- then:
  - Análise conclui usando somente o endpoint local selecionado.
  - Evidência de configuração/tráfego confirma cloud desabilitado e ausência de chamada de inferência externa.
  - API permanece restrita ao ambiente, sem exposição na rede ou chamada direta pelo browser.
  - Contêiner não recebe mounts/payloads de perfil, sessão ou credenciais.

### Medição e isolamento

#### `E2E-MEDICAO-01` — Custo real de uso equilibrado
- given: lock verificado, entradas de texto/imagem identificadas e demais processos locais disponíveis no ambiente próprio.
- when: executar ensaio com chamadas frias, quentes e convivência.
- then:
  - Registra tempos, uso efetivo GPU e pico VRAM/RAM por cenário.
  - Identifica CPU/offload parcial como degradação, sem alegar aceleração plena.
  - Registra liberação por inatividade e custo de recarga.
  - Explicita limites e falhas; teste não executado não vira compatibilidade ou qualidade aprovada.

#### `E2E-COEXISTENCIA-01` — Falha exclusiva de IA
- given: fila de teste e aplicação própria com coleta controlada e dados consultáveis; inferência indisponível ou chamada lenta.
- when: observar um ciclo de trabalho independente.
- then:
  - Coleta continua publicando seu progresso confirmado.
  - Interface continua lendo dados e aceita controles.
  - Alertas independentes mantêm seu processamento pelo canal fake.
  - Diagnóstico atribui bloqueio à IA sem fabricar condição ou lucro.

#### `E2E-ISOLAMENTO-01` — Smoke test sem efeito de negócio
- given: ambientes A/B, observação de teste e snapshots de condição, composição e recibos anteriores.
- when: executar preparo/smoke e parada normal de A.
- then:
  - Condição, composição, recibos e ausência de novos envios reais correspondem ao baseline.
  - Pesos e análises confirmadas de A persistem após parada normal.
  - Nenhum recurso de B é encerrado, alterado ou usado para inferência concorrente.
  - Falhas destrutivas usam somente contêiner/volume descartável explicitamente próprio.
