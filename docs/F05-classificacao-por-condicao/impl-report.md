# Implementação — F05 Classificação por condição

Status: implementada; veredito de conclusão reservado ao avaliador. Execução local, sem delegação, commits ou operações remotas. Spec, plano, contrato e o diário anterior foram preservados.

## Fases

| Etapa do plano | Entrega | Verificação |
|---|---|---|
| 1 — Entrada e regra | Declarações integrais com normalização Unicode, precedência de defeito, evidência original; projeções por ID/aba sobre a última observação aceita de F04. | Matriz unitária, worker real, substituição/ausência/falha, identidade e republicação. |
| 2 — Escolha manual | Migration 0005, escolha 1:1, CHECKs, revisão e instante; lock transacional compartilhado com a publicação de F04. Consulta e gravação usam o mesmo snapshot protegido. | Coleta no schema 0004 antes da migration; rollback PostgreSQL; duas correções simultâneas; coleta em voo; revisão antiga e elegibilidade alterada. |
| 3 — Abas e detalhes | Rotas HTML/CSRF; três abas; procedência; primeira escolha/correção; espera, confirmação, conflito e recuperação; preço pt-BR e texto ampliado. | UI-CONDICAO-01–08 e E2E-CONDICAO-01 pelo playwright-cli, com screenshots examinadas. |

3/3 etapas executadas; 0 commits (fora do escopo autorizado).

## Arquivos e integração

- `apps/backend/src/garimpei/domain/listing/condition.py`, `condition_ports.py`: regra única, sinais, condição efetiva, aba e requisito de condição para F09.
- `usecase/listing/{read_condition_usecase,list_conditions_usecase,classify_condition_usecase}.py`: fronteiras de leitura e escrita por DI.
- `infra/queries/listing/condition_queries.py`, `infra/repository/listing/{condition_repository,condition_mapper}.py`: projeção consistente, precedência manual e persistência atômica.
- `infra/persistence/listing_models.py`, `models.py`, `migrations/0005_listing_manual_condition.py`: schema e descoberta ORM.
- `infra/http/listing/`, `infra/http/templates/listing/`, `infra/http/static/listing/`: adaptação do design Mineral e interação real.
- `main.py`, `infra/http/urls.py`, `infra/http/error_handler.py`: composição, rotas e tratamento central com códigos estruturados. O handler possui apenas `handle` como entrada pública.
- `config/{settings,test_settings}.py`: locale pt-BR consistente com a interface.
- `infra/http/templates/monitoring/layout.html`: entrada Ofertas na navegação existente.
- `quality/{entrypoints.json,vulture_whitelist.py}`: somente propriedades acessadas dinamicamente por templates e fronteiras públicas exercitadas; consumidores identificados.
- `tests/fixtures/listing/condition_cases.json`, `tests/factories/{listing,condition_http,condition_lab}.py`: dados e preparação reproduzíveis, sem controles de falha em produção.
- `tests/unit/test_listing_condition.py`, `tests/integration/test_listing_condition.py`, `tests/http/{test_listing_condition,test_condition_recovery}.py`: regras, integridade, concorrência, HTTP e falhas recuperáveis.

## Pré-requisitos produzidos

A fixture entrega as nove ofertas do contrato com IDs externos 501–509, origem facebook_marketplace, URL canônica, preço BRL e cobertura de envio confirmada. `ConditionSource` alimenta o worker real de F04, admite atualização e nova identidade e falha da fonte. `fail_next_condition_write` instala uma falha PostgreSQL de teste antes do commit; uma sequência não transacional prova sua ativação e permite a tentativa seguinte. Nenhum simulador é incluído na composição de produção.

Laboratório reproduzível: na pasta `apps/backend`, executar `uv run --frozen --no-sync python -m tests.factories.condition_lab`. O laboratório cria segredos privados, inicia `init.sh --disposable`, prepara F03 e coleta F04. Aceita uma ação JSON por linha: `status`, `update`, `collect`, `source_failure`, `fail`, `clear_fault`, `reset_choices`, `restart`, `quit`. Exemplo: `{"action":"update","key":"INCERTA_A","fields":{"description":"Não funciona."}}`, depois `{"action":"collect"}`. `fail` admite `delay` em segundos, abaixo do timeout do banco. `quit` executa a limpeza identificada da própria instância. O navegador usa a URL e os IDs impressos, sem credenciais.

## Verificação

- `node scripts/run-gates.mjs`: seis grupos PASS; tipos, lint/templates, limites, arquitetura, ciclos e não utilizados. [Saída](evidence/backend-gates.txt).
- `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests -q`: 172 PASS, 387,44 s. [Saída](evidence/python-tests.txt).
- Foco de domínio/recuperação: 14 PASS; HTTP completo: 1 PASS na execução focal. O avaliador executará novamente o conjunto F05 após os últimos ajustes de assinatura e reflow.
- Django check, makemigrations --check --dry-run, collectstatic e uv build: exit 0, [comandos e instantes](evidence/build-checks.json). Wheel inspecionada: migration, templates e estáticos de F05 incluídos.
- `node scripts/check-harness.mjs` e testes do harness: exit 0.
- Abas e detalhes exercitados pelo playwright-cli. Falhas HTTP 503 reais, POST 303, revisão antiga e elegibilidade 409, CSRF 403, entrada 400, ID 404 e método seguro não suportado 405. Métodos inseguros sem CSRF são rejeitados pelo middleware antes do handler.
- [Estado anterior](evidence/worker-before-restart.json) e [posterior ao reinício](evidence/worker-after-restart.json): mesma escolha manual defect/revisão 2, mesmos nove eventos. Nova tarefa de coleta técnica após reinício; nenhuma descoberta/redução por escolha/correção.
- F09 ainda não está implementada. A fronteira publicada foi exercitada: somente good satisfaz o requisito de condição, leitura indisponível retorna CONDITION_UNAVAILABLE. Envio/elegibilidade completa pertencem à F09 e não foram simulados.

## Pendências

Nenhum requisito de F05 conhecido permanece sem implementação. A aprovação canônica depende do relatório do avaliador. Fotos, filtros financeiros e envio WhatsApp pertencem às features consumidoras; a interface mantém o fallback explícito quando não há foto coletada.
