# ADR-002: Servir a interface com templates Django e HTMX

**Status:** Aceito
**Data:** 10-11-2026
**ADRs relacionados:** [ADR-001](ADR-001-python-django.md), [ADR-005](ADR-005-operacao-local-wsl2.md)

## 1. Contexto e problema

As jornadas confirmadas são configurar interesses e custos, consultar
três abas, classificar condição incerta, conferir estimativas e abrir o
anúncio original. O MVP será usado por uma pessoa no próprio computador.
Não há requisito de interface offline ou de outro cliente consumindo uma
interface pública independente.

React/Vite havia sido escolhido inicialmente. O usuário reabriu essa
escolha e depois aprovou Python/Django com templates e HTMX. A decisão
está aceita como direção técnica, ainda sem telas implementadas. Este
registro não declara React inadequado nem usa a quantidade de usuários
como único critério de escolha.


## 2. Motivadores da decisão

- Atender às interações descritas no PRD com estado persistido no
  servidor.
- Reduzir o custo de manter frontend e aplicação como projetos
  independentes.
- Compartilhar regras e validações de negócio entre as entradas da
  aplicação.
- Permitir navegação e atualização de listas e detalhes com apresentação
  cuidada.
- Preservar estados explícitos de carregamento, falha e sucesso.

## 3. Opções consideradas

- Templates Django com interações HTMX.
- React/Vite consumindo uma interface de aplicação independente.

## 4. Resultado da decisão

Escolhida a opção templates Django com HTMX. A interface será servida
pela aplicação web e poderá atualizar partes da página nas jornadas
confirmadas. A decisão concentra apresentação e aplicação no mesmo
projeto, preservando a separação das regras de negócio.

Essa escolha substitui a direção anterior de React/Vite. Ela não define
estilo visual, mecanismo de atualização automática ou frequência de
consulta das listas. O acabamento e o tratamento de estados ainda
pertencem à especificação das jornadas, sem serem decididos apenas pela
tecnologia.


## 5. Prós e contras das opções


### Templates Django com HTMX

- Favorável: corresponde às listas, formulários, detalhes e ações
  pontuais do MVP.
- Favorável: reduz contratos e estado duplicado entre projetos
  separados.
- Desfavorável: muitas interações dependem de comunicação com o processo
  web local.
- Desfavorável: foco, navegação, requisições concorrentes e erros
  continuam exigindo desenho explícito.

### React/Vite com aplicação independente

- Favorável: oferece composição de componentes e controle de estado no
  navegador.
- Favorável: favorece interfaces extensas com muitas interações
  coordenadas no cliente.
- Desfavorável: mantém ferramentas, contratos e testes próprios além do
  backend.
- Desfavorável: a independência adicional não foi requerida pelas
  jornadas confirmadas.

## 6. Consequências

A estrutura prevista deixa de exigir um workspace web separado ou
servidor Vite. Templates recebem saídas explícitas dos casos de uso e
consultas, preservando a independência das regras em relação à
apresentação. Uma falha de gravação não pode ser mascarada como sucesso
na atualização visual.

As verificações de navegador precisam cobrir renderização e ações
parciais. Três abas, ordenação, indisponibilidade de estimativa e
classificação manual continuam comportamentos do produto; a tecnologia
não resolve suas pendências de apresentação.

O custo de uma interface mais complexa permanece distinto do custo de
manter a coleta em Python. O registro aceita a composição do MVP atual,
sem estabelecer que uma eventual interface diferente exigiria trocar
também o processamento.


## 7. Referências

- [docs/stack.md:10](../stack.md)
- [docs/stack-reavaliacao.md:59](../stack-reavaliacao.md)
- [docs/PRD.md:43](../PRD.md)
