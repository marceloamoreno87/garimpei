# Plano de implementação — F23 Docker completo e IA integrada ao fluxo

**Estado:** especificação de 2026-11-13; implementação não iniciada. Referências: [spec](spec.md), [contrato](contract.md), [PRD](../PRD.md). Complexidade complexa; prioridade 1, onda 14. Fundação sequencial: Compose, lifecycle, configuração, fila e composição são compartilhados; não executar frentes concorrentes nesses arquivos.

**Pré-requisitos:** código integrado de F02/F13/F14/F15/F17/F18/F19/F20/F21/F22; Docker/Compose, NVIDIA Container Toolkit, GPU local livre e host Linux/WSL2 com encaminhamento gráfico verificável. Imagens/modelo fixados, arquivo privado por ambiente, corpus autorizado e rótulos humanos conforme spec §7. F21 ainda possui prova real positiva pendente e bloqueia a conclusão integrada. Desenvolvimento controlado não constitui aceite dessa dependência.

## Fase 1 — Imagem e operação isolada

**1. Runtime completo** — Preparar imagem da aplicação e estágio de ferramentas, serviços web/worker/manage e redes/volumes de Compose conforme spec §2–3. Preservar o monólito Django, os pins dos serviços existentes e a restrição de acesso local.

**2. Lifecycle e sessão dedicada** — Adaptar wrappers para operar sem runtime Python/Node no host, coordenar migrations, prontidão, propriedade e grupos reservados. Disponibilizar login humano no Chromium do contêiner e recuperação explícita de inferência incerta, preservando as barreiras F11/F19/F22.

**Verificação da fase:** build reproduzível, inventário dos processos/contêineres, saúde real, abertura gráfica, sandbox, ausência de socket Docker na aplicação e conservação dos volumes após parada normal. Registrar pins resolvidos e comandos operacionais em `operations.md`.

## Fase 2 — Adoção e persistência

**3. Migração segura da instalação** — Preparar transição explícita de perfis, mídia, configurações, banco e análises para o runtime completo. Vincular adoção ao inventário e backup restaurável F17, com rollback sob barreira e sem repetir mensagens incertas.

**4. Revisões de assistência** — Introduzir contratos, persistência, leitura e vínculo de consumo dos resultados por finalidade, reutilizando o runtime de inferência. Preservar revisões e decisões históricas e registrar a nova política sem promover dados legados a analisados.

**Verificação da fase:** migração em base preenchida, restauração, unicidade concorrente, rastreabilidade de consumidor e preservação de recibos/filas/pausas. Não iniciar transição no ambiente real com backup não verificado.

## Fase 3 — Inferência e consumidores de negócio

**5. Perfis locais e validação** — Acrescentar perfis finitos de identidade, comparáveis, investigação e operação, com schemas/referências verificáveis e HTTP interno. Preservar modelo, limites do perfil F15, coordenação GPU e tratamento de resultados tardios/saídas inválidas.

**6. Fluxo de decisão integrado** — Conectar os resultados à normalização F18, investigação F13/F18, retenção F06 e qualificação F21/F16. Aplicar nova política somente às decisões correspondentes e manter cálculo e mensagem derivados dos snapshots determinísticos.

**Verificação da fase:** cenários positivos, insuficientes e contraditórios; preço parcial/acessório; correção manual; cache, concorrência, atraso e pausas. Inferência bloqueada não pode impedir consulta, coleta independente ou preservação de resultados válidos.

## Fase 4 — Consulta, explicação e cobertura

**7. Evidências nas jornadas existentes** — Expor revisão, origem e limitações nos detalhes, cobertura por interesse/finalidade na integração e explicação assistida no acompanhamento. Reusar padrões de design e recuperação contextual, com idempotência, CSRF e leitura sem efeitos.

**Verificação da fase:** respostas HTTP, navegação `playwright-cli` em desktop/largura estreita, teclado, estados sem dados/pendente/falha e continuidade de filtros. Confrontar contagens e evidências da UI com o mesmo snapshot persistido.

## Fase 5 — Qualidade e prova integrada

**8. Corpus e execução real** — Materializar corpus rotulado por humano e comparar a base atual com a nova política. Produzir execução GPU de cada perfil e cadeia completa até WAHA controlado, relacionando chamada, validação, consumidor e efeito, conforme spec §7.

**9. Fechamento documental e operacional** — Consolidar operações, pins, matriz por frente e evidências de contrato, incluindo falhas, reinício e rollback. Sincronizar PRD, stack, arquitetura e estado atual somente com resultados comprovados; preservar a pendência F21 até seu aceite próprio.

**Verificação da fase:** `node scripts/run-gates.mjs` no contêiner de ferramentas, pytest a partir de `apps/backend/`, checks/migrations Django, wheel/imagem, harness e UI/E2E; comparação humana sem regressão crítica. Todos os itens precisam de evidência correspondente; corpus/GPU/dependência ausentes deixam conclusão pendente.

O plano não autoriza implementação de outras features, envio real, commit, push ou deploy. Especificar F23 mantém seu progresso `pending`; implementação e avaliação são etapas posteriores.
