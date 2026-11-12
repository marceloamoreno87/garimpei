# ADR-003: Persistir dados em PostgreSQL com Django ORM e migrations

**Status:** Aceito
**Data:** 10-11-2026
**ADRs relacionados:** [ADR-004](ADR-004-worker-fila-postgresql.md), [ADR-006](ADR-006-isolamento-regras-negocio.md)

## 1. Contexto e problema

O produto precisa conservar interesses, acompanhamento de anúncios,
marcos da carga inicial, comparáveis e histórico de alertas entre
execuções. Reiniciar não pode converter anúncios conhecidos em novos nem
transformar a carga silenciosa em pendências. Essas informações possuem
relações e precisam de gravação consistente.

O usuário escolheu PostgreSQL em Docker e confirmou essa persistência ao
aprovar a stack revisada. Django ORM e migrations integram a composição
aprovada. MySQL e SQLite foram reconhecidos como viáveis, com outros
trade-offs. Não existe banco implementado do produto; a aceitação não
comprova capacidade ou recuperação.


## 2. Motivadores da decisão

- Preservar histórico e relações do acompanhamento entre desligamentos.
- Oferecer transações e restrições de integridade para operações
  relacionadas.
- Permitir tarefas persistentes no mesmo serviço de banco.
- Integrar evolução do armazenamento ao framework escolhido.
- Manter operação local e separação entre uso contínuo e ambientes
  descartáveis.

## 3. Opções consideradas

- PostgreSQL com Django ORM e migrations.
- MySQL/InnoDB com persistência relacional.
- SQLite como persistência local em arquivo.

## 4. Resultado da decisão

Escolhida a opção PostgreSQL com Django ORM e migrations. Ela reúne
persistência relacional e a possibilidade de filas persistentes no mesmo
serviço, com evolução do armazenamento integrada à aplicação. A
preferência não decorre de suposta ausência de transações ou JSON no
MySQL.

O ORM pertence à infraestrutura e não define as entidades de negócio. A
adoção do mesmo banco também não comprova que gravações em conexões
distintas façam parte da mesma transação. A garantia depende da
integração concreta e precisa ser verificada na fundação.


## 5. Prós e contras das opções


### PostgreSQL com Django ORM

- Favorável: atende ao histórico relacional e aos candidatos de tarefas
  discutidos.
- Favorável: combina consultas estruturadas e informações específicas
  das fontes.
- Desfavorável: mantém um serviço de banco e sua configuração
  operacional.
- Desfavorável: capacidade, migrations e recuperação dependem de
  verificação real.

### MySQL/InnoDB

- Favorável: oferece persistência relacional, transações e recuperação
  após falhas.
- Favorável: atende às relações e consultas previstas no produto.
- Desfavorável: não apresentou vantagem específica no ambiente
  informado.
- Desfavorável: a integração com a solução de tarefas precisa de
  composição correspondente.

### SQLite

- Favorável: elimina o serviço separado de banco e simplifica operação
  local.
- Favorável: pode atender uso individual com transações curtas e
  concorrência controlada.
- Desfavorável: a concorrência de escrita exige compatibilizar tarefas e
  persistência.
- Desfavorável: a composição de fila PostgreSQL discutida não se aplica
  diretamente.

## 6. Consequências

A preparação deverá identificar o banco e conservar isolamento e dados
entre reinícios. Migrations precisam evoluir com as funcionalidades, sem
pressupor que uma mudança de código reverta o armazenamento. Parada
normal conserva dados; limpeza permanece restrita a ambiente descartável
autorizado.

A divisão em módulos não exige banco por responsabilidade nem substitui
a modelagem de eventos de negócio. Bibliotecas, versões e detalhes de
esquema não são fixados aqui. Modelos de persistência e mapeamentos
continuam subordinados aos contratos das camadas internas.


## 7. Referências

- [docs/stack.md:11](../stack.md)
- [docs/PRD.md:41](../PRD.md)
- [docs/stack-reavaliacao.md:77](../stack-reavaliacao.md)
