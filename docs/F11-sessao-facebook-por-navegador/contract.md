# Contract — F11 Sessão Facebook por navegador

## Prerequisites
- PostgreSQL/web/worker F02 descartáveis, Chromium instalado e origem HTML sintética loopback exclusiva de eval.
- Perfil temporário privado externo ao checkout, sem sessão real nas evidências.
- Ambiente dev preservado; WSLg para janela real. Login e confirmação externos dependem do usuário.

## Quality gates
- `node scripts/run-gates.mjs` (seis grupos).
- Django check e makemigrations --check --dry-run com test settings.
- Testes de configuração/login/profile e regressões F04/F10 afetadas.
- Navegação `playwright-cli`, desktop e 390 px, usando fixture própria.

## Coverage Manifest
| AC | Itens |
|---|---|
| F11-AC01 — Login pelo navegador | HTTP-LOGIN-01, UI-LOGIN-01 |
| F11-AC02 — Continuidade privada | BROWSER-PROFILE-01 |
| F11-AC03 — Suspensão e retomada | WORKER-LOGIN-01 |
| F11-AC04 — Compatibilidade | CONFIG-SESSION-01 |
| F11-AC05 — Prova real | MANUAL-FACEBOOK-01 |

## HTTP API
#### `HTTP-LOGIN-01` — Abrir e confirmar
- POST exige CSRF; duplicar abertura ativa não cria outro pedido/perfil. Estado aguardando não implica conectado. Confirmar sem autenticação mantém a pausa; sucesso verificado permite retomada. Janela fechada/reinício/timeout não viram sucesso.

## Service
#### `BROWSER-PROFILE-01` — Perfil persistente
- Chromium real mantém cookies e localStorage ao fechar/reabrir no mesmo diretório privado 0700. Perfil dedicado, sem usar o perfil pessoal. Apenas um processo de navegador usa o perfil por vez. Navegador normal visível em dev; headless/origem substituta permitidos só na fixture eval. Flush/fechamento antes de liberar a coleta.
#### `CONFIG-SESSION-01` — Defaults corretos
- Sessão gerenciada na UI recebe padrões reais de timeout/retry/intervalo. Overrides explícitos preservados. Compatibilidade da importação e destino WhatsApp permanece.

## Worker
#### `WORKER-LOGIN-01` — Pausa segura
- Abrir login invalida a geração ativa e suspende coleta. Perfil é verificado explicitamente antes de retomar. Desafio posterior pausa; reinício não libera essa pausa. Marco inicial/ofertas/recibos conservados. Falha/interrupção pede recuperação manual.

## UI
#### `UI-LOGIN-01` — Operação local
- Botões de abrir/verificar e estado via polling no menu; instruções claras sobre a janela e desafio. Importação avançada acessível. Desktop e 390 px sem overflow, com foco/rótulos e sem material de sessão nas capturas.

## E2E
#### `MANUAL-FACEBOOK-01` — Acesso real
- Usuário abre janela, autentica, confirma Marketplace e observa coleta usando perfil após reabertura. Registrar resultado real sem segredos. Fixture local não comprova aceitação nem estabilidade da plataforma. Enquanto pendente, status implemented, não done.
