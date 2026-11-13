# Plano de implementação — F13

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-12T19-32-55Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

Pré-requisitos: [spec](spec.md), [contrato](contract.md), F03/F04/F11/F12 disponíveis, stack Python/Django aprovada, uv e dependências congeladas, PostgreSQL/worker pelos scripts existentes, catálogo de navegação e ambiente de avaliação próprios a produzir conforme contrato. A fase real depende de acesso verificado e exclusivo ao Marketplace. Esta entrega é documental; implementação não começou.

## Fase 1 — Baseline e regras

**1. Caracterizar a navegação existente.** Registrar percurso, limites e fronteiras persistentes atuais para separar a extensão F13 das capacidades já existentes. Verificar propriedade do perfil e do ambiente, sem iniciar coleta em recurso concorrente.

**2. Formalizar política e catálogo.** Materializar distribuição entre frentes, aliases conservadores, relações entre nichos e parâmetros operacionais conforme spec §3. Preservar cadastro livre e política vigente de alertas.

Verificação da fase: regressões significativas das regras e baseline documentado; confirmar casos positivos e negativos de aliases e relações.

## Fase 2 — Persistência e continuidade

**3. Preparar planejamento e checkpoints.** Acrescentar armazenamento aditivo para unidades, posse, confirmações e sugestões separadas. Manter histórico e caminho único de publicação.

**4. Integrar turnos e retomada ao coletor.** Devolver controle entre unidades, preservar contexto e reconstruir consultas quando a fonte invalidar cursores. Disponibilizar a fronteira de pesquisa complementar sem antecipar F18.

Verificação da fase: PostgreSQL real isolado, interrupções, resultados atrasados, alternância entre interesses e publicação antes do fim; medição confirma ou exige revisão dos limites antes da avaliação.

## Fase 3 — Sugestões e experiência

**5. Ativar exploração em tempo livre.** Aplicar relações verificáveis e orçamento próprio sem disputar trabalho ativo ou publicar sugestões como ofertas monitoradas. Adoção continua sendo gravação explícita de configuração.

**6. Expor progresso e recuperação.** Integrar acompanhamento, sugestões e prévia de configuração ao design existente. Preservar leitura estável, filtros, acessibilidade e tratamento central de erros.

Verificação da fase: jornadas HTTP e via playwright-cli, falha de atualização/gravação, sugestão ignorada e adoção confirmada; avaliação visual conforme frontend-ui-design.

## Fase 4 — Evidências e entrega

**7. Conferir operação integrada.** Exercitar ambiente controlado, fonte real autorizada e retomada com medições sanitizadas. Documentar preparo, diagnóstico e recuperação em operations.md.

**8. Consolidar validação e relatório.** Executar gates, suíte, checks e build indicados na spec, ligando evidências aos itens do contrato. Manter implementação/progresso pendentes até avaliação completa; commit, push, PR e deploy dependem de autorização própria.

Verificação da fase: todos os itens do contrato e gates aplicáveis têm resultado e evidência; bloqueio externo permanece pendente, sem marcar done.
