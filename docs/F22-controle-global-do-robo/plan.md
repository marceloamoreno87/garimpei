# Plano — F22 Controle global de ligar e desligar o robô

## Pré-requisitos

- Dependências F02/F03/F08/F13/F14/F15/F16/F19 avaliadas e disponíveis na versão integrada; verificar o progresso antes de iniciar, pois F14/F15 ainda não estavam `done` durante esta especificação.
- Python/Django/PostgreSQL/Procrastinate e versões travadas da stack atual; ambiente descartável próprio iniciado por `./scripts/init.sh` quando houver execução de aplicação, com limpeza restrita a essa instância.
- Ler `spec.md`, `contract.md`, PRD e clean-arch. Preparar as factories, relógio, barreiras e servidores locais descritos no contrato, sem usar fonte ou grupo real.
- Coordenar alterações em `main.py`, `runworker.py`, autorização F16, inferência F19 e fronteiras F13/F14/F15; preservar mudanças dos demais trabalhos. F17/F18 não são parte deste plano.

## Fase 1 — Fronteiras e estado persistente

**1. Inventário do trabalho automatizado** — Identificar cada ponto que inicia página, detalhe, transferência, avaliação, parte de inferência e envio na versão integrada. Definir a unidade finita de drenagem e as operações de integridade que permanecem disponíveis, conforme spec §3.

**2. Controle e adoção** — Acrescentar a intenção global, os comandos idempotentes e as autorizações duráveis. Migrar preservando o comportamento anterior quando não houver escolha global e sem tocar preferências específicas ou histórico.

**Verificação:** itens de adoção/admissão do contrato; migrations em base nova e preenchida e inventário completo das fronteiras. Falta de dependência ou worker antigo sem barreira impede declarar a função disponível.

## Fase 2 — Barreira operacional e drenagem

**3. Admissão por unidade** — Integrar o controle às tarefas agendadas e já enfileiradas, incluindo execução solicitada manualmente. Conservar trabalho negado pela pausa, sem consumir tentativas nem iniciar a próxima unidade do mesmo job.

**4. Drenagem e mensageria** — Permitir conclusão/checkpoint de unidades já autorizadas, identificar término indeterminado e manter a reconciliação sem novo envio. Aplicar uma ordem de locks única às autorizações e finalizações.

**Verificação:** concorrência, pausa nos dois lados da autorização, jobs antigos e falhas de leitura; comprovar todos os estágios sem usar canal real.

## Fase 3 — Retomada e recuperação

**5. Retomada condicionada** — Reconciliar trabalho válido ao ligar, respeitando relógio, revisão, recurso exclusivo e todas as pausas/barreiras individuais. Preservar os vínculos e as mensagens que já estavam autorizadas.

**Verificação:** reinício mantendo a pausa, entradas vencidas/ultrapassadas e controles individuais preservados; conferir que recibos e marcos não são zerados pela retomada.

## Fase 4 — Interface e contrato público

**6. Comandos e apresentação** — Oferecer ligar/desligar explícitos em Acompanhamento, com revisão, replay seguro e estado solicitado versus efetivo. Exibir resumo nas ofertas sem alterar sua revisão ou bloquear a consulta.

**Verificação:** itens HTTP/UI, duas abas, CSRF, erro de gravação e acessibilidade no navegador; confirmar que leitura não altera nem inicia trabalho.

## Fase 5 — Validação integrada e entrega

**7. Percurso e evidências** — Consolidar o percurso de atividade, pausa, drenagem, reinício e retomada, com cenários de envio e inferência incertos. Documentar operação e resultados por item junto da feature.

**Verificação:** executar todos os quality gates do contrato e conferir o Coverage Manifest contra os oito aceites F22. Manter pendências explícitas; a etapa só recebe `done` após avaliação completa. Este plano não autoriza commit, push, merge, deploy ou execução de outra feature.
