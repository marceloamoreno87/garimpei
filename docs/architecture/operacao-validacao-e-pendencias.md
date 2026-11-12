# Operação, validação e pendências

Estado: **operação proposta, ainda sem suporte executável Python**. A escolha local está aprovada; comandos, versões e ferramentas precisam ser especificados em F02.

## Processos e dependências

| Elemento | Responsabilidade e readiness proposta | Comportamento diante de indisponibilidade |
|---|---|---|
| Web Django | Servir HTML/HTMX e executar ações/consultas; verificar bootstrap e persistência necessária | Falha explícita de inicialização; não confirmar gravações que falharam |
| Worker Python | Consumir tarefas persistentes, coletar/processar e enviar; indicar vida e capacidade de consumir trabalho | Trabalho permanece recuperável; web informa estado sem prometer atualização corrente |
| PostgreSQL | Dados e tarefas persistentes | Web/worker não podem declarar operações dependentes bem-sucedidas |
| WAHA | Envio pela sessão configurada | Alertas afetados ficam com falha/incerteza identificada; disponibilidade de consulta local não comprova entrega |
| Fontes externas | Anúncios e referências definidos em F01 | Coleta/avaliação falha ou parcial; não inventar preço, condição, entrega ou cobertura |
| Navegador automatizado, se necessário | Recurso do adaptador de coleta | Falha identificada na tarefa, com liberação de recursos e recuperação conforme contrato |

Readiness depende da configuração e da etapa. F02 não comprova uma sessão WAHA real nem coleta real que pertença às features seguintes. Quando um processo/recurso obrigatório da execução configurada estiver ausente, os scripts precisam informar a falha, em vez de anunciar ambiente integralmente pronto.

## Lifecycle a especificar em F02

1. Resolver a identidade do checkout/ambiente, portas e nomes próprios de serviços e bancos.
2. Validar ferramentas, configuração requerida e compatibilidade do ambiente Python/WSL2/Docker.
3. Preparar PostgreSQL e migrations no banco identificado; preparar outros serviços previstos na etapa.
4. Iniciar web e worker separadamente e verificar sua prontidão, sem executar coleta ou envio como efeito de importação.
5. Registrar PIDs/grupos, portas, logs e recursos pertencentes à execução.
6. Na parada, interromper novas execuções, tratar trabalho em curso conforme contrato e encerrar recursos próprios preservando dados e sessão.

Os scripts canônicos continuam sendo a interface operacional pretendida, mas o suporte atual a npm/Prisma precisa mudar. O mapa de arquivos afetados está em [stack.md](../stack.md). Não há comando Python de instalação, servidor WSGI/ASGI ou gerenciador de dependências fechado neste documento.

Migrations Django e da biblioteca de tarefas escolhida terão ordem e compatibilidade verificadas. Um rollback de código não implica desfazer migrations automaticamente. Limpeza de banco permanece restrita a ambiente descartável identificado e autorizado.

## Isolamento local e dados

- Manter prefixo `garimpei_` e bancos separados para uso contínuo, desenvolvimento e testes.
- Resolver colisões de portas também para PostgreSQL e WAHA; porta aberta não prova propriedade do serviço.
- Identificar contêineres por projeto/ambiente, não por uma busca genérica contendo “postgres”.
- Preservar volumes e sessão na parada normal. Não copiar uma sessão WhatsApp real para worktrees de avaliação.
- Definir backup e restauração como procedimentos de operação com evidência de recuperação; método e frequência aguardam a especificação do ambiente.
- Tratar suspensão/desligamento como interrupção. A retomada é limitada ao que a fonte ainda disponibilizar.

## Configuração, logs e interface

A leitura autoral de ambiente fica em `config/env.py`. Bootstrap e settings consomem os valores centrais; adapters recebem os dados necessários pela composição. Configuração de fonte/WAHA pertence a pré-requisitos explícitos, sem exigir segredos de uma integração para comandos que não dependam dela.

Logs de aplicação serão JSON estruturado. Propõe-se correlacionar execução de coleta, tarefa, anúncio/evento e tentativa de envio, conservando só identificadores e diagnósticos necessários. Cookies, chaves, credenciais, conteúdo integral de sessão e valores secretos ficam fora dos logs e dos relatórios. Saída dos scripts continua legível.

O acesso apenas local dispensa login no recorte aprovado, mas não a configuração de acesso ao banco/WAHA. Propõe-se bind local, validação de hosts e proteção de operações mutáveis. Textos de anúncios são entrada externa; templates devem escapar seu conteúdo e as ações HTMX devem preservar as proteções aplicáveis do Django. [Segurança Django](https://docs.djangoproject.com/en/5.2/topics/security/).

A interface usará DTOs para páginas e fragmentos HTML. A composição editorial e as regras confirmadas estão em [docs/design](../design/MASTER.md); carregamento, vazio, falha, gravação pendente e sucesso ainda precisam de contratos completos. O primeiro uso será guiado e sua conclusão libera a primeira coleta; reinícios retomam o acompanhamento salvo. Na lista, um aviso permite aplicar novos dados ao clicar, preservando filtros, sem reordenação automática durante a leitura. Essa regra não pausa coleta ou alertas. O uso de HTMX não escolhe polling, SSE ou WebSocket: mecanismo e frequência de detecção de mudanças continuam pendentes.

## Gates e evidências futuras

| Cobertura exigida | Evidência que F02 precisa definir e produzir |
|---|---|
| Tipos e lint | Comandos Python sobre código autoral, com tratamento explícito do framework e de arquivos gerados |
| Limites de dependências | Rejeição de imports de Django/I/O em domínio/casos de uso e de dependências para camadas externas |
| Arquitetura e composição | Verificação das convenções Python, configuração central, DI e registros do framework sem dependências globais de negócio |
| Ciclos e código/dependências não utilizados | Análise que reconheça entradas web/worker e não esconda módulos inteiros com ignores amplos |
| Integração de framework | Registro ORM, migrations, bootstrap antes de haver dados de negócio e execução de web/worker |
| Persistência/fila | Transação, recuperação e concorrência segundo o mecanismo escolhido, sem assumir atomicidade por compartilhar o banco |
| Testes de regras | Fakes nomeados para fontes/mensageria e testes das invariantes/ausências conforme contrato de cada feature |
| Jornadas | Navegação por `playwright-cli`, verificando abas, detalhes, classificação e falhas quando essas features existirem |

Os gates TypeScript atuais são parte do harness preservado e não validam esta arquitetura. Ferramenta não definida, gate não executado ou cenário sem evidência permanece pendente. Uma implementação vazia não deve passar por ausência de testes ou por ignorar os diretórios relevantes.

Para esta entrega documental, a verificação abrange links, referências, formato dos ADRs, coerência com PRD/stack e preservação do progresso. Não se executam gates da aplicação para declarar Python aprovado sem aplicação.

## Pendências e destino de resolução

| Pendência | Fonte | Resolver antes de |
|---|---|---|
| Escopo de investigação prática e primeira plataforma/acesso | P01 | Execução de F01 e especificação de F04 |
| CPU/RAM disponíveis, engine WAHA e requisitos locais | P02 | Compatibilidade concluída em F01 e ambiente executável de F02 |
| Versões, dependências, servidor, convenções e biblioteca de tarefas | Stack/F02 | Contrato e implementação da fundação |
| Atomicidade de dados e tarefas ou outbox | Proposta de confiabilidade | Implementação do fluxo que dependa dessa garantia |
| Categorias, correspondência, duplicatas e inclusão de interesses | P03/P04 | Especificações F03/F04/F09 afetadas |
| Geografia e entrega no CEP | P05 | Coleta/geografia de F04 |
| Critérios de classificação automática e apresentação de informações conflitantes; a escolha manual já deve ser preservada e não dispara alerta | P06 | F05 e comportamento correspondente de F09 |
| Amostra, método, equivalência e ausência de referência de novo | P07 | F06 e propagação para F07/F09 |
| Valores de custo, arredondamento e desconhecidos | P08 | F03/F07 |
| Intervalos, tentativas, reconciliação e conteúdo dos alertas | P09 | Coleta agendada e conclusão de F09 |
| Campos dependentes da fonte, política para anúncio removido e mecanismo/frequência de detecção de mudanças; fluxos visuais, ordenação, paginação e atualização ao clicar já definidos em docs/design/flows-reference.md | P10 | F08 |
| Prazo e métricas de validação do valor | P11 | Avaliação de resultado do produto |

Estas lacunas não autorizam escolher defaults de negócio para fechar o desenho. Uma mudança que afete escopo ou operação volta à decisão do usuário; detalhes técnicos podem ser propostos nos contratos dentro da direção já aprovada.
