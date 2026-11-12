---
name: prd-writer
description: Criar ou revisar o PRD do Garimpei, definir etapas, critérios de aceite, dependências e ondas de execução com IDs estáveis.
---

# PRD do Garimpei

Use os requisitos fornecidos pelo usuário e os arquivos canônicos do projeto.

1. Leia `AGENTS.md`, o PRD existente e `docs/prd_progress.json`, quando houver. Identifique decisões tomadas e lacunas que alteram o escopo.
2. Esclareça as lacunas relevantes com perguntas curtas, uma decisão por vez. Quando o usuário estiver definindo etapas progressivamente, registre apenas o que foi definido. Identifique hipóteses; não invente metas numéricas ou decisões de negócio.
3. Use [o formato e o schema de progresso](references/prd-format.md) para produzir `docs/PRD.md`: resumo executivo, problema/oportunidade, público, objetivos, histórias, funcionalidades, fora de escopo, grafo de dependências e critérios de aceite. Escreva no idioma solicitado pelo usuário.
4. Mantenha IDs `F01`, `F02` etc. estáveis. Cada feature deve aparecer nas histórias, funcionalidades, tabela de dependências e critérios de aceite. Documente entradas/saídas entre features e aceite de integração.
5. Valide que as dependências existem, formam um DAG e aparecem antes da feature dependente. A onda é `1 + max(onda das dependências)`, ou 1 sem dependências. Marque as fundações que compartilham arquivos para execução sequencial.
6. Atualize `docs/prd_progress.json` preservando histórico, timestamps e IDs existentes. Novas features começam `pending`, sem ciclos, relatórios ou conclusão. Features retiradas ficam `removed`; não renumere features antigas.

O trabalho está pronto quando o PRD representa os requisitos fornecidos e o progresso corresponde às features e dependências documentadas. A definição do PRD, por si só, não inicia implementação.
