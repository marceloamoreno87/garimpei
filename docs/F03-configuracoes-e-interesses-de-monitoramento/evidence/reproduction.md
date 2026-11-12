# Reproduzir a verificação da F03

As evidências usam somente dados sintéticos em `eval_f03_213950`, instância descartável pertencente a esta execução. `CATEGORIA-REAL` é `479353692612078` (Electronics), comprovada no [catálogo verificado](catalog-verification.md). Os nomes dos produtos e CEPs são entradas de teste, sem vínculo com preferências de produção.

1. Prepare os requisitos e um arquivo privado próprio conforme a [operação da F02](../../F02-fundacao-tecnica-e-ambiente-local/operations.md). Configure nele `GARIMPEI_ENV=eval` e uma `GARIMPEI_INSTANCE` exclusiva. Aponte `GARIMPEI_ENV_FILE` para esse arquivo e execute `./scripts/init.sh --disposable`. Use a porta retornada por `Ready`/`./scripts/resolve-env.sh`; nesta avaliação foi `21551`. Confirme `GET /health/ready` 200 e os quatro checks.
2. Para NOVO, RASCUNHO ou ATIVA, execute a factory abaixo trocando o cenário. Ela exige instância marcada descartável e valida a identidade do banco. A limpeza do cenário atua apenas nas duas tabelas F03. Para criar os mesmos estados pela interface, comece em `/`, salve `01001-000` e `25,50`/`12,50`, adicione `PlayStation 5` e selecione a categoria real quando indicado. Salve como rascunho ou conclua, conforme o cenário.

```sh
uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py shell -c 'from tests.factories.monitoring import prepare_state, state_record; prepare_state("RASCUNHO"); print(state_record())'
```

A consulta usada pelo serviço é `from garimpei.main import build_read_monitoring_configuration; print(build_read_monitoring_configuration().execute())`. Para verificar isolamento da fila, conte `procrastinate_jobs WHERE task_name <> 'garimpei.runtime_probe'`; o resultado esperado é zero antes/depois. Os únicos jobs que podem existir são os probes técnicos da F02.

## Serviço e HTTP

A suíte `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests/integration/test_monitoring_persistence.py -v` prepara e limpa PostgreSQL/WAHA próprios pelo lifecycle da F02. Testa os snapshots, os formulários Django, a alteração concorrente com duas conexões, os cenários de falha e o rollback. A matriz declarada está em `apps/backend/tests/fixtures/monitoring/cases.json`; o teste unitário do catálogo verifica também o formato do arquivo e usa uma hierarquia sintética para distinguir agrupadores.

`test_real_database_rollback_on_failure_and_read_error` injeta erro no repositório depois da gravação, ainda dentro da transação, e compara a persistência após o 503. Também injeta falha na leitura antes da gravação e no serviço público. Não há rota de falha no aplicativo.

## Navegador e falhas controladas

Abra `playwright-cli -s=garimpei-F03-verificacao open http://127.0.0.1:<porta>/`; use `snapshot`, `click`, `fill`, `press` e `screenshot`. Para status de POST use `run-code` com `page.waitForResponse(response => response.request().method() === 'POST')` antes de acionar o botão. Não persista cabeçalhos, cookies ou HTML bruto de fontes externas.

- Em NOVO, confira campos vazios, sequência e etapas anteriores. Em interesses, selecione Electronics e confirme que a caixa de Cameras continua desmarcada. Salve o rascunho e recarregue. Acione Adicionar com campo vazio e observe `aria-invalid`, o resumo com foco e a seleção preservada. Corrija e salve só `PlayStation 5`; depois combine com Electronics.
- Em ATIVA, abra duas abas. Salve uma mudança na primeira e envie valores diferentes da revisão antiga na segunda: 409, entrada antiga preservada para revisão, link de recarga e configuração mais recente mantida. Remova o último interesse e tente salvar: 422 sem alteração. Abra a raiz para conferir o encaminhamento para acompanhamento.
- Para testar sem JavaScript, use `playwright-cli run-code` com `page.context().browser().newContext({javaScriptEnabled:false})` em NOVO e percorra o fluxo e a edição em uma nova página. Concluir deve seguir 303 para acompanhamento; editar deve seguir 303 para a página com confirmação e mostrar os valores persistidos.
- Para falha de catálogo ou gravação, use a mesma instância **descartável**, em ATIVA com produto salvo. Rode um processo Gunicorn adicional por falha com o wrapper abaixo; use porta livre em loopback, nunca a do produto. `catalog` injeta falha de leitura, `save` injeta falha depois do `save` real e antes do commit. Encerre esse Gunicorn ao terminar. Não exponha o wrapper fora do ambiente de teste.

```python
# f03_fault.py, em diretório temporário próprio
from garimpei.config.wsgi import application
from tests.factories.monitoring import failure_application

application = failure_application("save")  # ou "catalog"
```

```sh
uv run --project apps/backend --frozen --no-sync gunicorn --chdir apps/backend \
  --bind 127.0.0.1:<porta-livre> --workers 1 --pythonpath <diretorio-do-wrapper> f03_fault:application
```

- Na falha `catalog`, edite CEP, custos e produto antes de acionar Recarregar categorias. Confira que a mensagem e o caminho por produto continuam disponíveis e os campos permanecem. Na falha `save`, atrase o POST com `page.route` apenas na página de teste para observar todos os botões desativados e `aria-busy=true`; solte a resposta e confira 503, dados preservados, foco no resumo e nova tentativa possível. Uma recarga independente no servidor normal deve apresentar os valores anteriores.

## Reinício e layout

Compare o snapshot do rascunho e o da configuração ativa antes e depois de `./scripts/stop.sh` seguido de `./scripts/init.sh --disposable` na **mesma** instância. Não use `--clean` entre as duas observações. Confira que a raiz retoma interesses quando incompleta e segue ao acompanhamento quando confirmada. Compare ID, revisão, marco de conclusão, CEP, custos e interesses; conte novamente os jobs de negócio. O `run_id` do lifecycle deve mudar.

Capture as larguras `360`, `768` e `1440` com `playwright-cli resize`. Para o reflow equivalente a 200% de zoom em um viewport físico de 1440 px, use um contexto Chromium com `viewport.width=720`, `deviceScaleFactor=2` e captura em pixels de dispositivo. Compare `innerWidth` e `document.documentElement.scrollWidth`, e observe os botões, fontes locais e campos em cada captura. Teste o avanço pelo teclado e o foco do resumo nas respostas 422/503. Após verificar a instância de teste própria, encerre a sessão de navegador e limpe o ambiente descartável com `./scripts/stop.sh --clean`.
