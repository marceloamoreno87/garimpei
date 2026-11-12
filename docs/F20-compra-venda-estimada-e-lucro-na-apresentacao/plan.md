# Plano de implementação — F20

Pré-requisitos: [spec](spec.md), [contrato](contract.md), F07/F08/F09/F12 avaliadas e Python/Django, uv, Docker/PostgreSQL, worker e ferramentas do harness atuais. Confirmar arquivos/lock no início; não atualizar dependências para uma alteração de apresentação. Preparar instância `eval` própria com credenciais privadas e fonte/canal sintéticos pelas factories existentes. Executar `./scripts/init.sh --disposable` antes do trabalho que precise da aplicação; encerrar somente os processos próprios ao finalizar.

A F20 permanece `pending` até o início explícito da implementação. Este plano não inicia outras features, deploy, commit ou envio real. Coordenar arquivos compartilhados de exploração/alerta com F14/F16/F17/F18; a onda 11 não autoriza alteração simultânea desses arquivos.

## Fase 1 — Cenário reproduzível e compatibilidade

**1. Estado de referência** — Registrar as superfícies e publicações correntes e preparar o cenário isolado da spec §7, incluindo mensagens legadas e novas intenções ainda não autorizadas. Documentar criação, controles, verificações e encerramento em `operations.md` da F20.

**2. Persistência aditiva** — Estender a intenção com o snapshot financeiro e o formato do corpo, preservando as referências e os registros existentes. Aplicar a estratégia de migração e compatibilidade da spec §6.

Verificação da fase: ambiente próprio pronto; fixture/lab reproduzíveis; migration aplicada sem alterar corpos, tentativas ou recibos; schema e migrations correspondem.

## Fase 2 — Composição e mensagens

**3. Snapshot financeiro completo** — Vincular os componentes e referências da composição autoritativa ao evento e à intenção. Rejeitar dados incompatíveis e encaminhar falta de dados pelo fluxo de espera vigente, conforme spec §§5–6.

**4. Autorização e corpo imutáveis** — Gerar o novo trio na primeira autorização e manter corpo e snapshot fixos nas retomadas. Preservar textos legados e o vínculo de reconciliação, sem introduzir reenvio pela adoção do formato.

Verificação da fase: itens WRK-MENSAGEM e E2E-MENSAGEM; casos de arredondamento, mudança de taxa, corpo legado, queda e concorrência; comparação do corpo capturado pelo fake WAHA com o snapshot autorizado.

## Fase 3 — Interface financeira

**5. Trio nas ofertas** — Integrar a apresentação compartilhada aos cards e detalhes, com lucro em maior destaque e componentes ausentes identificados. Conservar a composição da revisão selecionada, os comparáveis e a explicação da taxa.

**6. Configuração e textos** — Remover campos e explicações financeiras de logística dos fluxos ativos, preservando CEP, interesses e taxa. Manter evidências originais e estruturas históricas necessárias à compatibilidade.

**7. Atualização e recuperação** — Preservar recorte, revisão e leitura anterior durante atualização ou falha. Aplicar novas composições somente pelo fluxo explícito existente e oferecer recuperação no mesmo contexto.

Verificação da fase: itens API-FINANCEIRO, UI-FINANCEIRO, UI-CONFIGURACAO e UI-ATUALIZACAO; navegação por teclado, sinal/indisponibilidade, desktop, largura estreita e zoom; páginas 20/20/2 e atualização mediante clique.

## Fase 4 — Integração e evidências

**8. Preservação ponta a ponta** — Consolidar o fluxo de publicação, leitura e mensagem para que cada superfície conserve sua composição aplicável. Demonstrar a integração F07/F08/F09/F12 sem depender de F16 ou de canal real.

**9. Fechamento da entrega** — Reunir evidências por item, instruções reproduzíveis e riscos materiais em `impl-report.md`, com os artefatos junto da feature. Atualizar o progresso apenas pelo workflow de implementação/avaliação autorizado.

Verificação final: executar todos os comandos de Quality gates do contrato e registrar códigos de saída; conferir Coverage Manifest completo e avaliação visual. Qualquer gate falho ou verificação necessária ausente conserva a pendência. Prova real de WhatsApp só ocorre após autorização específica; validação sintética não é prova de entrega real.
