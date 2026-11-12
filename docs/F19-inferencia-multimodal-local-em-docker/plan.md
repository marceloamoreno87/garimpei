# Plano de implementação — F19

Pré-requisitos: [spec](spec.md), [contrato](contract.md), F02/F12 disponíveis, Python/uv/lock existentes, Docker/NVIDIA no WSL e ambiente descartável próprio. A prova real precisa da RTX 5070 livre de outro ambiente Garimpei, artefatos oficiais fixados e foto autorizada em manifesto privado. Não exige F14/F15/F17 implementadas. Esta entrega é documental.

## Fase 1 — Preparação e limites

**1. Resolver artefatos e propriedade.** Materializar o lock de imagem/modelo/tokenizer e documentar preparação verificável, identificando daemon, GPU, portas e volumes próprios. Conservar a separação entre download e inferência.

**2. Definir entradas e saída validada.** Materializar corpus, schema, transformações, contagem de contexto e limites operacionais da spec. Preservar o material original e identificar tudo que não foi examinado.

Verificação da fase: metadados oficiais completos e hash verificável; regressões de assinatura/cobertura/schema e nenhum requisito externo tratado como já comprovado.

## Fase 2 — Serviço e persistência

**3. Estender lifecycle local.** Integrar Ollama/GPU ao Compose, configuração e manifesto sem tornar indisponibilidade da IA uma falha global da aplicação. Preservar pesos e identificar recursos antes de iniciar ou encerrar processos.

**4. Integrar requisições persistentes.** Acrescentar estado, partes, resultados e coordenação de GPU ao worker, disponibilizando a fronteira consumível por F15. Retomar somente trabalho válido e manter slots para coleta/alertas.

Verificação da fase: integração PostgreSQL, manifests legados, interrupção, capacidade concorrente, recurso ocupado e resultados fora de ordem com dependências controladas.

## Fase 3 — Controles e recuperação

**5. Entregar modo equilibrado.** Implementar análise habilitada automática, descarregamento por inatividade, pausa com drenagem e retomada explícita conforme spec. Estados diferenciam residência, disponibilidade e ação do usuário.

**6. Expor operação e smoke test.** Acrescentar tela em Integrações e comandos locais de status/preparo/prova sem alterar condição, lucro ou recibos. Dar diagnóstico específico e recuperação limitada para cada falha prevista.

Verificação da fase: jornada via playwright-cli, revisão/CSRF, falhas do gateway e persistência da pausa; avaliação visual conforme frontend-ui-design.

## Fase 4 — GPU real e evidências

**7. Medir execução local.** Exercitar texto/imagem na RTX 5070 dentro do contêiner, com pins efetivos, isolamento de rede, uso frio/quente e coexistência com a aplicação. Conferir liberação/recarga de memória e recuperação no ambiente proprietário.

**8. Consolidar validação.** Executar gates, suíte, checks e build; vincular cada item do contrato à evidência e documentar operação/limitações. Falta de prova real permanece pendente; conclusão depende da avaliação completa, sem commit, push, PR ou deploy implícitos.

Verificação da fase: todos os ACs e gates têm resultado verificável; medições podem exigir revisão dos parâmetros antes da avaliação, sem trocar modelo ou liberar fallback silencioso.
