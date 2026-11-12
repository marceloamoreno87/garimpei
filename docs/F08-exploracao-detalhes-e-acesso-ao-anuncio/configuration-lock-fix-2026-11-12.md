# Correção da contenção de configuração durante publicação F08

Base: `41e27e568ee829dbe347948288c1a690494fcf2d`, worktree90b7, branch `fix/exploration-configuration-lock`. Escopo autorizado pelo coordenador após diagnóstico somente leitura da principal. Nenhuma parada, edição, envio ou alteração de timeout foi executada na principal.

## Causa demonstrada

A publicação periódica do worker adquire o session lock80808008 antes de iniciar REPEATABLE READ. `ExplorationSource.snapshot` usava a leitura padrão F03: parent SELECT FOR UPDATE e depois filhos. A transação aninhada era um savepoint; seu retorno não liberava o row lock, que permanecia até terminar toda a compilação/publicação F08.

Amostras da principal em17:05:51–54 e17:07:40–42 capturaram o holder80808008 por até3,224s, incluindo SELECT de listing/observation/cycle, valuationprogress/evaluation e exploração, com intervalos ClientRead/processamento Python. Refresh F16 esperava a linha da configuração; em uma cadeia já segurava73003/74006, bloqueando também consumidores do lock global. PostgreSQL registrou35 timeouts até17:10:07, sobretudo SELECT FOR UPDATE da configuração, muito depois da conclusão do inventário2546. Não era somente backlog inicial. As etapas de leitura F16 são por UUID; não há chamada a all_visible nesse percurso. A carga F16 amplia a exposição à contenção, mas o holder longo observado é a publicação F08.

O SELECT F08 também carregava JSONs completos de CollectionCycle para cada listing. Para2546 listings em2 ciclos, só results representava56.315.808bytes de armazenamento comprimido repetido pela junção; esse número é proxy de volume, não medição de bytes na rede. A projeção não consome esses diários de ciclo. A tabela histórica de ofertas tinha cerca de3,2GB; nenhum dado/cache foi apagado.

## Alteração restrita

- `PostgresMonitoringQueries` ganhou opt-in `repeatable_snapshot`, utilizado somente pela composição F08. Ele exige transação externa já ativa e isolamento REPEATABLE READ ou SERIALIZABLE; lê parent e filhos sem FOR UPDATE, reutilizando o mapper e o MonitoringSnapshot existentes. Autocommit e READ COMMITTED falham com erro tipado. O modo padrão, read_form, repositório de escrita e UOW/73003 permanecem locking.
- A publicação F08 continua serializada pelo mesmo session lock80808008 adquirido antes do snapshot. A spec permite revisão anterior coerente quando a configuração muda durante a compilação; o publisher seguinte lê o estado novo. Não foi introduzida regra nova de CAS, nem alterados revisão, retenção, paginação, rollback ou atualização explícita.
- Apenas o SELECT de listings da F08 adia os JSONs não usados `latest__cycle__{results,planned,diagnostics,window_evidence,origin}`. F07 e a consulta de estado/diagnóstico atual não foram alteradas.

## RED/GREEN e verificações

Laboratórios descartáveis próprios iniciados por `scripts/init.sh --disposable`, fontes/WAHA em loopback e IAfalse; factories encerraram somente seus recursos. Nenhum grupo real foi acessado.

1. RED da barreira pública: writer F03 expirou após0,506s atrás da publicação F08 suspensa (1FAIL/11,17s). O timeout500ms vale somente para a conexão de teste, mais estrito que a configuração do produto.
2. GREEN da mesma barreira: writer F03 e publicação F16 concluíram em0,0575s enquanto o snapshot F08 permanecia suspenso. Após o edit, a releitura F08 manteve parent+children antigos coerentes; segundo publisher aguardou80808008 e publicou a configuração nova depois. As duas revisões e seus valores foram preservados.
3. Guards: autocommit e READ COMMITTED recusados; RR/SERIALIZABLE aceitos sem row lock; leitor padrão conserva FOR UPDATE.
4. RED da projeção: o SQL ainda selecionava results (1FAIL/2PASS). Após defer, os cinco JSONs estão ausentes, os tuples completos de Offer são idênticos à projeção completa e ambas executam8queries, sem recarga lazy de ciclos.
5. Novos testes:3PASS/32,77s. Focais F03/F08/F16 e HTTP:14PASS/230,50s. Seis gates backend exit0; Django check/drift exit0. Source final estável após essas execuções.

Comandos: `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests/integration/test_exploration_configuration_lock.py -s -q`; focais nos módulos test_monitoring_persistence.py, test_exploration.py, test_first_eligibility.py e HTTP test_alert_diagnostic.py; `node scripts/run-gates.mjs`; Django check e makemigrations --check --dry-run com test_settings. Logs públicos estão na pasta de evidências, em `.txt`, com apenas ANSI/espaços finais removidos. Source-digests registra os quatro arquivos de código/teste.

O full conjunto será executado pelo coordenador após o commit e sem mudanças de fonte durante a execução. O baseline500PASS anterior foi informado pelo coordenador; não é apresentado como resultado do código corrigido. A aplicação na principal e a observação pós-startup também pertencem ao coordenador.
