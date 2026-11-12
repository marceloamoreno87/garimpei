# Plano de implementação — F07

**Pré-requisitos.** F03, F04 e F06 integradas e avaliadas. Preparar PostgreSQL e aplicação descartável seguindo [operações F02](../F02-fundacao-tecnica-e-ambiente-local/operations.md). Confirmar a leitura de configuração ativa, observações e eventos imutáveis de F04 e validade/referência da avaliação F06.

## Fase 1 — Política e componentes do cálculo

**1. Implementar cálculo e proveniência no domínio.** Aplicar a fórmula e o arredondamento da [spec §3](spec.md#3-decisões-técnicas), modelar a composição por modalidade e os motivos de indisponibilidade. Entregar os casos determinísticos do contrato na convenção de factories e fixtures do backend.

**Verificação.** Exercitar com testes unitários a taxa no limite de meio centavo, os estados do frete, a retirada e os lucros calculáveis de zero e negativos. Comparar as somas com a composição exposta.

## Fase 2 — Integrar as consultas

**2. Ligar as leituras das três dependências.** Usar as interfaces de F03, F04 e F06, preservando revisão da configuração, identidade da observação e ID da avaliação. Montar as consultas em `main.py` com recorte consistente.

**3. Expor composição vigente e por evento.** Vincular redução ao preço da observação que originou o evento. Tratar mudança de variante, CEP, vencimento da avaliação e falhas técnicas. Entregar a composição e sua proveniência para F08 e F09.

**Verificação.** Rodar os itens SVC do [contrato](contract.md) em PostgreSQL. Confirmar que uma redução mantém o próprio preço após observação posterior e que uma edição confirmada altera a consulta vigente sem misturar revisões.

## Fase 3 — Verificar entrega

**4. Executar a matriz e os gates.** Rodar os comandos do contrato e registrar a preparação reproduzível e evidências por item. Conferir a cobertura dos quatro critérios do PRD e as interfaces destinadas à F08 e à F09.
