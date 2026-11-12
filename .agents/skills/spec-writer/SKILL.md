---
name: spec-writer
description: Especificar uma etapa do PRD do Garimpei produzindo spec.md, plan.md e contract.md com critérios de aceite verificáveis.
---

# Especificação, plano e contrato

Resolva a feature por ID, nome ou pasta. Leia seu conteúdo no PRD, dependências e os arquivos atuais; se o ID for ambíguo ou não existir, esclareça antes de criar documentos.

1. Identifique superfícies públicas, regras, integrações, dados, impactos de arquitetura e decisões pendentes. Para backend, consulte `clean-arch`.
2. Resolva apenas as decisões que mudam o contrato ou a implementação. Preserve escolhas do usuário e registre hipóteses e pré-requisitos externos.
3. Produza `docs/FXX-slug/spec.md` e `plan.md` conforme [feature-template.md](references/feature-template.md), dimensionando o detalhe pela complexidade. O plano ordena dependências e define como verificar cada fase.
4. Produza `contract.md` conforme [contract-template.md](references/contract-template.md): Prerequisites, Quality gates quando aplicáveis, Coverage Manifest e superfícies com itens Given/When/Then e IDs estáveis. Cada critério de aceite do PRD deve ter itens que o cubram.
5. O contrato descreve comportamento observável, incluindo falhas e integração. Testes internos pertencem à estratégia técnica. Cada pré-requisito precisa de forma de criação e verificação; não deixe fixtures, sementes ou credenciais implícitas.
6. Use `node scripts/run-gates.mjs` como entrada dos seis gates de backend e acrescente testes/build relevantes. Ausência de aplicação no estágio de fundação é pré-requisito, nunca evidência de sucesso.
7. Confira consistência entre PRD, dependências, arquivos, plano e contrato. Entregue os três caminhos e decisões pendentes; não avance o status para `done`.

Em pedidos de lote, fundações são sequenciais. Gere documentos em paralelo apenas quando o usuário autorizar esse modo; a especificação de uma feature não autoriza executar outras.
