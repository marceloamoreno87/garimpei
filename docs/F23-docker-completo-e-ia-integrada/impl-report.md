# Implementação — F23 Docker completo e IA integrada

O runtime completo e os quatro novos consumidores de IA foram implementados. A conclusão integrada permanece pendente: F21 continua `implemented`, o corpus não tem rótulos humanos independentes e a cadeia positiva completa F23 ainda não foi comprovada. Spec, plan e contract foram preservados.

## Alterações

- Dockerfile runtime/quality e Compose isolam web, worker, login, PostgreSQL, WAHA e Ollama. Wrappers usam Docker por padrão; compatibilidade host é explícita. Preflight confere containers, volumes e redes antes da primeira mutação; aplicação não recebe CLI/socket Docker, e perfil Facebook pertence apenas a worker/login.
- F19 admite alvos tipados sem criar observação fictícia. Migrations 0028–0030 preservam perfis históricos, preenchem alvo/revisão legados e mantêm assinaturas/coortes. Trigger compatível com emissor antigo preenche somente metadata ausente; constraint recusa alvo divergente. Backup F17 inclui as novas tabelas/campos.
- Identidade, comparáveis, investigação e operação usam perfis finitos, referências verificáveis, contexto completo e cache compatível. Fatos originais sustentam revisão de correção manual sem remover sua autoridade; ausências e conflitos continuam explícitos. Seleção prioriza equivalentes e avança exclusões sem confundir orçamento com denominador.
- Retenção assistida precede os critérios determinísticos F06. F15 permanece multimodal; os quatro perfis novos são textuais e declaram mídia não examinada. Diagnóstico assistido explica códigos/snapshot sanitizado sem executar ações. Entrada apenas de metadados recebe 422 antes de criar trabalho; o worker pula entrada inutilizável.
- API assíncrona é idempotente, exige CSRF e revisiona alvos. Detalhes, cobertura e acompanhamento exibem referências, consumidores, limites e próxima ação; GET não inicia inferência. Captura automática de diagnóstico não preenche destino F17 vazio.
- Helper de adoção fria conserva inventário, checksums, pausa e bytes em destino próprio vazio; o runbook distingue seu ensaio mecânico da adoção de uma instalação anterior real.

## Verificação

- Cinco perfis executaram no modelo local fixado com GPU, com validação e consumidores persistidos: quatro novos perfis textuais e F15 com PNG autorizado. O comparável isolado permaneceu insuficiente para a amostra mínima; F15 permaneceu parcial/incerto. Nenhum desses resultados foi promovido artificialmente a Ouro.
- Runtime final aplicou 0030 e retornou health 200, preservando 8 requisições, 8 partes/resultados, 7 revisões/consumidores, assinaturas/coortes, mídia, tokenizer e controles. Recuperação do Ollama em idle foi executada; chamada real de término incerto não foi fabricada.
- Backup Docker F17 anterior a 0030 restaurou 54 tabelas, resultados e mídia em destino isolado; novo backup pós-0030 verificou integridade e metadata contra a fonte. Estado de restauração e pausa são explicitados nas evidências separadas.
- Seis grupos Python passaram. A bateria completa foi coletada em 968 nodeids; resultados originais e reexecuções dirigidas permanecem separados na cobertura final. Falhas reproduzidas e correções de fixtures preservam critérios, contagens, prazos de negócio e ausência de duplicação.
- Revisão independente encontrou três P2, todos corrigidos com regressões; conferência posterior dos deltas de produção não identificou novo P1/P2. UI foi navegada com playwright-cli, screenshots e limites documentados.

## Limites

O corpus materializa 39 entradas autorizadas/controladas e um worksheet pendente; não contém gabarito humano inventado. A qualidade independente, o aceite real positivo F21, a cadeia completa com cinco comparáveis revisados/modelo real/mensagem capturada e a adoção/rollback de instalação anterior continuam sem aceite. Não houve login em conta real nem envio externo real. Consulte o relatório canônico final e o diário para os vereditos por item e os códigos de saída.
