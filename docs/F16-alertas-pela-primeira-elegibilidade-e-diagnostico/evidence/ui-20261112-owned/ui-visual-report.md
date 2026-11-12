# F16 — Prova de interface e avaliação visual local

Execução em 12/11/2026, aproximadamente 12:52–13:06 UTC. Relatório de evidência auxiliar; não é avaliação canônica nem conclusão da feature.

Foram usadas as skills `playwright-cli` e `frontend-ui-design`, incluindo seus critérios visuais e `docs/design/MASTER.md`. Chromium headless, sessão exclusiva `f16-ui-owned`, viewports 1440 × 1100 e 360 × 900. As imagens citadas abaixo foram abertas e examinadas, além dos snapshots e verificações de DOM.

## Isolamento e preparo

- Factory `tests.factories.first_eligibility.first_eligibility_scenario(private, enabled=False)` mantida viva por driver temporário fora do checkout. O próprio helper executou `./scripts/init.sh --disposable` e seu lifecycle de encerramento.
- Instância `wave11b_f16_4b870bf9`; ambiente/banco `garimpei_eval_wave11b_f16_4b870bf9`; web `127.0.0.1:16972`. Worker somente dessa instância pausado durante os seeds e as leituras. Fonte e WAHA programáveis exclusivamente em loopback; grupo `100@g.us`, conta/sessão sintéticas. IA desativada. A instância real pareada na porta 20411 não foi acessada.
- Oferta principal externa `16001`, identidade `796e0fa4-7ef2-4185-859c-5f9382d39394`, inicialmente incerta. Cinco comparáveis preparados pela factory sustentaram compra R$ 1.000,00, venda R$ 1.500,00 e lucro R$ 350,00.
- Grupo sintético salvo como configurado/ativo no adapter de integração antes do primeiro POST. Esse cadastro não apareceu na UI como confirmação de mensagem.
- Os estados de identificação e amostra foram fixtures específicas de apresentação, persistidas somente no laboratório. Não constituem prova de que os respectivos produtores automáticos executaram. Duas intenções preparatórias foram encerradas no próprio seed, sem transmissão; por isso o inventário total contém três intenções e apenas uma tentativa/um POST.
- A correção posterior dos rótulos do histórico foi carregada por SIGHUP apenas no Gunicorn próprio, após conferir sua propriedade pelo manifesto. Não houve reinício do worker nessa repetição.

`commands.log` registra os comandos das jornadas de estados e seus retornos. Arquivos `*.seed.json`, `lab.json`, os snapshots e resultados complementares documentam o preparo e a observação sem arquivos de ambiente ou credenciais.

## Resultado por item

| Item | Evidência observada | Resultado e limite |
|---|---|---|
| UI-DIAGNOSTICO-01 | Lista resume o estado; detalhe apresenta motivo/data. Estados executados: nunca avaliada, data ausente, condição não confirmada, identificação pendente, comparáveis pendentes, fila, configuração, falha recuperável, transmissão incerta e confirmação histórica com impedimento atual. Imagens 01–12, 15–16 e 21–22. O [suplemento de análise](../ui-20261112-analysis/ui-analysis-supplement.md) acrescenta `analysis_pending`. | Apresentação dos estados verificada localmente, incluindo análise como fixture de leitura pública. Motivo, data e histórico permanecem legíveis a 360 px; histórico recebe foco e abre com Enter. O estado de análise não comprova produtor F15, inferência ou GPU. |
| UI-DIAGNOSTICO-02 | Navegação lista → detalhe conservou `aba=incerta`, `q=PlayStation`, `pagina=1` e versão `69981176-a0f0-4f65-ad95-5dc44e42f5b3`. Nova observação tem compra R$ 900,00, enquanto a revisão visual e o corpo autorizado mantêm R$ 1.000,00. Aviso explícito de observação mais recente aparece. | Verificado localmente: leitura não aplicou a revisão nova; filtros, página, versão e valores antigos permaneceram. O diagnóstico atual foi separado da confirmação histórica. Imagens 13–16 e 22; seed `13-newer-observation.seed.json`. |
| UI-DIAGNOSTICO-03 | Exclusivamente no banco próprio, tabela de identidade de primeiro alerta renomeada temporariamente e restaurada. Lista/detalhe continuaram legíveis, com falha específica do diagnóstico e recuperação por link da mesma jornada. | Verificado localmente: HTTP 200, título/dados preservados, sem representar erro como primeiro uso. Retry resolvia para a mesma URL, incluindo filtros/versão na oferta principal; acionado com foco + Enter após restauração. Imagens 17–20 e resultados 24. |
| E2E-PERCURSO-01, contribuição local | Oferta inicialmente incerta recebeu enriquecimento sintético da observação, preparado no laboratório, primeira elegibilidade e um POST ao grupo fake correto. Resposta foi deliberadamente tratada como perdida no seed; reconciliação real pelo gateway fake persistiu `message-1`. | Parcial: comprova composição/persistência/canal fake e UI. Parte do preparo foi comandada por adapters/casos de uso com worker pausado; não representa uma prova autônoma integral de todos os estágios agendados. Não é prova de canal real. |
| E2E-PERCURSO-02, contribuição local | Reentrada em adoção/reavaliação e reload do web próprio conservaram intenção confirmada e hash do corpo. | Parcial: sem novo POST, mas não houve reinício do worker nesta prova. Prova integral de retomada de processo deve vir das integrações específicas. |

## Data duvidosa pelo pipeline

Foi produzido um anúncio adicional, externo `16901`, com publicação textual `há 2 horas`, usando um servidor HTTP temporário em loopback. O caminho executado foi:

`FixtureSource.search/detail → consolidate → encode_evidence/decode_evidence → repository.stage/record/publish_batch → primeira elegibilidade → consulta pública → detalhe no navegador`.

A origem `fixture.published_at.invalid` sobreviveu à consolidação e à persistência; a data permaneceu ausente como instante absoluto. O diagnóstico foi `publication_untrusted`, `first_alert_state=not_sent`, e a UI mostrou **Aguardando confirmação da data de publicação**. Não foi feito seed direto desse estado final. Evidências: `23-untrusted-codec.result.json`, `ui-23-untrusted-codec.py.txt`, `23-untrusted-codec-mobile360.png` e snapshot correspondente.

## Leituras sem efeitos e corpo preservado

Antes/depois dos GETs, da falha parcial/restauração e do reload próprio, os contadores foram idênticos:

| Medida | Antes | Depois |
|---|---:|---:|
| Intenções totais, incluindo duas fixtures encerradas sem envio | 3 | 3 |
| Tentativas | 1 | 1 |
| POSTs no fake | 1 | 1 |
| Mensagens no fake | 1 | 1 |
| Chamadas totais ao fake | 12 | 12 |

Compare `result-before-get-final.json`, `result-after-get-final.json`, `result-after-web-reload.json` e `result-final.json`. Portanto as leituras também não acionaram consulta de reconciliação no fake. O corpo autorizado conservou SHA-256 `c9ec6e889f80a9978ce0d95b7887000867a8de511ce411d6437682a90baf8f6f`; comparação em `22-web-reload.result.json` e `result-hash-after.json`.

## Avaliação visual

| Dimensão | Nota | Evidência concreta |
|---|---:|---|
| Design, peso 2 | 8 | Direção Mineral consistente: fundo claro, tinta verde, tipografia Bricolage Grotesque/Manrope e composição editorial entre oferta, valores e comparáveis. O diagnóstico acompanha esse vocabulário sem competir com os valores. Imagens 02 e 14. |
| Originalidade, peso 2 | 7 | Tipografia e tratamento financeiro dão identidade própria; navegação lateral e bloco textual de diagnóstico seguem padrões convencionais. |
| Acabamento, peso 1 | 8 | Imagens desktop/mobile sem clipping ou overlay de produto ocultando conteúdo. Verificação de DOM sem overflow horizontal. Texto principal 16 px; metadados 14 px. Contrastes medidos no bloco: 13,87:1 principal, 5,32:1 metadados e 8,32:1 aviso. Ver `contrast-desktop.txt`. |
| Funcionalidade, peso 1 | 7 | Espera, incerteza e confirmação têm textos diferentes; confirmação ressalva que não comprova entrega/leitura. Recuperação funciona por teclado e conserva a jornada. No mobile, o diagnóstico vem após todos os comparáveis, exigindo uma rolagem longa para consultá-lo. |

Média ponderada: **7,5/10**. Nenhuma dimensão atingiu o limiar de reprovação visual ≤3. Essa nota não aprova automaticamente itens contratuais ausentes.

Achado durante a execução: histórico expunha códigos como `first_eligibility · uncertain`. Foi comunicado ao coordenador e corrigido pelo worker. Após reload do web próprio, nova captura e Enter confirmaram **Primeiro alerta**, **Confirmada no servidor** e **Não enviada · encerrada**, sem os códigos internos. Evidência anterior: imagem 12; correção examinada: imagem/snapshot 22 e `22-history-localized-keyboard.txt`. Achado encerrado nesta releitura visual.

Melhoria opcional: avaliar um acesso curto ao diagnóstico no topo do detalhe mobile, preservando o layout existente. A posição atual funciona, mas exige percorrer o bloco extenso de comparáveis. Não há falha de clipping ou inacessibilidade observada.

## Limitações e encerramento

- Sem Facebook autenticado real e sem WhatsApp real; não há evidência para E2E-GRUPO-01.
- IA desativada. A variante de espera por análise foi acrescentada no [suplemento](../ui-20261112-analysis/ui-analysis-supplement.md) como fixture de apresentação/DTO; o produtor F15 e a execução de análise permanecem fora desta prova. As imagens não cobrem todas as combinações possíveis de estado/revisão.
- As imagens não contêm fotos de vendedores; a fixture usa o fallback de imagem. O banner de conexão Facebook e o aviso de worker parado são esperados no laboratório.
- Único erro de console inicial observado: favicon local ausente, HTTP 404; sem erro JavaScript funcional observado na jornada.
- Não foram executados gates/suítes por esta tarefa. Nenhum fonte, teste, progresso ou avaliação canônica foi alterado por este agente.
- Encerramento e verificação de propriedade do laboratório próprio são registrados em `cleanup.json`; a sessão exclusiva `f16-ui-owned` foi fechada. Os recursos reais e os laboratórios de outros agentes foram preservados.
