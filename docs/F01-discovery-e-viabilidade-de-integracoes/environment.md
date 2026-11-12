# F01 — Ambiente, protocolo e passagem para F02

Run `2026-11-10T19-07-31Z`, iniciado em 2026-11-10T19:07:31Z. Este registro executa as fases documentais autorizadas no pedido atual; os limites históricos de geração de spec/plano não impedem esta execução. Fontes: [stack](../stack.md), [harness](../harness.md), [arquitetura](../architecture/README.md), [contrato](contract.md) e [evidências](evidence-index.md).

## Escopo desta execução

Autorização: «Use $implement-and-evaluate F01 para executar o ciclo completo com até três ciclos de correção. Preserve o harness ao integrar o scaffold. Registre evidências e pendências. Não faça commit, push ou PR neste pedido.»

| Dimensão | Escopo adotado / limite |
|---|---|
| Ações | Ler documentos e fontes públicas oficiais, inventariar recursos locais por comandos de leitura, executar gates existentes e escrever artefatos F01/progresso. |
| Plataformas | OLX, Facebook Marketplace, Enjoei, Mercado Livre; documentação WAHA. |
| Contas e entradas | Nenhuma conta ou segredo utilizado. Sem CEP, login, sessão WAHA ou destinatário. |
| Requisições | Pesquisa documental pontual, sem coletor, carga, paginação de anúncios, login, proxy ou tentativa de superar bloqueios. Links com 403/login são lacunas; sem repetição automática. |
| Duração | Limitada à sessão desta execução; inventário de uma amostra. Sem monitoramento periódico nem medição de latência externa. |
| Custos | Nenhuma compra, plano, assinatura ou recurso pago provisionado; custo total futuro desconhecido. |
| Recursos criados | Lock de feature em metadados Git, temporário do sistema para snapshot/comandos e documentos da feature. Nenhum contêiner, banco ou serviço do produto criado. |
| Limpeza | Liberar apenas lock próprio ao finalizar. Nenhum processo/volume/sessão preexistente deve ser encerrado; temporário contém apenas evidências locais e pode ser removido após validação. |
| Scaffold | F01 prepara o mapa abaixo. Geração/integração de Django e adaptação dos scripts são escopo de F02; nenhum scaffold copiado nesta execução. |

Provas com contas, instalação, custos e mensagens não têm escopo específico autorizado. Elas não foram iniciadas; a investigação documental e a inspeção local de leitura prosseguem dentro do pedido atual. Fontes inacessíveis são registradas individualmente no índice.

## Protocolo de investigação

1. Para cada candidata, verificar API, páginas públicas, sessão/cookies e scraping avançado separadamente; registrar autenticação, restrições/antirrobô, campos, esforço, custo, estabilidade e manutenção.
2. Confrontar categorias/subcategorias, texto/modelo, localização, retirada, entrega, frete, mudanças e recuperação com o PRD. Não extrapolar documentação de vendedores para busca geral de ofertas.
3. Distinguir referências de usados e novos; não gerar amostra sintética como comprovação de mercado.
4. Consultar WAHA por versão/engine/CPU, sessão/persistência/custo; separar serviço, autenticação e entrega. Inventário pontual não é benchmark.
5. Para cada conclusão usar D/I/O/H/L do índice. Ausência exige data, contexto, impacto e próximo passo. A recomendação não satisfaz decisão explícita.

Uma prova futura deverá registrar antes de executar: plataforma e modalidade; pergunta verificável; fonte e conta autorizadas; CEP privado se necessário; URLs/recursos e propriedade; máximo de páginas/requisições, duração e concorrência; orçamento; condição de parada em 401/403/429/CAPTCHA; saída sanitizada; plano de limpeza. Um teste WAHA precisa ainda de imagem/digest, engine, sessão, destinatário e autorização específica de envio. Esses campos estão **pendentes**, sem valores fictícios.

## Inventário local

**E-LOCAL-01**, amostra de **2026-11-10T19:09:15Z**, comandos executados uma vez para registro, sem carga de aplicação. Todos os comandos abaixo retornaram exit 0. Valores arredondados de `free`/`df`; nenhuma inferência sobre RAM física do host.

| Comando | Resultado sanitizado |
|---|---|
| `git --version` | 2.53.0 |
| `bash --version` | 5.3.9(1), x86_64-pc-linux-gnu |
| `node --version` | v26.3.1 |
| `uname -srm` | Linux 6.18.33.2-microsoft-standard-WSL2 x86_64 |
| `lscpu` (campos selecionados) | 32 CPUs lógicas visíveis; AMD Ryzen 9 9950X 16-Core Processor; hipervisor Microsoft |
| `free -h` | RAM total visível 31 GiB; usada 3,7 GiB; disponível 27 GiB; swap 8 GiB, sem uso nessa amostra |
| `df -h .` | Filesystem do checkout: 1007 GiB totais, 167 GiB usados, 789 GiB disponíveis, 18% |
| `docker version --format '{{.Client.Version}}\|{{if .Server}}{{.Server.Version}}{{end}}'` | Cliente e servidor 29.9.3 |
| `docker compose version` | v5.7.0 |
| `docker info --format '{{.Architecture}}\|{{.NCPU}}\|{{.MemTotal}}\|{{.OSType}}'` | x86_64, 32 CPUs, 33.650.585.600 bytes de memória reportada pelo daemon, linux |

Os separadores `\|` nas células acima escapam a tabela Markdown; nos argumentos reais são `|`, sem barra. Não foi inspecionado `docker inspect`, ambiente privado ou conteúdo de sessões. Os recursos reportados pelo daemon podem compartilhar a mesma capacidade WSL; **não somar** as duas memórias. RAM do Windows, configuração `.wslconfig`, limites por contêiner e margem sob carga permanecem L-05. Consumo mostrado é do ambiente inteiro, sem atribuição ao Garimpei.

Conclusão: as ferramentas e a arquitetura observadas permitem planejar a validação local. Compatibilidade conjunta de navegador, Django, worker, PostgreSQL e WAHA continua **não testada**. Não é necessário provisionar cloud para essa comparação.

## Pré-requisitos e verificação

| Entrada | Preparação | Verificação | Ausência / consequência |
|---|---|---|---|
| Requisitos e checkout | Ler fontes canônicas e preservar trabalho não rastreado; snapshot antes de editar. | Hashes de 492 arquivos e JSON original; comparar no fechamento (E-PRESERVE-01). | Sem baseline confiável, não sobrescrever arquivos existentes. |
| Exclusão por feature | Criar `.git/feature-locks/F01.json` com exclusividade, PID vivo, host, branch, início/run. | Identidade/propriedade antes de liberar; arquivo sob `.git`, sem segredo em relatório. | Lock ativo de outra execução impede concorrência. |
| Git/Bash/Node | Usar executáveis presentes, sem instalação. | Versões acima e dois gates do contrato. | Gate não executado/falho impede aceite. |
| Fontes oficiais | Abrir documentos públicos e guardar síntese datada/URL/estado. | [Índice de evidências](evidence-index.md), com 403/login explícitos. | Lacuna por capacidade; não fabricar dados. |
| Área temporária | Diretório próprio do sistema para baseline/saídas sanitizadas. | Fora da raiz; proprietário desta execução identificado no lock. | Não gerar arquivos brutos na árvore do produto. |
| Contas/CEP/prova | Definir escopo específico e entradas privadas se a prova for aprovada. | Presença/prontidão, nunca valor em relatório. | Cenário prático não executado; revisão documental continua. |
| WAHA / imagem / sessão | Fixar release e digest, engine e volume próprios antes de futura instalação. | Plataforma da imagem, prontidão do serviço, sessão e teste de persistência separados. | L-06; Docker ativo sozinho não comprova WAHA. |
| Aprovação da escolha | Apresentar recomendação rastreável ao usuário. | Data e referência à decisão explícita em [decisions.md](decisions.md). | L-08: F01 não fica done; F02 permanece bloqueada por dependência. |

Nenhuma aplicação necessária a este contrato; `init.sh`/`stop.sh` não são acionados contra processos reais, porque a F01 não inicia aplicação. O comportamento anterior ao scaffold é verificado pelo teste existente. Sem banco, migrations, fixtures ou seeds de produto na F01.

## Passagem técnica para F02

O mapa é proposta de aceite para o futuro contrato F02. Não são ferramentas já implementadas/aprovadas. Escolha de plataforma/acesso pendente impede executar a fundação dependente, conforme plano. [Stack](../stack.md) e regras de negócio continuam canônicas; Node fica nas ferramentas do harness, sem substituir Python do produto.

| Recurso / preparação em F02 | Integração seletiva e configuração | Verificação requerida / consequência da ausência |
|---|---|---|
| Base Python/Django | Fixar versões/gerenciador compatíveis e gerar em temporário; listar origem, dependências e inventário aceito/rejeitado antes de copiar para `apps/backend/`. | Bootstrap Django real e comandos de build/estáticos aplicáveis; sem base testada, fundação pendente. Não usar gerador TypeScript como base Django. |
| Arquivos canônicos | Preservar `AGENTS.md`, `README.md`, `.gitignore`, `.codex/`, `.agents/`, `scripts/`, PRD, arquitetura/design e trabalho atual; mesclar apenas ajustes necessários. | Diff/hash de cada arquivo tocado; sem substituição em bloco ou `--force`. |
| `scripts/init.sh` | Preparar dependências Python, configuração, migrations e iniciar web/worker separados; templates/HTMX servidos por Django. | Web/worker prontos e falha de dependência obrigatória retornando erro; não basta PID/porta abertos. |
| `scripts/resolve-env.sh` | Portas livres por checkout, bind `127.0.0.1`, banco `garimpei_<ambiente>` e identificação de recursos. | Dois ambientes simultâneos isolados; colisão de porta/banco detectada, sem tomar recurso alheio. |
| `scripts/spawn-detached.mjs`, PIDs e `stop.sh` | Identificar processos Python/grupos por checkout e início; encerrar só próprios. Parada normal conserva banco e sessão. | Regressões de PID reutilizado, processo alheio, parada/retomada e dados preservados; limpeza apenas descartável autorizada. |
| `scripts/migrate-dev.sh` | Trocar pressuposto Prisma por migrations Django/fila, com configuração central e banco identificado. | Migrations reais em banco descartável marcado; não aceitar execução contra banco compartilhado desconhecido. |
| Compose PostgreSQL/WAHA | Fixar imagens/digests, nomes/labels e volumes privados por ambiente; chaves em ambiente, sem QR/cookies em artefatos. | Bind local, propriedade, readiness e persistência após reinício; não apagar sessões/volumes existentes. |
| Fila / worker | Validar candidato Procrastinate com PostgreSQL; composição explícita e DI, regras `domain` ← `usecase` ← `infra`. | Integração transacional e retomada das tarefas verificadas; sem Redis inicial. A fila não garante envio exatamente uma vez. |
| `scripts/run-gates.mjs` | Manter entrada canônica, adaptar comandos e pré-requisitos à base Python. | Seis coberturas abaixo com comandos reais e violações representativas rejeitadas; ferramenta ausente não vira PASS. |
| Testes/skills | Adaptar pressupostos npm/Prisma em lifecycle, testes e validadores, preservando regressões relevantes. | `check-harness.mjs`, testes do harness e testes Python aplicáveis aprovados; nenhum gate vazio. |

### Coberturas de validação exigidas

O contrato F02 deve definir e depois executar comandos reais por ferramenta, escopo e código de saída. Ainda **não há aprovação** de:

1. Tipos Python, inclusive entradas web/worker usadas.
2. Lint Python e verificações aplicáveis de templates/JavaScript autoral.
3. Limites de importação/dependências e bloqueio de I/O em domínio/casos de uso.
4. Arquitetura: estrutura, configuração central, DI e composição Django/web/worker.
5. Ciclos de importação nos módulos Python.
6. Código e dependências não utilizados, considerando registros/entradas do framework.

Complementar com testes de negócio, integração PostgreSQL/fila, inicialização real web/worker, migrations, build/coleta de estáticos quando pertinente e jornadas via `playwright-cli`. Tipos, lint e testes isolados não substituem essas seis coberturas. O runner atual retorna pré-requisito 64 sem backend e não comprova validação Python; não precisa ser executado como gate F01.
