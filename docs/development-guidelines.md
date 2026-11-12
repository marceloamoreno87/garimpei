# Garimpei — diretrizes de desenvolvimento

Consulta das fontes: **10 de novembro de 2026**. Stack do produto: **Python/Django, templates/HTMX, PostgreSQL/Django ORM e worker Python separado**, sem Redis inicialmente. Documento preparado com a [skill development-guidelines](../.agents/skills/development-guidelines/SKILL.md), adaptação local da referência Full Cycle.

## 1. Status, autoridade e regras existentes

Este guia reúne regras vigentes e recomendações para a futura aplicação. Não aprova ferramentas, versões ou detalhes pendentes de arquitetura. A aplicação Python ainda não existe; F01–F09 continuam `pending`. Os protótipos e o Storybook de `docs/design/` são laboratório visual, não implementação Django.

As marcações abaixo valem também para exemplos e comandos da seção correspondente:

| Marcação | Significado |
|---|---|
| **Vigente** | Requisito ou regra já registrado nas fontes canônicas indicadas |
| **Proposta anterior** | Desenho já documentado em `docs/architecture/`, ainda sujeito à especificação/verificação |
| **Proposta nova** | Recomendação deste guia; deve ser decidida e incorporada ao contrato pertinente antes de virar obrigação |
| **Referência técnica** | Capacidade ou limitação confirmada na documentação oficial; não comprova integração executada |

O [AGENTS.md](../AGENTS.md), o [PRD](PRD.md), a [stack aprovada](stack.md) e as instruções atuais do usuário prevalecem. Os [ADRs](adrs/README.md) registram decisões de direção; a [arquitetura](architecture/README.md) distingue essas decisões de propostas de implementação. Este documento não modifica essas fontes.

| Regra vigente | Origem |
|---|---|
| `domain` ← `usecase` ← `infra`; DI por construtor, composição explícita e configuração central | AGENTS.md, seção Backend; [ADR-006](adrs/ADR-006-isolamento-regras-negocio.md) |
| Handlers validam entrada, chamam casos de uso e delegam erros ao tratamento central | AGENTS.md, seção Backend |
| Módulos pequenos, tipos explícitos, retornos antecipados, sem duplicação e sem mais de dois níveis de indentação | AGENTS.md, seção Backend |
| Evitar `any` | AGENTS.md, seção Backend; tradução Python proposta na seção 4 |
| Erros informam o valor problemático e o formato esperado, sem expor segredos | AGENTS.md, seção Backend |
| Testar regras de negócio e defeitos com testes significativos; fakes nomeados para I/O externo | AGENTS.md, seção Backend |
| Logs da aplicação em JSON; CLI em texto legível; segredos no ambiente | AGENTS.md, seções Backend e Arquivos |
| Todos os gates do contrato devem passar; ausente/não executado permanece pendente | AGENTS.md; PRD F02-AC03 |
| Isolar ambientes/portas, manter prefixo `garimpei_` e preservar dados/sessão na parada normal | Stack; PRD F02-AC02 |
| Verificar jornadas com `playwright-cli`; usar o design de `docs/design/` e avaliação visual prevista | AGENTS.md, seção Frontend |

## 2. Stack e referências de versão

**Vigente:** Django serve páginas e fragmentos HTML com HTMX; PostgreSQL guarda dados e tarefas persistentes; web e worker compartilham código e banco. Aplicação/worker rodam no Linux/WSL2; PostgreSQL e WAHA, em Docker. Acesso somente deste computador, via localhost, sem login no Garimpei. Node atende ao harness/laboratório existente. [Stack aprovada](stack.md).

**Referência técnica:** versões observadas nas fontes oficiais na data da consulta, sem fixá-las como versões do projeto:

| Componente | Referência consultada | Consequência para F02 |
|---|---|---|
| Python | 3.15.2 estável; séries 3.14 e 3.13 também mantidas, em fases diferentes | Escolher versão compatível com Django, driver, fila e ferramentas; usar patch mantido. [Downloads oficiais](https://www.python.org/downloads/) |
| Django | 6.1.3 é a versão oficial mais recente; 5.2.19 é o patch observado da série 5.2 LTS, com suporte estendido até abril de 2028 | Os exemplos usam APIs documentadas em 5.2 LTS; isso não elege a série do produto. [Downloads/suporte](https://www.djangoproject.com/download/) |
| Compatibilidade Python/Django | A documentação 5.2 inclui Python 3.10–3.14; suporte a 3.14 entrou em 5.2.8 | Não combinar automaticamente Django 5.2 com o Python mais recente. [Matriz oficial](https://docs.djangoproject.com/en/5.2/faq/install/#what-python-version-can-i-use-with-django) |
| PostgreSQL | Política consultada lista 18.6 e 17.11 como versões mantidas | Fixar major/patch e imagem compatíveis com recursos locais, driver e fila; planejar atualização do volume. [Versionamento oficial](https://www.postgresql.org/support/versioning/) |
| HTMX | Documentação consultada apresenta 2.0.11 | Fixar o asset e verificar comportamento de respostas/fragmentos na versão escolhida. [Documentação oficial](https://htmx.org/docs/) |
| WAHA | Componente aprovado; engine, imagem, sessão e destinatário ainda pendentes | F01 valida recursos/compatibilidade; F09 especifica envio e reconciliação. [Pendências canônicas](PRD.md#pendências-de-descoberta-e-especificação) |

**Proposta nova:** escolher uma combinação mantida e verificável, registrando versões exatas no manifesto/lock e imagens por versão/digest. Uma atualização deste guia não deve atualizar dependências automaticamente. Procrastinate continua **candidato**, conforme a stack, até prova da integração.

Os exemplos Python pressupõem Python 3.12+; os exemplos Django usam APIs da série 5.2. São recortes didáticos, sem scaffold do produto ou escolha de suas versões.

## 3. Organização e dependências entre módulos

**Vigente:** regras de negócio independem de Django, ORM, fila e rede. Antes de implementar backend, ler a [skill clean-arch](../.agents/skills/clean-arch/SKILL.md).

**Proposta anterior:** seguir o desenho de [organização e dependências](architecture/organizacao-e-dependencias.md), sem criar arquivos vazios para preencher o diagrama:

```text
apps/backend/
  manage.py
  pyproject.toml
  src/garimpei/
    main.py                  # composição explícita de web/worker
    config/                  # env.py, settings e entrada WSGI/ASGI
    domain/                  # monitoring, listing, valuation, alert
    usecase/                 # ações e DTOs; depende de domain
    infra/
      http/                  # rotas, handlers, erros, templates, static
      persistence/           # aplicação Django, modelos e migrations
      repository/            # escrita/restauração de entidades
      queries/               # projeções tipadas de leitura
      gateway/               # fonte, WAHA e outros adapters
      worker/                # tarefas e adaptação da fila
  tests/                     # organização detalhada proposta em F02
```

**Proposta anterior:** contratos ficam no domínio; casos de uso recebem adapters por construtor. Repositórios de escrita devolvem entidades; consultas devolvem projeções tipadas. Templates recebem DTOs, sem entidades ORM ou `QuerySet` lazy. `main.py` constrói o grafo; camadas internas não consultam service locator nem ambiente.

**Referência técnica:** modelos precisam estar definidos ou importados no módulo `models` da aplicação registrada. O `models.py` de persistência pode registrar explicitamente os modelos distribuídos entre features. Não executar queries, coleta, envio ou iniciar worker em importações ou `AppConfig.ready()`. Esse hook também participa de comandos administrativos. [Registro/inicialização Django](https://docs.djangoproject.com/en/5.2/ref/applications/).

**Proposta nova:** testes espelham as camadas em `tests/unit/`, `tests/integration/` e `tests/http/`; evidências de jornadas ficam junto da feature responsável. Imports absolutos de módulos concretos favorecem fiscalização dos limites. Exceções de registro do framework devem ser pontuais e justificadas.

## 4. Estilo, tipos e funções

**Vigente:** funções pequenas, retornos antecipados, tipos explícitos e comentários que expliquem motivos. Nomes do produto seguem [CONTEXT.md](../CONTEXT.md).

**Proposta nova:** usar quatro espaços; `snake_case` em módulos/funções/variáveis, `PascalCase` em classes e `UPPER_CASE` em constantes. Manter nomes de código em inglês conforme a proposta de arquitetura e textos de interface em português. Definir largura/formatter em F02, em vez de misturar estilos. [PEP 8](https://peps.python.org/pep-0008/).

**Referência técnica:** anotações Python não validam valores em execução; `Any` permite operações sem a verificação correspondente, enquanto `object` exige refinamento. [Typing/Protocol](https://docs.python.org/3/library/typing.html). **Proposta nova:** traduzir a regra de evitar `any` como evitar `typing.Any` autoral e conter tipagem dinâmica nas fronteiras. Usar `Protocol` para portas estruturais úteis, `dataclass` para estruturas apropriadas e `Decimal | None` para valor possivelmente indisponível. Não esconder erros com `cast` ou ignores amplos.

**Proposta anterior:** representar dinheiro com `Decimal`, construído de texto/valor decimal, sem passar por `float`. Escala, moeda, precisão e arredondamento continuam em P08. A fórmula abaixo apenas ilustra F07 com entradas já validadas, sem escolher arredondamento nem cobrir todos os custos futuros. [Decimal](https://docs.python.org/3/library/decimal.html).

```python
from decimal import Decimal


def estimate_profit(
    resale: Decimal | None,
    *,
    purchase: Decimal,
    shipping: Decimal,
    fee_percent: Decimal,
) -> Decimal | None:
    if resale is None:
        return None
    fee = resale * fee_percent / Decimal("100")
    return resale - purchase - shipping - fee
```

**Vigente — PRD F06/F07:** indisponível não vira zero; lucros calculáveis iguais a zero ou negativos não são descartados. Evitar `if not resale` ou `resale or 0`, que confundem ausência com valor numérico. O frete informado prevalece sobre o estimado configurado; esse critério deve ser aplicado antes da função.

## 5. Validação de entrada e invariantes

**Vigente:** validar formato na entrada HTTP/worker, invariantes no domínio e regras que exigem estado no caso de uso. O mesmo caso de uso atende web e worker sem depender de um formulário Django.

**Proposta nova:** usar Forms Django para conversão e erros de campos da interface. Em F03, nome/modelo vazio deve falhar; não exigir atributos extras. Exemplo de infraestrutura, sem persistência:

```python
from django import forms


class ProductNameForm(forms.Form):
    name_model = forms.CharField(label="Nome/modelo", strip=True)
```

`is_valid()` preenche `cleaned_data` ou `errors`; somente dados validados seguem para DTOs tipados. Form não substitui invariantes nem consulta remota de negócio. [Validação de forms](https://docs.djangoproject.com/en/5.2/ref/forms/validation/).

**Referência técnica:** `Model.save()` não chama `full_clean()` automaticamente. `full_clean()` pode validar campos/regras de modelo, mas não substitui constraints nem resolve corridas. Bulk operations também exigem cuidado com os hooks que deixam de executar. [Validação de modelos](https://docs.djangoproject.com/en/5.2/ref/models/instances/#validating-objects).

**Proposta nova:** definir limites de comprimento/tamanho dos payloads nos contratos; rejeitar números não finitos e representar dinheiro/timestamps em formato explícito nas fronteiras. Validar esquema e versão do payload de tarefa antes de chamar o caso de uso. Respostas externas incompletas permanecem parciais ou falhas, nunca ofertas/preços fabricados.

**Vigente — PRD F03:** frete estimado e percentual começam em branco e são preenchidos pelo usuário; exemplos e fixtures não viram defaults de negócio. Critérios de amostra, identidade de republicação e arredondamento ainda precisam das decisões correspondentes.

## 6. Erros e tratamento central

**Vigente:** handlers delegam erros ao tratamento central. Não capturar `Exception` em cada camada, devolver sucesso após falha nem registrar credenciais. Mensagens identificam o campo/valor público problemático e o esperado; para segredos, informar apenas nome e estado ausente/inválido.

**Proposta nova:** exceções de domínio não conhecem HTTP; adapters traduzem falhas de bibliotecas para erros estáveis e preservam a causa com `raise ... from exc` quando aplicável. A borda registra uma vez o diagnóstico sanitizado. Exemplo puro para a regra de nome obrigatório de F03:

```python
class InvalidProductName(ValueError):
    pass


def require_product_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise InvalidProductName(
            f"Nome/modelo {value!r} inválido; esperado texto não vazio."
        )
    return cleaned
```

**Proposta nova:** adaptar as categorias abaixo no tratamento central de HTTP e de tarefas. Os códigos HTTP são convenções propostas, não contratos já aprovados:

| Situação | HTTP proposto | Resultado/tarefa |
|---|---|---|
| Entrada de formulário inválida | 422 com fragmento de erros, após configurar HTMX | Não executar caso de uso com dados inválidos |
| Recurso inexistente | 404 | Erro conhecido; política de descarte/recuperação no contrato |
| Conflito de estado/concorrência | 409 | Reconciliar; não repetir gravação cegamente |
| Dependência temporariamente indisponível | 503 | Retentativa limitada apenas se segura |
| Defeito inesperado | 500, mensagem pública genérica e ID de correlação | Falha visível; sem transformar em lista vazia |
| Timeout após envio ao WAHA | Estado público de confirmação incerta | Não marcar como enviado nem presumir que falhou antes de enviar |

No exemplo, `repr` é apropriado apenas para o campo público limitado pelo contrato. Não interpolar payloads/URLs autenticadas em mensagens genéricas. Falhas de validação não precisam de stack trace; defeitos precisam de diagnóstico técnico sanitizado. [Exceções Python e encadeamento](https://docs.python.org/3/tutorial/errors.html).

## 7. Configuração e segredos

**Vigente:** configuração central, segredos no ambiente e nenhuma credencial em relatórios. Ausência de configuração obrigatória impede declarar inicialização bem-sucedida, conforme F02-AC04.

**Proposta anterior:** somente `config/env.py` acessa o ambiente autoral. Settings/bootstrap usam os valores centrais e a composição os injeta nos adapters. Nenhum caso de uso importa settings.

**Proposta nova:** usar configuração tipada por processo/capacidade; `.env.example` contém somente nomes e exemplos não secretos. Não carregar `.env` por toda a aplicação. Um helper possível, restrito a `config/env.py`, é:

```python
import os


class ConfigurationError(ValueError):
    pass


def required_secret(name: str) -> str:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise ConfigurationError(
            f"{name}: valor ausente/vazio; esperado segredo não vazio."
        )
    return value
```

A leitura ocorre ao chamar o bootstrap, sem executar o helper em importação. Não incluir o valor recebido no erro. Fazer parsing explícito de booleanos, portas, URLs, durações e níveis de log; `bool("false")` é verdadeiro. [Ambiente Python](https://docs.python.org/3/library/os.html#os.environ).

**Proposta nova:** separar configuração técnica de interesses/custos persistidos pelo usuário. Validar conexão do banco e chaves necessárias ao processo; comandos sem I/O de mensageria não devem exigir uma sessão WhatsApp real. Inventário mínimo para F02: identidade do ambiente, bind/portas, banco, secret key Django, nível de log e capacidades habilitadas. Parâmetros de coleta/envio aguardam F01/F04/F09.

## 8. Persistência, transações e migrations

**Vigente:** PostgreSQL com Django ORM/migrations. ORM fica na infraestrutura; invariantes e entidades não herdam de `Model`.

**Proposta anterior:** unit of work define a fronteira de escrita; transação e mappers são adapters Django. **Proposta nova:** usar `transaction.atomic()` em trechos curtos, fora de chamadas à plataforma/WAHA. Tratar `IntegrityError` ao sair do bloco que reverte a escrita, sem continuar consultando uma transação quebrada. [Transações Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).

Exemplo de escopo transacional de infraestrutura; o callback representa uma escrita já definida pelo contrato:

```python
from collections.abc import Callable

from django.db import transaction


def run_atomic(write: Callable[[], None]) -> None:
    with transaction.atomic():
        write()
```

**Proposta nova:** preferir ORM; quando SQL for necessário, parametrizar valores e manter identificadores em uma lista permitida. Não concatenar entrada nem colocar aspas ao redor de `%s`. Exemplo independente do schema, para verificar binding de valor:

```python
from django.db import connection


def echo_database_value(value: str) -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT %s", [value])
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Consulta sem resultado; esperada uma linha.")
    return str(row[0])
```

O cursor é fechado pelo context manager; a conexão é gerenciada pelo Django. Não usar esse exemplo como healthcheck de produção. [SQL parametrizado Django](https://docs.djangoproject.com/en/5.2/topics/db/sql/).

**Proposta nova:** constraints/índices devem refletir invariantes e consultas reais. Testar transações, unicidade e locking em PostgreSQL, com conexões distintas nos cenários concorrentes. Não usar SQLite como evidência de equivalência de fila/concorrência. Paginação e ordenação acontecem antes da renderização; joins/projeções evitam N+1 conforme medições.

**Referência técnica:** Django 5.2 suporta PostgreSQL 14+ e recomenda Psycopg 3, com mínimos próprios de versão. `CONN_MAX_AGE` não é configuração de pool; em ASGI, conexões persistentes devem ser desabilitadas segundo a documentação. Dimensionar conexões de web e worker junto da fila; processos longos precisam tratar conexões envelhecidas. [Backend PostgreSQL e conexões](https://docs.djangoproject.com/en/5.2/ref/databases/).

**Proposta nova:** versionar migrations revisadas; checar drift, plano e aplicação em banco descartável, inclusive sequência com a fila. Testar instalação sem dados pré-existentes. Não fazer rollback destrutivo automático de schema nem apagar volume para esconder migration quebrada. Backup/restauração e upgrade de major precisam de procedimentos verificáveis em F02.

## 9. Worker, concorrência e efeitos externos

**Vigente:** worker separado, tarefas persistentes no PostgreSQL e funcionamento independente de aba aberta. Marco inicial, identidades e eventos sobrevivem a reinícios; carga inicial não envia alertas. Classificação manual não gera alerta nem pendência de envio. [PRD F04/F05/F09](PRD.md).

**Proposta anterior:** persistir intenção/evento antes do efeito externo; transportar identificadores em payloads pequenos, revalidando estado ao executar. Excluir rede de transações longas. Distinguir evento novo, redução de preço e repetição do mesmo evento. [Fluxos de confiabilidade](architecture/dados-fluxos-e-confiabilidade.md).

**Referência técnica:** `on_commit()` evita disparar antes do commit, mas o callback executa depois e sua falha não reverte os dados. Há uma janela entre commit e enfileiramento; usar esse hook sozinho não garante trabalho durável. Para gravação e tarefa atômicas, avaliar mesma conexão/transação comprovada ou outbox persistente. O Procrastinate documenta conexão externa, mas a compatibilidade concreta com Django ainda precisa de teste. [Callbacks Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/#performing-actions-after-commit), [conexão externa Procrastinate](https://procrastinate.readthedocs.io/en/stable/howto/production/external_connection.html).

**Proposta nova:** definir timeouts de conexão/leitura/execução, concorrência limitada e tentativas com backoff, teto e classificação de erros. Falha permanente de validação não deve entrar em loop. Intervalos, limites e política de reconciliação permanecem em P09; não adotar valores arbitrários neste guia.

**Proposta nova:** testar claim concorrente, queda após gravação, queda após chamada externa e parada graciosa. Uma constraint local pode impedir intenção duplicada; não garante entrega exatamente uma vez ao WhatsApp. Timeout após o pedido pode deixar envio incerto; persistir essa condição e reconciliar conforme contrato de F09. Repetir automaticamente nesse caso pode duplicar mensagem.

**Referência técnica:** Procrastinate oferece integração Django, registro de tarefas e migrations; isso não aprova sua adoção nem substitui a composição e os testes do produto. [Integração oficial](https://procrastinate.readthedocs.io/en/stable/howto/django/configuration.html).

## 10. Templates, HTMX e segurança local

**Vigente:** respeitar as jornadas e estados do [design](design/README.md), sem confirmar gravação que falhou. Em F08, novos dados geram aviso e só atualizam a lista ao clicar, preservando filtros; ordenação/paginação seguem o PRD.

**Proposta nova:** compartilhar templates/partials entre página completa e resposta HTMX; usar HTML semântico, labels, foco e erros associados aos campos. Oferecer envio HTML normal quando viável. Não interpolar HTML de anúncios como confiável nem aplicar `safe` a entrada externa.

Exemplo de partial proposto, incluindo CSRF como campo do formulário. Pressupõe uma rota chamada `product-create`, contexto com `form` e HTMX carregado; não cria essa rota:

```html
<div id="product-form">
  <form method="post" action="{% url 'product-create' %}"
        hx-post="{% url 'product-create' %}"
        hx-target="#product-form" hx-swap="outerHTML">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Adicionar produto</button>
  </form>
</div>
```

**Referência técnica:** o padrão HTMX 2.x não troca o conteúdo para respostas 4xx/5xx. A proposta 422 da seção 6 requer regra específica em `responseHandling` ou handler equivalente; falhas 409/503 também precisam de apresentação explícita. Não habilitar swap indiscriminado de qualquer erro. Usar CSRF nos POSTs; requisições fora de formulários devem enviar o token pelo mecanismo documentado. [Respostas e CSRF no HTMX](https://htmx.org/docs/).

**Proposta anterior:** bind local para aplicação e portas publicadas dos serviços, hosts explícitos e proteção de operações mutáveis. **Proposta nova:** `ALLOWED_HOSTS` sem curinga, CSRF ativo e GET sem mutação; considerar `Vary: HX-Request` se página e partial compartilharem URL e cache. Tratar URLs de anúncio como entrada externa e permitir apenas esquemas esperados.

Ausência de login é escopo aprovado, não autorização para expor serviços na rede. Proteções de cookies/HTTPS devem acompanhar o ambiente real: HTTP de desenvolvimento local não deve receber configurações incompatíveis copiadas de produção. A configuração de segurança do WAHA é independente do login do produto. [Checklist Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [segurança WAHA](https://waha.devlike.pro/docs/how-to/security/).

## 11. Logs e diagnóstico

**Vigente:** aplicação emite JSON estruturado; scripts/CLI apresentam texto legível. Segredos, cookies, sessão WAHA e credenciais ficam fora de logs/evidências.

**Proposta anterior:** correlacionar tarefa, coleta, anúncio/evento e tentativa de alerta. **Proposta nova:** incluir timestamp UTC, nível, logger, evento estável e IDs internos opcionais; usar allowlist de campos. Não registrar telefone, conteúdo integral de anúncio, corpo de mensagens ou exceção externa bruta.

Exemplo independente usando `logging` da biblioteca padrão; os textos de evento e os IDs abaixo são fictícios e não carregam dados externos:

```python
import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        fields = ("run_id", "job_id", "listing_id", "error_code")
        payload.update(
            {key: record.__dict__[key] for key in fields if key in record.__dict__}
        )
        return json.dumps(payload, ensure_ascii=False)


def configure_example_logger(level: int) -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("garimpei.example")
    logger.handlers[:] = [handler]
    logger.propagate = False
    logger.setLevel(level)
    return logger


logger = configure_example_logger(logging.INFO)
logger.info("collection.started", extra={"run_id": "example-run"})
```

O exemplo demonstra formatter e contexto; não sanitiza texto arbitrário nem configura todos os loggers do produto. A configuração real deve ocorrer uma vez no bootstrap, pelo `LOGGING` do Django e equivalente do worker, incluindo bibliotecas sem duplicar handlers. [Logging Python](https://docs.python.org/3/library/logging.html), [logging Django](https://docs.djangoproject.com/en/5.2/howto/logging/).

**Proposta nova:** DEBUG para diagnóstico local, INFO para transições normais, WARNING para degradação recuperável, ERROR para operação falha e CRITICAL para processo incapaz de continuar. Registrar código/tipo de erro e stack sanitizada quando necessária, sem despejar `exc_info` com segredos. Definir retenção/rotação; acompanhar duração de coleta, atraso/quantidade da fila e falhas de envio com baixa cardinalidade. Não adicionar stack de observabilidade antes de necessidade demonstrada.

## 12. Testes e evidências

**Vigente:** cobrir regras e defeitos com cenários significativos e fakes nomeados. Jornadas de navegador usam a [skill playwright-cli](../.agents/skills/playwright-cli/SKILL.md). Cada feature conserva evidências junto de sua especificação.

**Proposta nova:** iniciar com `unittest` e runner Django, reduzindo dependências adicionais; `coverage.py` é candidato para medição de branches. Pytest não está adotado por este guia. Evitar testar detalhes privados ou replicar o algoritmo no teste.

O bloco abaixo pode acompanhar a função `estimate_profit` no mesmo arquivo temporário. Os valores são fixtures, não parâmetros padrão do usuário:

```python
import unittest
from decimal import Decimal


def profit_for_fixture(resale: Decimal | None) -> Decimal | None:
    return estimate_profit(
        resale,
        purchase=Decimal("80"),
        shipping=Decimal("10"),
        fee_percent=Decimal("10"),
    )


class ProfitEstimateTest(unittest.TestCase):
    def test_preserves_unavailable_estimate(self) -> None:
        self.assertIsNone(profit_for_fixture(None))

    def test_preserves_zero_profit(self) -> None:
        self.assertEqual(profit_for_fixture(Decimal("100")), Decimal("0"))

    def test_preserves_negative_profit(self) -> None:
        self.assertEqual(profit_for_fixture(Decimal("90")), Decimal("-9"))
```

Esses testes protegem a distinção observável entre indisponibilidade, zero e negativo, de F06/F07. Não validam política de amostra ou arredondamento. [Asserções unittest](https://docs.python.org/3/library/unittest.html#assert-methods).

| Camada/cenário | Estratégia proposta e requisito a proteger |
|---|---|
| Domínio e casos de uso | Sem Django/banco; fakes nomeados de fonte/WAHA, relógio controlado, erros e ausências explícitos |
| Persistência | `TestCase` sobre PostgreSQL isolado para repositórios, consultas, constraints e migrations |
| Commit/rollback/locking reais | `TransactionTestCase` e conexões independentes quando necessários; `TestCase` envolve o teste em transação |
| Callbacks de commit | `captureOnCommitCallbacks(execute=True)` para callbacks em `TestCase`; teste separado da garantia durável da fila |
| HTTP e HTMX | Client Django: resposta completa/partial, payload inválido, falha de gravação e CSRF; usar `enforce_csrf_checks=True` para verificar proteção |
| Worker/fila | Reinício, evento repetido, claim concorrente e queda em pontos de falha; WAHA fake na rotina de testes |
| Navegador | Configuração inicial, três abas, detalhes, classificação que falha/salva e atualização ao clicar; evidências de foco/erros e responsividade |

As APIs de teste acima constam das [ferramentas oficiais Django](https://docs.djangoproject.com/en/5.2/topics/testing/tools/). Integração real com fonte/WAHA exige escopo específico; a suíte comum não deve enviar mensagens reais como efeito colateral. F02 ainda deve definir testes vazios como falha e a descoberta correta dos testes de cada camada.

## 13. Dependências e ferramentas candidatas

**Proposta nova:** preferir biblioteca padrão quando atender à necessidade; declarar dependências diretas e separar runtime de desenvolvimento. Usar `pyproject.toml` como manifesto, com um único gerenciador/lock reproduzível, a decidir em F02. [Guia oficial PyPA](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).

Versões abaixo são metadados observados no **PyPI em 10/11/2026**, não um conjunto aprovado ou testado em conjunto. Os links identificam as distribuições consultadas; F02 precisa escolher versões mutuamente compatíveis, sobretudo para stubs/plugins Django.

| Distribuição | Versão observada | Finalidade e status |
|---|---|---|
| [psycopg](https://pypi.org/project/psycopg/) | 3.3.8 | Driver PostgreSQL proposto; dependência da implementação ORM/fila |
| [procrastinate](https://pypi.org/project/procrastinate/) | 3.10.0 | Candidato já citado na stack para tarefas persistentes |
| [uv](https://pypi.org/project/uv/) | 0.13.7 | Nova proposta para ambiente, resolução e lock |
| [ruff](https://pypi.org/project/ruff/) | 0.17.4 | Nova proposta para lint e formatação |
| [mypy](https://pypi.org/project/mypy/) | 2.4.1 | Nova proposta para tipos Python |
| [django-stubs](https://pypi.org/project/django-stubs/) | 6.1.2 | Candidato complementar; escolher pela matriz de Django/mypy, não pelo número mais recente |
| [coverage](https://pypi.org/project/coverage/) | 7.17.2 | Nova proposta para medir cobertura de linhas/branches |
| [import-linter](https://pypi.org/project/import-linter/) | 2.16 | Nova proposta para contratos de imports e análise de ciclos |
| [vulture](https://pypi.org/project/vulture/) | 2.16 | Nova proposta para localizar código possivelmente não utilizado |
| [deptry](https://pypi.org/project/deptry/) | 0.25.1 | Nova proposta para dependências ausentes/não utilizadas/mal declaradas |
| [pip-audit](https://pypi.org/project/pip-audit/) | 2.10.1 | Nova proposta para vulnerabilidades conhecidas em dependências resolvidas |

**Proposta nova:** para cada inclusão, registrar necessidade, compatibilidade, licença, manutenção, dependências transitivas e efeito operacional. Não instalar SDK de coleta antes de F01 nem Redis/Celery por default. Para HTMX, avaliar asset local versionado servido pelo Django, com licença/origem registradas, evitando exigir bundler de aplicação.

**Proposta nova:** versionar o lock e revisá-lo junto do manifesto; manter ambiente de execução enxuto. Atualizações precisam de changelog, nova resolução e verificações relevantes. Auditoria de vulnerabilidades conhecidas não comprova ausência de falhas; erro de consulta da auditoria deve aparecer como verificação pendente/falha, nunca aprovação. [pip-audit oficial](https://github.com/pypa/pip-audit).

## 14. Gates e comandos de referência

**Vigente:** F02-AC03 exige tipos, lint, limites de dependências, arquitetura, ciclos, código/dependências não utilizados e testes aplicáveis. Os gates TypeScript preservados não validam Python. O contrato de F02 precisa definir comandos executáveis, cobertura e evidência antes de concluir a fundação.

**Proposta nova:** o conjunto abaixo é uma base a especificar, não um runner instalado. Comandos Python assumem `apps/backend/` como diretório atual, pacote `garimpei` instalado, `src/` e `tests/` criados e ferramentas configuradas. `uv` assume manifesto, lock e grupo dev contendo as ferramentas. Não executar esses comandos agora como se houvesse aplicação.

| Cobertura | Comando candidato | Limite/condição |
|---|---|---|
| Lock/ambiente | `uv sync --locked --group dev` | Falhar se lock exigir atualização; não resolver silenciosamente em validação |
| Formatação | `uv run --locked ruff format --check .` | Escopo/exclusões definidos no manifesto |
| Lint | `uv run --locked ruff check .` | Lint não substitui tipos/arquitetura |
| Tipos | `uv run --locked mypy src tests` | Configurar Django/stubs e proibir ignores amplos |
| Limites de imports | `uv run --locked lint-imports` | Exige contratos: camadas e I/O proibido no núcleo |
| Ciclos | Mesmo analisador, com contratos específicos | Camadas sozinhas não rejeitam ciclos entre irmãos; cobrir todos os pacotes autorais |
| Arquitetura/configuração/DI | Verificador Python autoral a implementar em F02 | Ainda sem comando aprovado; inclui leituras de ambiente, composição e convenções |
| Código não utilizado | `uv run --locked vulture src tests` | Ajustar registros Django e whitelist pontual revisada; não excluir toda a infraestrutura |
| Dependências não utilizadas | `uv run --locked deptry .` | Declarar imports dinâmicos/entradas Django e dependências de desenvolvimento corretamente |
| Testes unitários | `uv run --locked python -m unittest discover -s tests/unit -v` | Sem bootstrap Django; runner deve rejeitar zero testes |
| Testes Django | `uv run --locked python manage.py test --verbosity 2` | Descoberta de testes e banco de testes PostgreSQL isolado configurados |
| Cobertura | `uv run --locked coverage run --branch manage.py test` | Complementar unitários se o runner Django não os descobrir; não mede worker externo automaticamente |
| Relatório de cobertura | `uv run --locked coverage report -m` | Limiar depende do contrato; não importar os 70% do template como regra aprovada |
| Verificações Django | `uv run --locked python manage.py check` | Não substitui regras de arquitetura nem prontidão real |
| Drift de migrations | `uv run --locked python manage.py makemigrations --check --dry-run` | Exige configuração Django funcional |
| Plano de migrations | `uv run --locked python manage.py migrate --plan` | Rever plano antes de aplicar ao banco identificado |
| Auditoria de dependências | `uv run --locked pip-audit` | Audita o ambiente sincronizado; falhas precisam de tratamento explícito |

Sintaxes consultadas: [uv lock/sync](https://docs.astral.sh/uv/concepts/projects/sync/), [Ruff](https://docs.astral.sh/ruff/), [mypy](https://mypy.readthedocs.io/en/stable/running_mypy.html), [Import Linter e contratos](https://import-linter.readthedocs.io/en/stable/), [Vulture](https://github.com/jendrikseipp/vulture), [deptry](https://deptry.com/usage/), [coverage run](https://coverage.readthedocs.io/en/latest/commands/cmd_run.html), [comandos Django](https://docs.djangoproject.com/en/5.2/ref/django-admin/).

**Proposta nova:** validar os validadores com violações representativas: import de Django no domínio, leitura de ambiente em caso de uso, ciclo entre módulos, símbolo não usado, dependência direta ausente e zero testes. Contratos de imports precisam incluir módulos externos quando necessários. Análise estática não prova ausência de I/O indireto nem imports dinâmicos; complementar com inspeção e testes de bootstrap. Falha não vira warning para permitir conclusão.

**Vigente:** comandos que já existem na raiz para verificar apenas o harness:

```bash
node --test scripts/test/harness.test.mjs
node scripts/check-harness.mjs
```

Esses comandos não aprovam F02, o backend, a fila ou jornadas da aplicação.

## 15. Ambiente, recursos e desempenho

**Vigente:** usar `./scripts/init.sh` antes de trabalho que precise da aplicação e `./scripts/stop.sh` para encerrar processos próprios. Antes do scaffold, init apenas informa preparação. A adaptação Python, readiness e migrations ainda pertencem a F02. Preservar prefixo `garimpei_`, portas isoladas, dados e sessão WAHA; limpeza descartável depende de escopo autorizado. [Harness atual](harness.md).

**Proposta anterior:** web, worker, banco e serviços previstos têm readiness própria; porta aberta não prova propriedade nem saúde. A web disponível não comprova que alertas estão sendo processados. Recursos obrigatórios ausentes impedem anunciar ambiente integralmente pronto. Testar parada/reinício sem perda de estado.

**Proposta nova:** evitar contêineres da aplicação como exigência nova: a operação aprovada mantém Python no WSL2 e serviços em Docker. Não copiar o Dockerfile genérico do template Full Cycle. Fixar imagens/volumes em F02 após avaliar recursos em F01; não escolher Alpine ou `latest` automaticamente.

**Proposta nova:** medir antes de otimizar: quantidade/duração de queries, latência de página, atraso da fila e custo da coleta. Usar perfis locais sanitizados; limitar lotes/concorrência conforme memória e banco. `cProfile`/`tracemalloc` são opções nativas, sem nova infraestrutura obrigatória. [Profiling Python](https://docs.python.org/3/library/profile.html), [memória](https://docs.python.org/3/library/tracemalloc.html).

Carga/benchmarks entram quando uma hipótese ou critério de aceite exigir, com dados sintéticos e sem disparar alertas reais. Não há orçamento numérico de latência/throughput aprovado. Async, threads, polling, SSE e WebSocket não são escolhidos apenas por suporte da linguagem/framework; mecanismo e frequência continuam nas pendências do produto.

## 16. Revisão, pendências e fontes

Checklist para especificar/implementar uma feature, combinando regras vigentes com os controles propostos identificados acima:

- [ ] Confirmar PRD, contrato, dependências e decisões pendentes; não transformar sugestão em regra aprovada.
- [ ] Manter domínio/casos de uso sem framework/I/O, composição explícita e configuração central.
- [ ] Validar formatos/invariantes; distinguir ausente, zero, falha e resultado incerto.
- [ ] Rever tratamento central, valores públicos nos erros e ausência de segredos nos logs.
- [ ] Confirmar transações, constraints, migrations e recuperabilidade dos efeitos envolvidos.
- [ ] Testar regra/defeito e integrações necessárias com fakes nomeados e PostgreSQL isolado onde aplicável.
- [ ] Verificar estados de interface/jornadas com evidência quando a feature incluir UI.
- [ ] Executar todos os gates definidos, registrar saída/códigos e manter pendente o que não foi verificado.
- [ ] Atualizar artefatos da feature sem alterar estados de implementação por aprovação documental.

**Pendências preservadas:** F01 esclarece fonte, acesso, recursos e WAHA; arquitetura/F02 escolhem versões, servidor WSGI/ASGI, gerenciador, ferramentas, organização final e biblioteca de tarefas. F04/F09 fecham intervalos, concorrência, tentativas e reconciliação; F06/F07 fecham amostragem/precisão/arredondamento conforme P07/P08. Nenhum exemplo resolve essas escolhas por default.

**Adaptação da referência Full Cycle:** incluídos organização, estilo/tipos/funções, erros, configuração, banco, logs, testes, dependências, concorrência e diagnóstico no contexto real da stack. Docker limita-se à operação aprovada; carga e benchmarks são condicionais. Contagens de linhas/exemplos, cobertura de 70%, instalação automática de ferramentas e defaults genéricos não se tornam regras do Garimpei. Não foram adotadas estruturas de projetos de terceiros como autoridade arquitetural.

As fontes oficiais estão vinculadas junto das afirmações e comandos. A consulta utilizou também Context7 para Python, Django e HTMX; documentação versionada e páginas oficiais foram usadas para confirmar APIs e suporte. Fontes locais de requisitos/decisões são [AGENTS.md](../AGENTS.md), [PRD](PRD.md), [stack](stack.md), [arquitetura](architecture/README.md), [ADRs](adrs/README.md), [vocabulário](../CONTEXT.md), [design](design/README.md) e [harness](harness.md). Documentação oficial comprova APIs, não testes de integração já realizados no produto.

**Verificação desta entrega documental:** os oito blocos Python tiveram sintaxe verificada e execução em ambiente temporário com Python 3.12.13/Django 5.2.19. Passaram os três testes de lucro e verificações de nome inválido, configuração ausente, allowlist JSON, form e renderização do template. Os exemplos de binding SQL e commit/rollback foram exercitados somente em SQLite em memória para conferir a API Django, sem equivalência presumida com PostgreSQL. Integração PostgreSQL/fila/WAHA, comportamento HTMX no navegador e gates da aplicação permanecem sem execução nesta entrega. Links locais foram conferidos; AGENTS.md, PRD, stack e progresso foram preservados.
