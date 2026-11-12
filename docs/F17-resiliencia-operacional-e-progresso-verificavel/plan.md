# Plano — F17 Resiliência operacional e progresso verificável

**Pré-requisitos:** dependências F02/F04/F06/F08/F09/F10/F12 avaliadas; Python 3.13 e dependências de `uv.lock`, PostgreSQL 17/Docker e scripts do projeto; leitura de `spec.md` e `contract.md`. Trabalho de aplicação começa com `./scripts/init.sh` em instância `eval` própria. Não reutilizar banco, perfil ou canal reais. A especificação não autoriza commit, push, merge ou deploy.

## Fase 1 — Baseline e ambiente controlado

**1. Laboratório e calibração** — Preparar carga saudável, recortes, pontos de falha e recursos descartáveis conforme os pré-requisitos do contrato. Medir os estágios existentes e confrontar o perfil inicial da spec antes de habilitar as novas políticas; registrar divergências sem fabricar medições para etapas ainda inexistentes.

**Verificação da fase:** inventário de propriedade/cleanup, manifesto da fixture, baseline saudável e adverso com duração/filas/bytes. Perfil incompatível exige revisão documental antes da adoção; relatório antigo de F12 é referência, não medição da F17.

**Gate para as fases seguintes:** regenerar spec/plano/contrato com os limites medidos e a evidência do ensaio; só então retirar a condição preliminar do contrato. Os estágios novos ainda inexistentes exigem medição do primeiro incremento em laboratório antes de habilitação; valores escolhidos não podem ser apresentados como observações empíricas.

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
