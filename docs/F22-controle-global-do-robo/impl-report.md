# F22 — Relatório de implementação

Base `a73642d`; branch `wave/20261113-f22`, worktree isolada `c4f1`. Commits: `eacd946` (controle/portas/migration), `5793861` (integração por unidade e evidências) e `8f10673` (corrigir a disputa da pausa com pré-checks do canal). Integração e push pertencem ao coordenador.

## Comportamento entregue

Controle persistente por instalação, ações explícitas idempotentes com UUID/revisão, separação entre intenção e execução, comandos HTTP com CSRF, leitura sem cache, painel em Acompanhamento e resumo nas ofertas. Pausa conserva as preferências particulares e a consulta. O estado não é apresentado como parado quando há autorização indeterminada ou proprietário desaparecido.

Admissão global ordenada antes da publicação e locks específicos. Os pontos de execução abrangem navegação e investigação, sugestões, pesquisa F18, cada chamada de página do browser/retail, candidatos/derivados de mídia, identificação automática, valoração, preparação/fotos/partes da análise, cada parte de inferência e autorização final de mensagem. Permissões registram chave de negócio, revisão, geração e proprietário PID/data de criação. Conclusão de unidade já autorizada conserva resultado/recibo; recuperação específica continua necessária para fechar incerteza. Desaparecimento do processo é diagnóstico de incerteza, não confirmação de encerramento remoto.

Jobs negados não consomem o orçamento de falhas. Claims de mídia, valoração e pesquisa podem devolver a preparação; a fila de navegação não encadeia continuação nem renova lease quando pausada. Reconciliação de envio incerto continua sem POST novo; `safe_retry` espera habilitação. O pré-check que falha após uma pausa concorrente também conserva failures/next_action/estado; a regressão reproduziu duas falhas antes da correção.

Migração aditiva `0026_robot_control` adota intenção habilitada, sem iniciar processo e sem substituir preferência existente. Controle, comandos e posse de operações são estado local da instalação: cópia de negócio preserva a decisão do destino e não transporta esses três modelos. O classificador explícito de schema permanece obrigatório; sua falta causou `archive_business_schema_incomplete`, reproduzido e corrigido com regressão de backup real.

## Artefatos e validação

- Factory `tests/factories/robot.py`, corpus `tests/fixtures/robot/control_cases.json` e testes `test_robot_*` cobrem serviço persistido, concorrência, migração, incerteza, retomada da IA, mensagens, mídia, navegação, backup e pré-checks do canal.
- [Seis gates](evidence/six-gates-precheck-fix-wave13.txt): exit 0 após a correção de pré-check. Django check e `makemigrations --check --dry-run`: exit 0. [Build wheel](evidence/build-wave13.txt), [harness](evidence/harness-wave13.txt) e check-harness passaram.
- [Pré-check: RED 2 falhas](evidence/alert-precheck-red-wave13.txt) → [GREEN 10 testes](evidence/alert-precheck-green-wave13.txt). Os testes de serviço/IA, página/mídia e migração foram também exercidos em PostgreSQL isolado; resultados finais de regressão completa cabem à fonte integrada do coordenador.
- [Navegador e avaliação visual](evidence/browser-and-visual-review-wave13.md): desktop/390 px, teclado, duas abas, erros HTTP e recuperação do polling. Dois defeitos observados (perda de foco e documento completo em poll de erro) foram corrigidos e rechecados.
- [Jornada com worker real](evidence/real-worker-browser-wave13.json): POST fake já autorizado foi retido; o botão mostrou Desligando; a resposta concluiu o mesmo recibo enquanto pausado; stop/init preservou pausa e corpo; ligar retomou coleta e uma redução, sem repetir o primeiro alerta. Essa jornada não substitui todas as variações de jobs de cada estágio.

Uma execução preliminar da suíte unit/http/quality da raiz, com fonte em alteração concorrente, produziu 524 PASS/5 FAIL. O teste CLI depende do cwd backend; passou sem alteração de assertiva com `uv run --directory apps/backend`. Quatro casos HTTP de diagnóstico/financeiro/condição passaram na repetição estável (83,11 s). O quinto defeito, backup507, foi reproduzido e corrigido; o caso original e a nova regressão passaram (26,30 s). Não se declara a execução original limpa. A suíte completa final deve usar a fonte integrada congelada e cwd backend.

## Operação e limites de avaliação

Atualização exige parar/substituir os consumidores antigos desta instalação pelo lifecycle próprio antes de declarar a barreira disponível; migration não encerra processos. A prova de adoção parou e verificou os processos pertencentes ao banco descartável antes de recuar/avançar schema. Reinício normal no mesmo banco conserva intenção; restauração de cópia de negócio não deve copiar o comando de outra instalação.

Toda execução usou origem/canal sintéticos locais. Não houve Facebook, WhatsApp real ou GPU. Segredos permanecem em env privados; laboratórios e instâncias próprios foram encerrados e limpos. As capturas de probes inválidos são históricas e não são PASS: um preço fake sem marcador monetário e um timeout incompatível com lease foram corrigidos somente no probe, sem modificar produto ou expectativas do contrato.

Estado preliminar: implementação pronta para avaliação consolidada. `done` requer relatório completo por item, regressão integrada e resolução de pendências de cobertura; nenhuma aprovação genérica de serviço ou observação visual é usada como prova de toda a cadeia de jobs.

## Complemento de validação local

As combinações faltantes foram executadas:4 barreiras individuais,2 disputas simultâneas,1 revisão ultrapassada/GPU ocupada e3 variantes de tempo/edição/reinício passaram. A jornada mista preenfileirou quatro jobs reais antes da pausa pelo navegador; consumidores não iniciaram novas operações nem consumiram attempts. A mensagem incerta conservou ref/body após stop/init; ligar após49h conservou o envio anterior incerto, recusou primeira intenção vencida e confirmou somente oferta recente. Os29 itens observáveis estão PASS; done/clean aguarda a regressão integrada do coordenador.
