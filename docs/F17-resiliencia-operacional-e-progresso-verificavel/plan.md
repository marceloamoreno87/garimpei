# Plano — F17 Resiliência operacional e progresso verificável

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-13T03-39-54Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

**Pré-requisitos:** dependências F02/F04/F06/F08/F09/F10/F12 avaliadas; Python 3.13 e dependências de `uv.lock`, PostgreSQL 17/Docker e scripts do projeto; leitura de `spec.md` e `contract.md`. Trabalho de aplicação começa com `./scripts/init.sh` em instância `eval` própria. Não reutilizar banco, perfil ou canal reais. A especificação não autoriza commit, push, merge ou deploy.

## Fase 1 — Baseline e ambiente controlado

**1. Laboratório e calibração** — Preparar carga saudável, recortes, pontos de falha e recursos descartáveis conforme os pré-requisitos do contrato. Medir os estágios existentes e confrontar o perfil inicial da spec antes de habilitar as novas políticas; registrar divergências sem fabricar medições para etapas ainda inexistentes.

**Verificação da fase:** inventário de propriedade/cleanup, manifesto da fixture, baseline saudável e adverso com duração/filas/bytes. Perfil incompatível exige revisão documental antes da adoção; relatório antigo de F12 é referência, não medição da F17.

**Gate para as fases seguintes:** regenerar spec/plano/contrato com os limites medidos e a evidência do ensaio; só então retirar a condição preliminar do contrato. Os estágios novos ainda inexistentes exigem medição do primeiro incremento em laboratório antes de habilitação; valores escolhidos não podem ser apresentados como observações empíricas.

**Execução do gate — 2026-11-13 UTC:** concluído no recorte controlado; spec/plano/contrato foram regenerados com [calibration-confirmed-2026-11-13T03-08-37Z.json](evidence/calibration-confirmed-2026-11-13T03-08-37Z.json). Os valores permaneceram iguais e a habilitação real continua desligada. Fases seguintes e avaliação integral permanecem obrigatórias.

## Fase 2 — Progresso durável e integridade

**2. Estado operacional** — Introduzir políticas e persistência de progresso, orçamento e checkpoint, ligadas às fronteiras confirmadas já existentes. Migrar dados preservando identidades, revisões e recibos sem transformar histórico não medido em avanço novo.

**3. Funil consistente** — Publicar leitura de etapas e contagens com definições, recorte e horário comuns. Manter ausência de etapas futuras explícita e distinguir elegibilidade de aceitação pelo servidor de mensagens.

**Verificação da fase:** gates Python, contagens do conjunto controlado, reexecução idêntica, escrita concorrente e resultado fora de ordem; nenhuma mutação financeira/de classificação por consulta.

## Fase 3 — Isolamento e recuperação limitada

**4. Trabalho independente** — Reservar capacidade de execução por grupo, preservar uso exclusivo do perfil e tornar independentes os reconciliadores. Aplicar orçamento limitado, contrapressão e retomada a partir do checkpoint confirmado, respeitando os prazos da fonte.

**5. Continuidade após queda** — Integrar gerações/posses e as proteções de publicação/envio ao novo diagnóstico. Conservar transmissão incerta em reconciliação e impedir que reinício ou retentativa recriem primeiro alerta.

**Verificação da fase:** controle saudável versus item/fonte/canal lentos; fila no teto; suspensão e retomada explícita; quedas nos pontos de commit/publicação/envio e migração de dados existentes. Inspecionar encerramento dos processos próprios.

## Fase 4 — Cópias e recuperação de dados

**6. Backup e exportação** — Implementar cópia por schema versionado, agendamento de 24 horas, retenção de sete cópias e exportação da cópia selecionada. Aplicar integridade, privacidade, limites de espaço e publicação atômica, preservando cópias anteriores durante falha.

**7. Restauração isolada** — Implementar validação de pacote, importação em destino descartável e barreira durável de despacho. Demonstrar reconciliação do intervalo não coberto e separar recuperação dos dados de recuperação do acesso.

**Verificação da fase:** agendamento atrasado e em dia, duas inicializações concorrentes, oitava cópia, interrupção/armazenamento cheio, exportação exata, pacote inválido e cópia anterior ao último envio. Restauração bem-sucedida e cópia apenas criada devem produzir estados diferentes.

## Fase 5 — Interface operacional e recuperação da leitura

**8. Diagnóstico e ações** — Integrar etapas, funil, motivos e backups ao Acompanhamento existente, com ações de retomada/exportação validadas. Preservar a jornada da exploração e a leitura já carregada em falhas, mantendo atualização dos dados mediante clique.

**Verificação da fase:** jornadas de navegador desktop/janela estreita, teclado, timeout offline/503, primeira abertura e retry na mesma rota; avaliação visual conforme `frontend-ui-design`. Repetição não reordena a lista sem aplicação explícita.

## Fase 6 — Evidência integrada

**9. Validação de ponta a ponta** — Executar percurso com dados suficientes e a matriz adversa do contrato em recursos próprios. Consolidar medições e resultados de restauração, privacidade e deduplicação, incluindo limitações que exigem intervenção.

**10. Entrega verificável** — Atualizar os guias operacionais e produzir `impl-report.md` com comandos, perfil confirmado, evidências por item e recursos encerrados. Encaminhar avaliação do contrato; status de implementação só muda de acordo com o ciclo autorizado e seus resultados.

**Verificação final:** seis gates Python, suíte relevante completa, Django/migrations, harness quando alterado e itens do contrato. Arquivar logs sanitizados; falhas, medições ausentes ou item não executado permanecem pendentes, sem declarar F17 concluída.


## Evidência histórica de calibração inicial — 2026-11-12

**Estado histórico, superado pela calibração de 2026-11-13 UTC:** o parágrafo seguinte preserva a situação daquele ensaio e não define o estado canônico atual.

[calibration-initial.json](evidence/calibration-initial.json) registra cinco controles e cinco timeouts por adaptador com prazos operacionais (fonte20s, valoração30s, canal10s), além de cinco percursos completos com PostgreSQL e recibo fake F16 em19,30–20,02s incluindo startup. Estes resultados confirmam as fronteiras existentes. O primeiro incremento de manutenção, restauração, isolamento e a integração de mídia ainda requerem ensaio; o contrato continua preliminar e a habilitação real permanece desativada. Nenhum limite foi ampliado e nenhum gate foi dispensado.


## Perfil calibrado — 2026-11-13 UTC

O gate documental da fase 1 foi satisfeito no recorte controlado descrito em [calibration-confirmed-2026-11-13T03-08-37Z.json](evidence/calibration-confirmed-2026-11-13T03-08-37Z.json). O perfil/hash **071796693048f99049727b4a2f0c2a97809c67ee5b1378ba1fc7937977355423** conserva todos os limites e políticas já aprovados: nenhum prazo, orçamento, fila ou armazenamento foi ampliado. Isto confirma o perfil técnico no laboratório; não aprova automaticamente os 58 itens nem habilita a instalação real.

| Evidência atual | Resultado observado |
|---|---|
| Fonte/valoração/canal | 30 observações: cinco controles e cinco timeouts por adaptador, com prazos operacionais 20/30/10 s |
| Falhas de rede/arquivo/fila | 35 observações pareadas; prazos de 1 s são injeção somente em eval, separados dos prazos operacionais |
| Backup/exportação/restauração/reconciliação | Cinco controles completos; backup 0,516–0,546 s, exportação 0,376–0,411 s, restauração 0,594–0,674 s, verificação 0,351–0,408 s; mídia original protegida e zero POST duplicado |
| Quedas de processo | 25 pares controle/falha: cinco por fronteira antes/depois de autorização, após POST, após confirmação e após lote confirmado/antes da publicação seguinte |
| Carga mista | Cinco pares com duas ofertas: enquanto valoração e POST estavam retidos, runtime/coleta/backup avançaram em 6,790–6,880 s; controles 3,337–3,629 s |
| Armazenamento | Máximo lógico amostrado de dados 16355196 bytes; backups/exportações/temporários 203420 bytes; mínimo livre 8512139264 bytes |
| Revisões | Hashes de runtime, testes e uv.lock idênticos em todos os pares e na calibração canônica; versões completas no JSON |

Os picos são máximos **amostrados a cada 0,1 s**, não ocupação física contínua. A origem teve 2.908 amostras e zero erro; o destino é fechado intencionalmente entre restaurações e os períodos sem conexão estão contados, sem preencher zeros. As consultas por restauração corroboram os tamanhos disponíveis. A idade máxima de 342 s inclui a unidade de recuperação deliberadamente pausada, não latência de trabalho saudável. Os limiares de 180 s/5 s/três falhas/1.000 unidades continuam escolhas de engenharia, exercitadas nos testes de fronteira, sem promessa de throughput ou RPO/RTO. Faltas de espaço são injetadas em eval; não foi necessário preencher o disco do operador.

A confirmação é limitada à carga sintética rastreável, com PostgreSQL/web/workers reais, fonte/canal loopback e arquivos próprios. Os recursos da calibração e dos pares foram encerrados conforme os inventários. A evidência anterior acima permanece histórica. A avaliação integral e as correções de CLI/HTTP identificadas continuam obrigatórias para `done`; `operational_enablement=false` foi conservado.
