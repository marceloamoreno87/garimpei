# Plano de implementação — F21 Alertas ouro

## Pré-requisitos

- Python 3.13, Django 5.2, PostgreSQL, Procrastinate e dependências de `apps/backend/uv.lock`, com ambiente próprio preparado pelos scripts F02.
- F06/F07/F15/F16/F18/F20 implementadas e avaliadas, incluindo as evidências de fotos/análise e identificação que sustentam a qualificação. Conferir progresso/relatórios antes de executar; F15/F18 estavam pendentes de conclusão na especificação.
- Ler `spec.md`, `contract.md`, clean-arch e os documentos das dependências. Coordenar alterações com trabalho ativo em condição, identidade e alertas; a onda não autoriza execução paralela.
- Arquivo privado `GARIMPEI_ENV_FILE` e recursos eval próprios; fakes e corpus da spec §7 produzidos na etapa inicial. Perfis, banco e canal reais não são recursos de falha injetada.

## Fase 1 — Reproduzir a fronteira atual e preparar dados

**1. Corpus e ambiente de qualificação** — Materializar os casos e o lab reproduzível da spec §7, usando as factories e fronteiras existentes. Registrar a distinção entre controle sintético e corpus real, além do inventário de intenções/recibos legado.

**Verificação da fase:** o lab prepara cada handle, `status` confere campos/revisões/valores e o canal fake mostra contador inicial conhecido; nenhuma dependência ausente é declarada satisfeita.

## Fase 2 — Qualificar evidências e persistir decisões

**2. Política e snapshot rastreável** — Criar a qualificação tipada com condição, identidade normalizada, amostra histórica e composição aplicáveis, reutilizando os responsáveis por identificação, mediana e lucro. Persistir decisões versionadas e referências sem alterar a identidade dos anúncios ou o histórico avaliado.

**3. Invalidação e recuperação** — Integrar publicação de novas evidências à reavaliação durável. Conservar resultado anterior identificado como histórico e impedir reutilização incompatível quando mudarem identidade, fotos, condição, amostra, taxa ou validade.

**Verificação da fase:** cenários ALIASES/HISTORY/PROFIT/CONDITION demonstram agrupamento correto, bloqueios específicos, estimativa reproduzível e lucro; cenários de atualização rejeitam resultado antigo.

## Fase 3 — Integrar autorização e adotar a política

**4. Primeira elegibilidade e reduções** — Aplicar a mesma qualificação aos dois caminhos e conferi-la novamente na autorização final. Preservar prazo, exceção manual, vínculo de destino e identidade lógica dos envios da F16/F09.

**5. Migração e barreira de adoção** — Entregar migração aditiva, leitores compatíveis e ativação persistente após inventário/drenagem do despacho anterior. Preservar corpos e recibos e exigir qualificação das intenções sem transmissão comprovada; falha de dependência após ativação conserva a suspensão de novas autorizações.

**Verificação da fase:** QUEUED/AGE_MANUAL/LEGACY/RACE_FAILURE demonstram revalidação final, concorrência, reinício, transição de política e ausência de POST duplicado, incluindo mensagens incertas.

## Fase 4 — Explicar qualificação e comprovar integração

**6. Diagnóstico, histórico e mensagem** — Expor nome normalizado, evidências, composição e bloqueios nos detalhes e na lista, separando qualificação atual de confirmação histórica. Mensagens recém-geradas acrescentam resumo da referência e ressalvas, preservando textos anteriormente congelados e contexto de navegação.

**7. Evidência integrada e encerramento** — Consolidar o percurso saudável e os casos adversos do contrato, os gates e o corpus real com suas limitações. Entregar evidências sanitizadas na pasta F21 sem modificar relatórios ou declarações de conclusão das features anteriores.

**Verificação da fase:** contrato inteiro e manifesto cobertos, seis gates Python, suíte completa e jornadas `playwright-cli`/avaliação visual das superfícies alteradas; prova real separada do canal fake. Ausência de pré-requisito ou de prova exigida continua pendente. A especificação por si só mantém F21 `pending`.
