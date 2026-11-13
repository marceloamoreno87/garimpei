# F15 — Implementação em andamento, escopo parcial autorizado

Base8e94dab, branch feat/F15-avaliacao-multimodal, worktree e16d. F14 permanece implemented por E2E-FONTE-01; nenhum done/clean F15 será declarado com esse pré-requisito pendente. Revisão humana do corpus ainda não recebida; rótulos permanecem nulos. Nenhuma inferência GPU/real executada nesta etapa.

Implementados: proteção textual determinística das três sondagens e escopo principal/acessório/energia; política conservadora de suficiência e precedência manual; perfil condition-evidence-v1 na fronteira/fila/gateway F19 existentes; esquema com referências literais/foto/hash, contexto conjunto por chamada limitada e preservação do perfil anterior; registro de derivados independentes sob quota F19, com pins F14 sobre os originais; avaliações e cabeças persistentes com geração, cache por conteúdo, reaproveitamento explícito por observação, publicação cercada por entrada/manifesto/modelo; diagnóstico congelado na exploração e condição compartilhada com guardas dos alertas; interface de evidências e recuperação da condição manual sem esperar inferência no GET.

Migration aditiva0021_condition_assessment sobre0020: ConditionAssessment,AssessmentHead, assessment_id/revision opcionais nas decisões regulares/de primeira elegibilidade. Flag central GARIMPEI_ASSESSMENT_ENABLED opt-in/defaultfalse. Reconciliador curto separado prepara/conclui10 ofertas por rodada; GPU permanece no executor inference de F19, sem fila nova.

Verificação até este checkpoint:85 testes de texto/política/schema/F19 passaram em2,77s;4 integrações PostgreSQL de suficiência/pins, precedência, entrada ultrapassada, concorrência e reaproveitamento passaram em16,75s. A concorrência detectou strings JSON equivalentes com ordem de chaves distinta entre memória/JSONB; contexto de inferência agora é canônico sort_keys, convergindo a uma solicitação. Seis gates Python aprovados em /tmp/f15-phase4-gates.txt; rodada HTTP/falhas ampliada6PASS21,39s. Rodada atual conjunta de regras/schema/F19/persistência79PASS23,84s e seis gates novamente PASS. Isso é checkpoint de implementação, não avaliação completa do contrato.

Ainda em trabalho: laboratório reproduzível com ações do contrato; matriz de alertas fake/adoção/retomada e prova de progresso independente; navegação por playwright-cli e acabamento; corpus humano/modelo real quando coordenado; suíte ampla/freeze após sincronização F17 validada. Pacotes de revisão em human-review-package.md, human-review-real.html e human-review-controls.html;21 controles com ilustrações sintéticas identificadas e13 fotos locais de dois anúncios reais, sem copiar sessão/URLs da fonte.

## Fechamento — 2026-11-12T22:00Z

Implementação estável em80d5fed, após aa2c6b2/060be5d/4a5b8a0. A avaliação final desta worktree registra28PASS/0FAIL/3BLOCKED em31itens;3ACs verificados e5indeterminados. Status implemented/manual-pending, sem done/clean. Bloqueios: qualidade real/revisão humana adiada explicitamente; mudança física completa de versões de política/prompt/schema/modelo sem artefato executado; ensaio completo de instrução hostil em imagem não efetuado. F14 permanece pré-requisito externo incompleto. O coordenador possui correções adicionais de vigência/identidade na união, avaliadas separadamente.

Correção1 reproduziu lotes irmãos superseded com5/12 fotos distintas e WebP omitido; migração0022 adiciona coorte/geração sem alterar default/assinatura do perfil legado.84afetadosPASS35,71s. Correção2 corrigiu cobertura pendente0/0→0/1 e digest divergente indevidamente aceito;3focaisPASS13,41s. Rodada anterior à guarda final16integraçõesPASS109,72s, preservada como checkpoint, sem extrapolá-la ao fonte posterior.

Revisão focal final autorizada demonstrou que mensagem preservava só light_wear, perdendo dano com manualgood prevalecente. RED2FAIL37,94s→GREEN4PASS95,00s; agora corpo conserva clear_defect/suspected/unknown e divergência manual. Elegibilidade/política não mudaram; E2E comprova apenasUMA mensagemfake e recibo preservado após reinício. Seis gates Python PASS novamente no fonte80d5fed. Nenhum teste total é calculado somando rodadas sobrepostas.

Playwright CLI verificou lista com atualização explícita sem perder filtros/foco/revisão, detalhes1440/390/reflow195, original640×480 carregado, navegação por teclado para foto, ausência/pendência honestas e escolha manual divergente preservada. Resultado controlado é declarado na própria interface. Operação com fake lento provou coleta/publicação/HTTP independentes; retomada atravessou dois processos Python e reutilizou resultado F19 sem nova chamada.

Todos os laboratórios/browsers F15 próprios foram encerrados; cleanup.json confirma cinco portas fechadas e stop--clean próprio exit0. Não houve uso de perfil Facebook, cópia de sessão, inferência GPU/cloud nem transmissão WhatsApp real nesta feature. Usuário deixou labels para depois; quality-report.md registra campos reais ausentes sem inventar números. Finalfull da união congelada6144193 (675 testes/110 arquivos/3shards) permanece pending até evidência do coordenador. Somente documentação/evidências foram modificadas após80d5fed.

Evidência suplementar fornecida pelo coordenador da união:6c315ca/identidade efetiva F18→assessment,12PASS43,66s;5dfcd99/prompt-schema vigente e leitura antiga,4PASS16,69s. Cópias integration-identity-assessment-after.txt/integration-assessment-version-after.txt. Não são testes executados neste HEAD e não suprem upgrade físico de modelo/política. Veredito local continua conservador.


## Retomada de2026-11-13

F14 agora done. Corrigido diagnóstico técnico mascarado quando a descrição não declarava funcionamento, com4regressões hostis através das fronteiras reais F14/F15/F19 e transporte controlado. Quatro migrações de metadados legados sintéticos comprovam revisão/fingerprint/abstenção/histórico sem trocar pesos de produção.

Preparado pacote offline23casos com9originais reais autorizados/18 ilustrações/3 regressões e export humano vinculado ao manifesto, mantendo todoslabels nulos. Adicionado executor real de qualidade com validação anterior a runtime, propriedade eval, fila exclusiva, recusa de fake e relato de matriz/erros/recursos;19 unit e1integração controlada aprovados. Modelo/GPU próprios foram preparados pelo coordenador somente com calibração sintética F19. Corpus reservado continua sem execução aguardando revisão efetiva e depois medição real.

Fonte backend congelada em f25a4e0, precedida por31b327a. Seis gates e regressões afetadas aprovados; baseline724 reutilizado para entradas inalteradas, full após mudanças consolidado separadamente pelo coordenador. Ver novo eval-report desta data. A feature permanece implemented/pending, nunca done por preparação documental/técnica.
