# ADR-006: Isolar regras de negócio e casos de uso do framework e do I/O

**Status:** Aceito
**Data:** 10-11-2026
**ADRs relacionados:** [ADR-001](ADR-001-python-django.md), [ADR-003](ADR-003-postgresql-django-orm.md)

## 1. Contexto e problema

O repositório estabelece dependências voltadas ao domínio, injeção por
construtor, composição explícita e configuração central. A aprovação
de Python/Django preservou esses princípios e determinou sua tradução.
Web e worker precisam executar as mesmas regras, diante de fontes e
políticas ainda sujeitas ao discovery.

A decisão canônica é manter regras e casos de uso independentes de
frameworks e integrações. Ela não representa aprovação de cada caminho
ou detalhe do desenho Python. A organização documentada é proposta
para concretizar a regra, ainda sem implementação ou validação de
imports.


## 2. Motivadores da decisão

- Evitar regras divergentes entre interface e processamento contínuo.
- Testar invariantes com entradas explícitas e substitutos nomeados de
  integrações.
- Conter alterações de fontes, mensageria e banco nas implementações
  externas.
- Manter visível a composição das dependências de cada processo.
- Preservar objetivos de qualidade durante a mudança de linguagem.

## 3. Opções consideradas

- Regras e casos de uso independentes, com framework e persistência em
  adapters.
- Regras e orquestração diretamente nos recursos de modelo e
  apresentação do Django.

## 4. Resultado da decisão

Escolhida a independência das camadas internas. O domínio define
invariantes e contratos; os casos de uso orquestram operações com
dependências injetadas; infraestrutura implementa persistência,
transporte e efeitos externos. A composição monta as dependências, com
configuração de ambiente centralizada.

O uso de Django ORM não transforma modelos do framework em entidades
de negócio. A separação entre escrita por repositórios e leitura por
consultas continua canônica. Traduzir convenções e registro do
framework pertence à proposta e à fundação, sem liberar inversões de
dependência.


## 5. Prós e contras das opções


### Independência das camadas internas

- Favorável: permite verificar regras sem banco, servidor ou sessão de
  mensageria.
- Favorável: compartilha comportamento entre processos sem detalhes de
  transporte.
- Desfavorável: exige contratos e mapeamento entre domínio e
  persistência.
- Desfavorável: o registro do framework exige integração e verificação
  explícitas.

### Regras diretamente no framework

- Favorável: reduz contratos e mapeamentos iniciais em uma aplicação
  simples.
- Favorável: acompanha convenções usuais do framework sem traduzir
  camadas.
- Desfavorável: acopla invariantes e orquestração a persistência e
  apresentação.
- Desfavorável: dificulta testes isolados e amplia o alcance de
  mudanças de integração.

## 6. Consequências

Adapters recebem dependências necessárias, e camadas internas não
consultam um localizador global. Modelos e mecanismos do framework
precisam ser registrados de modo compatível com composição explícita.
Descoberta automática de módulos não autoriza efeitos de negócio
durante importação.

A fundação deverá preparar verificações Python de imports,
arquitetura, tipos, ciclos e código não utilizado. O conjunto
TypeScript preservado não comprova essas propriedades na nova
linguagem. Verificação ausente continua pendente; a adaptação dos
controles acompanha os princípios.

Este registro não introduz barramento de eventos, repositórios remotos
ou serviços distribuídos. A independência pode existir em um projeto
modular local, compartilhado pelos processos web e worker aprovados.


## 7. Referências

- [AGENTS.md:30](../../AGENTS.md)
- [docs/stack.md:80](../stack.md)
- [.agents/skills/clean-arch/SKILL.md:12](../../.agents/skills/clean-arch/SKILL.md)
