# Contract — F10 Configurações de integrações

## Prerequisites

### Runtime services
- Instância F02 eval descartável com PostgreSQL/web/worker por scripts próprios; WAHA HTTP programável para sessões/QR/grupos/recibos. Instância dev do usuário preservada.
### Persistent state
- Migrations 0001–0008 e nova migration aditiva; configuração F03 e coletas F04. F09 com intenções anteriores para provar vínculo fixo.
### Static inputs
- Cookies sintéticos header/JSON com c_user/xs, vencidos, inválidos e domínio alheio. Sessão WAHA desligada, QR sintético, WORKING, grupos normais e GOWS, conta alterada.
### Configuration
- Arquivo privado de avaliação e diretório externo exclusivo de credenciais; URLs de fixture só em eval. Nenhum cookie/chave/QR real em evidências.
### External dependencies
- Pareamento real depende do usuário escanear QR e fornecer cookies válidos na UI. Não enviar mensagens a destinatários reais na avaliação automática.

## Quality gates

- Seis gates: `node scripts/run-gates.mjs`.
- Python/PostgreSQL: `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests`.
- Django: `DJANGO_SETTINGS_MODULE=garimpei.config.test_settings uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py check`.
- Migrations: mesmo ambiente, `manage.py makemigrations --check --dry-run`.

## Coverage Manifest

| AC | Itens |
|---|---|
| F10-AC01 — Configuração de cookies no menu | HTTP-COOKIES-01, UI-INTEGRACOES-01 |
| F10-AC02 — Aviso e renovação de acesso | WRK-ACESSO-01, WRK-ACESSO-02 |
| F10-AC03 — Conexão WhatsApp por QR | HTTP-WHATSAPP-01, UI-INTEGRACOES-01 |
| F10-AC04 — Escolha do grupo e envio vinculado | HTTP-GRUPOS-01, WRK-GRUPOS-01 |
| F10-AC05 — Persistência e privacidade | HTTP-COOKIES-01, HTTP-GRUPOS-01, WRK-ACESSO-02 |

## HTTP API

#### `HTTP-COOKIES-01` — Salvar cookies privados
- given: formulário local e sessão sintética em header ou JSON.
- when: salvar cookies.
- then:
  - Formato válido é persistido privadamente e mostra aguardando verificação, sem devolver os valores.
  - Formato inválido, domínio alheio e autenticação ausente/vencida exibem erro; a revisão anterior permanece.
  - POST sem CSRF é recusado; respostas não permitem cache; segredos não aparecem em logs.

#### `HTTP-WHATSAPP-01` — Pareamento e recuperação
- given: serviço local e sessão desligada, em QR ou WORKING.
- when: conectar e consultar estado.
- then:
  - Conexão apresenta QR atual e reconhece WORKING após pareamento.
  - Falha/expiração têm recuperação explícita e não são apresentadas como conectadas.
  - A chave não vai ao navegador e conectar não envia mensagem.

#### `HTTP-GRUPOS-01` — Grupo autorizado
- given: sessão conectada e lista paginada de grupos.
- when: salvar um grupo e ativação de alertas.
- then:
  - Apenas grupo retornado pela conta atual é aceito e persiste após reinício.
  - Grupo forjado, conta alterada ou sessão indisponível não substituem a última configuração válida.
  - Desativar conserva recibos; trocar destino não muda intenções vinculadas.

## UI

#### `UI-INTEGRACOES-01` — Menu e estados
- given: aplicação navegável, desktop e janela estreita, dados sintéticos.
- when: acessar Integrações pelo menu e percorrer salvar cookies/conectar/selecionar grupo.
- then:
  - Controles funcionam por teclado, com rótulos, erros e feedback claros, sem overflow horizontal.
  - Cookies nunca são reapresentados; QR e estado de conexão têm apresentação coerente.
  - As telas existentes mantêm navegação e identidade visual.

## Worker

#### `WRK-ACESSO-01` — Acesso expirado
- given: acesso Facebook exige login ou checkpoint na coleta.
- when: o worker registrar a falha.
- then:
  - A coleta fica suspensa e um aviso persistente explica como renovar/verificar a sessão.
  - Ofertas e histórico anteriores permanecem disponíveis.

#### `WRK-ACESSO-02` — Renovação com concorrência
- given: coleta antiga em curso e nova revisão de cookies salva.
- when: retomar o worker.
- then:
  - O worker passa a usar a nova revisão sem reiniciar; resultado/arquivo antigo não sobrescreve a revisão atual.
  - O marco de carga inicial e os recibos anteriores permanecem.

#### `WRK-GRUPOS-01` — Alerta ao grupo escolhido
- given: grupo selecionado com ativação explícita e um evento elegível F09.
- when: despachar e reconciliar.
- then:
  - O POST usa o grupo selecionado e o corpo/referência do evento.
  - Recibos GOWS e normais exigem saída, grupo e conta corretos e ACK aplicável.
  - Troca de grupo/conta não redireciona intenções antigas nem libera reenvio incerto.
