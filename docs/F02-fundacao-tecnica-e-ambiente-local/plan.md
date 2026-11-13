# Plano de execução — F02 Fundação técnica e ambiente local

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-10T21-15-47Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

Data: 2026-11-10. Complexidade alta. Dependência: **F01**, ainda com decisão manual pendente. Onda 2, execução **sequencial**, por alterar arquivos compartilhados. Fontes: [spec](spec.md), [contrato](contract.md), [PRD](../PRD.md), [stack](../stack.md) e [passagem F01](../F01-discovery-e-viabilidade-de-integracoes/environment.md).

Este plano descreve implementação futura. O pedido atual produz somente spec/plano/contrato, sem instalar, gerar scaffold, iniciar serviços, alterar progresso ou realizar commit/push/PR. A especificação não libera a dependência F01.

## Pré-requisitos

| Entrada | Preparação | Verificação / consequência da ausência |
|---|---|---|
| F01 encerrada e fontes canônicas | Registrar decisão explícita e avaliação completa; revisar consequências para a fundação. | Progresso F01 done e relatório limpo atual, sem inferir escolha da sugestão OLX. Ausência bloqueia iniciar implementação F02. |
| Checkout e isolamento | Preservar trabalho atual; escolher checkout apropriado à execução autorizada, reservar temporário e snapshot de arquivos. | Baseline e propriedade; sem commit base, hashes/cópias também cobrem arquivos não rastreados. Não criar commit automaticamente. |
| Ferramentas do ambiente | Disponibilizar Git, Bash, Node, uv/Python 3.13, Docker/Compose e ferramentas de inspeção locais. | Versões reais e Docker acessível; falta é pré-requisito pendente, sem instalação implícita de sistema. |
| Dependências/imagens | Resolver patches mantidos, travar lock e registrar origem/digests antes da cópia do scaffold. | `versions.md` e PoC da combinação; série/engine incompatível exige decisão técnica explícita. |
| Configuração privada | Preparar segredos e identidade conforme spec §3; avaliação usa instância descartável exclusiva. | Presença/formato verificados sem valores; env inválido impede início. |
| Dados de prova | Criar factories, marcadores e fixtures técnicas no escopo F02. | Conferir formato e propriedade pelo contrato; sem sessão pessoal ou seed de negócio. |

## Fase 1 — resolver compatibilidade e preparar integração

**1. Matriz e prova isolada** — Registrar versões exatas, origem e artefatos da matriz da spec §3; validar Django/PostgreSQL/Procrastinate e a imagem/engine WAHA em ambiente temporário próprio. Consolidar incompatibilidades antes de depender delas no scaffold.

**2. Inventário de integração** — Gerar a base Django em temporário e selecionar apenas os arquivos necessários à estrutura da spec §4. Registrar arquivos aceitos/rejeitados e mesclas previstas, preservando instruções, harness e trabalho existente.

**Verificação da fase:** bootstrap em banco vazio, migrations da fila, consumo de probe e rollback transacional reais; manifesto/digest/arquitetura WAHA, serviço saudável sem pareamento e nenhuma imagem móvel aceita como fixada. Conferir snapshot e `versions.md`; incompatibilidade impede avançar para integração. Não usar o gerador TypeScript para criar a base Django.

## Fase 2 — estabelecer base Python e persistência

**3. Estrutura e bootstrap** — Integrar configuração central, composição explícita, entradas web/worker, contratos de prontidão e base de templates/estáticos conforme spec §§2–5. Preparar documentação de instalação e grupos de dependências travados, sem antecipar módulos/telas de negócio.

**4. Schema e consumo técnico** — Preparar migrations e modelos técnicos, registrar os handlers injetados e tornar a fila persistente verificável pelos probes da spec §6. Preservar execução independente do web e distinguir idempotência técnica local de entrega externa.

**Verificação da fase:** import de domain/usecase sem Django/I/O, registro ORM/migrations sem consultas precoces, aplicação de schema vazio e repetida, tarefa consumida/pendente recuperável e commit/rollback com conexões independentes. Validar endpoints técnicos e renderização/asset local. Itens API-SAUDE-01–04, CLI-MIGRACAO-01–03, WRK-FILA-01–03 e E2E-TRANSACAO-01–02.

## Fase 3 — adaptar operação e preservar recursos

**5. Lifecycle e isolamento** — Adaptar scripts canônicos e Compose ao início/parada de Python, identidade estável, propriedade de processos/recursos e prontidão da spec §2. Preparar diagnósticos, rollback da tentativa malsucedida e preservação de dados/sessão, com limpeza apenas descartável autorizada.

**Verificação da fase:** início frio e idempotente, falhas de configuração/serviço/porta, dois ambientes simultâneos, PID reutilizado/alheio, parada repetida e restauração por reinício. Verificar bind local, banco `garimpei_`, volumes/marcadores e logs sem canários. Itens CLI-INICIO-01–04, CLI-PARADA-01–03 e E2E-REPRODUCAO/ISOLAMENTO/FALHA/PRESERVACAO/PROPRIEDADE/LIMPEZA/LOGS.

## Fase 4 — tornar a qualidade executável

**6. Validadores e regressões** — Implementar a entrada canônica e os seis grupos Python da spec §7, com escopos reais, registros do framework e exceções estreitas. Adaptar as verificações do harness e manter cenários negativos que comprovem a rejeição de violações representativas, sem enfraquecer o contrato.

**Verificação da fase:** seis grupos executados e aprovados na árvore válida; em cópias temporárias, cada gate rejeita sua violação e informa o grupo correto. Testes de código/dependência não utilizados precisam falhar por esses motivos, sem aprovação por exclusão ampla. Ferramenta/source ausente retorna erro real, sem download ou fallback TypeScript. Itens CLI-QUALIDADE-01–03 e E2E-COMPOSICAO-01.

## Fase 5 — consolidar evidências e passagem

**7. Operação reproduzível** — Consolidar `versions.md`, `environment.md` e `operations.md` com preparação, comandos reais, limitações de capacidade e procedimentos de diagnóstico/recuperação. Distinguir serviço WAHA de sessão/envio e instruções de desenvolvimento das de limpeza descartável.

**8. Revisão final da fundação** — Confrontar todos os itens com o estado instalado, registrar comandos/códigos e preservar os artefatos anteriores no relatório de implementação. Entregar a base para avaliação integral; done depende do veredito do contrato, não deste plano ou de gates parciais.

**Verificação da fase:** todos os comandos complementares e itens executados, links/origens/locks consistentes e diff/hash dos arquivos preservados. Sem pendências silenciosas de ferramentas, ambiente, Docker ou provas práticas obrigatórias. Itens DOC-PREPARACAO-01–02 e todos os ACs; ambientes de prova próprios encerrados preservando dados quando aplicável.

## Validação e término

As fases têm dependência sequencial; não se inicia uma frente paralela de fundação. Comandos e critérios completos estão na spec §7 e no contrato; não duplicar configurações de gates em runners divergentes.

- Durante esta especificação: validar cobertura literal dos quatro ACs, referências de IDs, links locais, coerência dos comandos e preservação dos arquivos existentes/progresso. Não rodar aplicação inexistente para simular aprovação.
- Durante implementação/avaliação: `node scripts/run-gates.mjs`, testes Python/PostgreSQL/fila, checks/migrations/estáticos/build, lifecycle real e regressões do harness. Registrar bloqueios e códigos, sem skip de cenário obrigatório.
- Sem F01 concluída ou incompatibilidade local resolvida: manter implementação bloqueada e documentação revisável; não trocar fonte, stack ou escopo implicitamente.
- Sem autorização de Git/deploy: nenhum commit, push, PR, merge ou deploy. Preparar relatório/evidências é suficiente para revisar a entrega.
