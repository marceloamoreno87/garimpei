# F22 — Verificação de navegador e avaliação visual da onda 13

Avaliador: coordenador Codex, usando `playwright-cli` e `frontend-ui-design`. Ambiente descartável próprio `eval_f04_64fdcc933c`, origem local porta21094, PostgreSQL/web/worker reais e fonte fake da factory F08. Não houve Facebook, GPU ou WhatsApp real nesta verificação. Estados de operação foram preparados pela porta de admissão/complete; não representam por si só drenagem de I/O real. Suíte de Worker/E2E é responsabilidade da avaliação F22.

## Evidências e resultado observado

Resultados estruturados e hashes exatos das superfícies verificadas em [browser-observations-wave13.json](browser-observations-wave13.json). Desktop1440×1000 e mobile390×844, capturas examinadas pelo avaliador.

- UI-CONTROLE-01: ligado, desligado, desligando com permissão sintética ativa, término indeterminado e worker sem heartbeat distinguíveis; ação por teclado comprovada após dois polls reais. Nenhum estado de término foi inferido só da ausência de worker.
- UI-CONTROLE-02: durante pausa, consulta/filtro Sony/cameras, página2 e detalhe Câmera21 preservaram `aba/q/categoria/pagina/versao`; scrollWidth390=viewport390. Stop/init normal conservou pausa e versão da oferta.
- UI-CONTROLE-03: servidor Gunicorn isolado com falha da porta de comando retornou503, manteve o estado ligado no banco e ofereceu recuperação, sem confirmação otimista. Não é uma injeção de falha física de commit.
- HTTP: habilitação303; replay303 sem incrementar revisão; reuso de UUID com payload diferente409; entrada inválida400; CSRF ausente403; GET em rota de mutação405/AllowPOST; status `no-store`. Duas abas com revisão4: comando recente publicou5 e aba antiga recebeu409, sem sobrescrever.
- Falha de leitura: tela completa mostra indisponibilidade e status503/no-store. Poll de erro após a correção conserva um painel e um main; segundo poll continua funcionando e recuperação acontece automaticamente após restaurar a resposta normal.

## Achados corrigidos nesta execução

1. Poll a cada3s retirava o foco do botão: antes BUTTON, depois BODY. O novo listener conserva a ação focada; recheck em duas respostas reais e tecla Enter passou.
2. Status com falha retornava documento HTML completo, inserido dentro do painel pelo tratamento global HTMX. Havia dois main, navegação duplicada e nenhum `#robot-control`, interrompendo os polls. A resposta de status agora é fragmento503 preservando painel/poll/recuperação. Recheck: controls1/mains1 e recuperação automática.

`ui-poll-error-before-fix-wave13.png` e as capturas iniciais ficam preservadas como evidência da falha; não são a aparência final. Preparações do probe com URL de filtro inválida e request relativa foram corrigidas no probe, sem mudança de produto nem uso como PASS.

## Avaliação visual

| Dimensão | Nota | Evidência |
|---|---|---|
| Design |7| Papel claro e tinta verde, tipografia/hierarquia coerentes com Mineral; controle agrupado com espaço próprio e ação explícita. |
| Originalidade |6| Reutiliza o vocabulário editorial do produto; controle textual convencional, sem nova assinatura visual. |
| Acabamento |7| Sem rolagem horizontal a390px; botão mobile tem altura44,39px; mensagens e parágrafos longos exigem rolagem vertical, sem sobreposição. |
| Funcionalidade |8| Intenção e execução separadas, ação explícita, conflito entre abas e erro recuperável; teclado estável após correção. |

Média ponderada: `(7×2+6×2+7+8)/6 = 6,83/10`. Nenhuma dimensão≤3. Não há achado visual crítico pendente nas superfícies observadas. O aviso de Facebook desconectado pertence ao laboratório de fonte fake; não comprova sessão real. Respostas503 injetadas e favicon404 explicam erros de rede observados, sem erro JavaScript não tratado identificado.

Esta avaliação fornece evidência UI/HTTP ao avaliador canônico; não declara a feature `done` nem substitui gates, migração, concorrência, ou Worker/E2E completos.
