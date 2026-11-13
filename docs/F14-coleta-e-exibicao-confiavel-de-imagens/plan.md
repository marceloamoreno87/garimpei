# Plano de implementação — F14

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-13T12-24-34Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

Especificação: [spec.md](spec.md). Aceite: [contract.md](contract.md). Dependências: F04, F08 e F12 avaliadas; F14 continua `pending`, prioridade 1 e onda 11. Este plano não autoriza implementação de outras features, execução paralela, commit, push, deploy ou envio ao WhatsApp.

## Pré-requisitos

- Python 3.13/Django 5.2/Procrastinate existentes, uv e lock do backend; acrescentar e fixar Pillow durante a implementação.
- Ambiente isolado por F02, PostgreSQL, scripts `init.sh`/`stop.sh` e raiz privada de mídia por instância. Serviços reais só serão iniciados quando necessários à implementação/verificação.
- Perfil Facebook dedicado já autorizado para a prova de leitura real, com posse exclusiva e sem copiar credenciais para o laboratório.
- Orçamento de armazenamento informado por configuração para habilitar aquisição na instalação real. O laboratório usa orçamento sintético; ausência do valor real não impede gerar estes documentos.

## Fase 1 — Fonte e fronteiras de evidência

**1. Extração verificável** — Identificar no payload do detalhe a principal, adicionais e variantes de resolução pertencentes ao item correto. Documentar campos, identidade, limitações e casos de acesso real sem expor URLs assinadas ou sessão, conforme spec §2/§7.

**2. Massa e regras de mídia** — Entregar os cenários sintéticos, políticas, estados e protocolos definidos na spec §3. Reaproveitar as factories e convenções existentes, separando ausência comprovada de informação desconhecida.

**Verificação da fase:** corpus reproduzível, comparação entre itens corretos e recomendações, regressões das lacunas identificadas e registro inicial da prova de fonte. Fonte inacessível mantém a prova externa pendente, sem ser substituída por fixture.

## Fase 2 — Persistência e processamento

**3. Adoção e preservação** — Acrescentar registros de captura, associação, versão, tarefa e referência com migração aditiva. Conservar observações, escolhas e alertas existentes, inicializando a proteção dos anúncios legados conforme spec §6.

**4. Obtenção e derivação independentes** — Entregar transferência limitada, armazenamento atômico, reserva de orçamento e miniaturas separadas. Garantir que download ou derivação interrompidos conservem as cópias válidas e permitam recuperação, conforme spec §3.

**5. Worker, renovação e estoque acompanhado** — Integrar tarefas e reconciliação à operação persistente, preservando filas existentes e exclusividade do perfil. Incorporar retomada e recuperação de ofertas já armazenadas sem recriar descoberta ou autorizar mensagem por mudança de foto.

**Verificação da fase:** itens Worker do contrato; cenários de limite, rede, quota concorrente, queda e atraso, com comparação de hashes/arquivos e avanço de uma unidade saudável.

## Fase 3 — Consulta, retenção e interface

**6. Versões e proteção para análise** — Entregar a consulta pública de mídia e as referências duráveis para o consumidor futuro F15, com limpeza condicionada às duas proteções. Manter registros de remoção e recuperação idempotente de falhas da limpeza, conforme spec §3/§5.

**7. Apresentação vinculada à observação** — Integrar galeria e versões fixadas à publicação F08 e servir bytes pelas rotas locais. Adaptar lista, detalhes, ampliação e recuperação ao design existente, preservando leitura, recorte e atualização mediante clique.

**Verificação da fase:** itens Service/HTTP/UI do contrato; comparação entre revisões, pin concorrente à limpeza, estados de imagem e jornadas com teclado e larguras estreita/ampla.

## Fase 4 — Evidência e entrega para avaliação

**8. Validação integrada e operação** — Consolidar o percurso controlado e a prova real de cópias na melhor qualidade obtida, com limites e pendências explícitos. Documentar configuração do orçamento, preparo do laboratório, retenção e retomada em `operations.md`, além das evidências do contrato e do relatório de implementação.

**Verificação da fase:** executar todos os Quality gates do contrato e seus itens E2E, incluindo regressões das dependências, navegador por `playwright-cli` e avaliação visual com `frontend-ui-design`. Falha ou pré-requisito externo ausente permanece pendente/reprovado conforme evidência; este plano não transforma documentação em aceite da implementação.

A ordem das fases é sequencial. Alterações em coletor, `main.py`, migrations, worker e projeções devem ser coordenadas com F13/F16/F17/F19/F20 quando outras sessões trabalharem nesses arquivos; preservar suas mudanças e adaptar a ponta atual. Encerrar somente os processos/recursos próprios de avaliação. Atualizar progresso de execução apenas pelo fluxo autorizado de implementação/avaliação, nunca para `done` por existir esta especificação.
