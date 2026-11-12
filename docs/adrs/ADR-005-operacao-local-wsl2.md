# ADR-005: Executar localmente no WSL2 com dependências Docker e acesso restrito

**Status:** Aceito
**Data:** 10-11-2026
**ADRs relacionados:** [ADR-002](ADR-002-templates-htmx.md), [ADR-004](ADR-004-worker-fila-postgresql.md)

## 1. Contexto e problema

O usuário definiu um MVP individual no próprio computador, com
prioridade para o menor custo viável. O ambiente informado é
Linux no WSL2, com Docker disponível. Não há exigência de
operação contínua durante desligamento ou hospedagem em nuvem.
Os recursos disponíveis à máquina e aos serviços ainda
precisam de avaliação.

O usuário escolheu aplicação no WSL2, PostgreSQL e WAHA em
contêineres e acesso apenas pelo navegador deste computador,
sem login no Garimpei. A stack revisada inclui web e worker
Python nesse ambiente. A topologia está aceita, mas ainda não
existe prova de instalação, consumo ou conectividade do
produto.


## 2. Motivadores da decisão

- Atender ao uso individual no ambiente já informado.
- Evitar contratação de infraestrutura para a validação
  inicial.
- Facilitar desenvolvimento e inspeção dos processos da
  aplicação.
- Conservar dados e sessão de mensageria na parada normal.
- Restringir acesso ao recorte local, sem ampliar autenticação
  ou rede.

## 3. Opções consideradas

- Aplicação e worker no WSL2, com PostgreSQL e WAHA em Docker.
- Aplicação, worker e dependências inteiramente em Docker.

## 4. Resultado da decisão

Escolhida a execução híbrida local. Aplicação e worker rodam
no WSL2 e usam os serviços PostgreSQL e WAHA em contêineres. O
acesso ao produto fica restrito ao próprio computador, sem
login, conforme decisão explícita do usuário.

A ausência de login no produto não elimina a configuração de
acesso aos serviços e às fontes. Monitoramento depende dos
processos ativos; fechar a interface não equivale a parar o
worker, mas suspensão ou desligamento interrompem a operação.


## 5. Prós e contras das opções


### Execução híbrida local

- Favorável: acompanha o ambiente disponível e facilita
  inspecionar a aplicação.
- Favorável: isola dependências sem exigir contêiner para o
  código em desenvolvimento.
- Desfavorável: combina ferramentas Python e Docker na
  preparação local.
- Desfavorável: rede, portas e recursos precisam de
  verificação no WSL2 real.

### Execução integral em Docker

- Favorável: uniformiza execução dos processos e serviços.
- Favorável: concentra dependências de runtime na configuração
  dos contêineres.
- Desfavorável: acrescenta decisões de build, volumes, rede e
  inspeção de código.
- Desfavorável: não elimina a dependência do computador ativo
  nem comprova melhor consumo.

## 6. Consequências

A operação deverá preservar dados e sessão na parada normal e
identificar recursos próprios. Acesso local não autoriza abrir
o produto à rede nem acrescenta contas e colaboração. A
documentação de preparação precisa refletir essa topologia de
forma reproduzível.

A retomada depende dos anúncios disponíveis na fonte; a
operação local não permite recuperar publicações nunca obtidas
que já desapareceram. Não há promessa de disponibilidade
durante o período em que computador ou processos estiverem
desligados.

A execução simultânea de aplicação, banco, mensageria e
eventual navegador permanece sem medição. Essa limitação de
evidência não altera a decisão, mas impede declarar
compatibilidade ou operação concluída apenas com aprovação
documental.


## 7. Referências

- [docs/stack.md:17](../stack.md)
- [docs/PRD.md:39](../PRD.md)
- [docs/stack-reavaliacao.md:15](../stack-reavaliacao.md)
