# ADR-001: Adotar Python e Django como base da aplicação

**Status:** Aceito
**Data:** 10-11-2026
**ADRs relacionados:** [ADR-003](ADR-003-postgresql-django-orm.md), [ADR-006](ADR-006-isolamento-regras-negocio.md)

## 1. Contexto e problema

O Garimpei reunirá anúncios de eletrônicos usados, classificará
condições e estimará oportunidades de revenda com referências
rastreáveis. As regras de correspondência, suficiência da amostra e
acesso à primeira plataforma ainda dependem de discovery. A aplicação
precisa permitir ajustes nessas partes sem transformar o MVP em uma
coleção de serviços independentes.

O usuário solicitou reavaliação livre de preferência por linguagem e de
viés do harness. A comparação incluiu Python, Node/TypeScript, Go e
Rust. A direção Python/Django foi aprovada em 10-11-2026 e substitui a
recomendação anterior de Fastify/Prisma. Este registro aceita a direção
técnica; não há aplicação implementada ou benchmark do produto que
comprove superioridade de runtime.

## 2. Motivadores da decisão

- Facilitar a investigação de dados reais e a evolução das regras de
  comparação ainda desconhecidas.
- Reunir recursos comuns de aplicação e persistência sem escolher um
  serviço para cada responsabilidade.
- Entregar o uso individual local com custo operacional compreensível.
- Preservar testes e limites claros entre regras, orquestração e
  integrações.
- Escolher pelo produto, tratando a adaptação do harness como
  consequência.

## 3. Opções consideradas

- Python com Django.
- Node.js com TypeScript e Fastify.
- Go como base da aplicação.

## 4. Resultado da decisão

Escolhida a opção Python com Django. O encaixe favorece um projeto
integrado e o ciclo de examinar anúncios, identificar exceções e ajustar
políticas antes de estabilizar as integrações. A escolha não se apoia na
necessidade de uma linguagem específica para médias ou cálculos
monetários.

A comparação completa também avaliou Rust; este ADR limita as opções
detalhadas às três alternativas mais próximas para a decisão da base. A
interface e a persistência possuem registros próprios, pois seus trade-
offs não se reduzem à linguagem.

## 5. Prós e contras das opções

### Python com Django

- Favorável: integra recursos usuais de aplicação, reduzindo decisões de
  composição para o MVP.
- Favorável: permite desenvolver exploração dos dados e aplicação no
  mesmo ecossistema.
- Desfavorável: requer disciplina explícita de tipos, dependências e
  distribuição do ambiente.
- Desfavorável: a escolha não elimina a necessidade de medir ou isolar
  trabalho intensivo de processamento.

### Node.js com TypeScript e Fastify

- Favorável: possui ferramentas reais de coleta e automação e oferece
  tipagem estática.
- Favorável: permite compartilhar linguagem com uma interface JavaScript
  independente.
- Desfavorável: a composição discutida mantém mais peças para aplicação,
  persistência e interface.
- Desfavorável: o benefício de uma interface independente não está
  demonstrado pelas jornadas atuais.

### Go como base

- Favorável: oferece tipagem estática e distribuição da aplicação
  compilada.
- Favorável: permite concorrência e integrações de coleta e tarefas
  persistentes.
- Desfavorável: há maior composição esperada para os recursos de
  aplicação discutidos.
- Desfavorável: nenhuma necessidade medida de distribuição ou
  processamento o colocou à frente neste MVP.

## 6. Consequências

A fundação deverá preparar Python/Django e adaptar os scripts e
validadores preservados. Os recursos TypeScript do harness não
constituem validação da aplicação escolhida. A decisão não obriga a
dividir o produto em serviços ou a introduzir outro runtime para cada
etapa de processamento.

Versões, biblioteca de tarefas e ferramenta da primeira coleta não fazem
parte desta escolha de linguagem/framework. A compatibilidade do
conjunto permanece uma obrigação de discovery e da fundação, sem
converter uma direção aprovada em prova de implementação.

## 7. Referências

- [docs/stack.md:9](../stack.md)
- [docs/stack-reavaliacao.md:40](../stack-reavaliacao.md)
- [docs/PRD.md:11](../PRD.md)
