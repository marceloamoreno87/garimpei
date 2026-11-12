# F19 — CLI-PREPARO-01: pins negativos e códigos da CLI

**Resultado do escopo:** FAIL. Não é avaliação global da F19.

Execução: 2026-11-12T03-38-57Z. Instância exclusiva D=`eval_wave11_f19_pins`, IA desabilitada por `GARIMPEI_AI_SERVICE_ENABLED=false`; nenhuma GPU, Ollama ou ambiente A/C foi manipulado.

## Método e fronteiras

O script `.runtime/f19-pins-20261112.py` criou segredos novos em diretório temporário privado, iniciou D por `init.sh --disposable`, confirmou `/health/ready` 200 e pausou apenas o worker D para tornar o diagnóstico estável. Usou cópias privadas do lock oficial e um `HostGpuGuard` em arquivo temporário próprio, sem reserva do host real.

O **OllamaGateway real**, com transporte HTTP real para `PinsMetadataHttpFake` em loopback, produziu cada diagnóstico. O resultado foi persistido pelo **PostgresInferenceRepository real** em D e consultado pela **CLI real** `uv run --project apps/backend --frozen --no-sync python apps/backend/manage.py local_ai status`. Nenhuma função de CLI foi substituída. A CLI lê diagnóstico persistido; ela não recebeu caminho de lock alternativo e não verificou os pins privados diretamente. Esse limite é relevante para interpretar os resultados: a fraqueza comprovada está no caminho `read_lock` → `OllamaGateway.diagnose/_verify`, refletido no status persistido da CLI.

A preparação foi chamada apenas como `local_ai prepare`, **sem `--download`**. O ramo recusou o preparo. Em todas as variantes houve zero chamadas `/api/chat`, `/api/pull` e `/api/create`, zero recuperação e zero evidência de download implícito. O fake nunca usa GPU.

## Matriz observada

| Caso | Motivo esperado | Motivo observado | CLI | Prontidão |
|---|---|---|---:|---|
| valid_metadata_control | `ready` | `ready` | 0 | PASS |
| lock_absent | `artifact_mismatch` | `artifact_mismatch` | 64 | PASS |
| lock_invalid_json | `artifact_mismatch` | `artifact_mismatch` | 64 | PASS |
| model_digest_divergent | `artifact_mismatch` | `artifact_mismatch` | 64 | PASS |
| server_version_divergent | `artifact_mismatch` | `artifact_mismatch` | 64 | PASS |
| image_latest_unpinned | `artifact_mismatch` | `ready` | 0 | FAIL |
| image_divergent | `artifact_mismatch` | `ready` | 0 | FAIL |
| image_digest_incomplete | `artifact_mismatch` | `ready` | 0 | FAIL |
| image_pin_absent | `artifact_mismatch` | `ready` | 0 | FAIL |
| manifest_layers_incomplete | `artifact_mismatch` | `ready` | 0 | FAIL |
| model_tag_divergent | `artifact_mismatch` | `ready` | 0 | FAIL |
| weights_missing | `model_missing` | `model_missing` | 64 | PASS |
| weights_corrupt | `model_corrupt` | `model_corrupt` | 1 | PASS |
| vision_missing | `artifact_mismatch` | `artifact_mismatch` | 64 | PASS |
| gpu_reservation_absent | `gpu_unavailable` | `gpu_unavailable` | 1 | PASS |

## Falhas comprovadas

1. **Pin inválido anunciado pronto:** `image_latest_unpinned`, `image_digest_incomplete`, `image_pin_absent`, `manifest_layers_incomplete` e `model_tag_divergent` retornaram `reason=ready`, com HTTP de metadados válidos e CLI 0. São locks sem pin obrigatório completo, com `latest`, sem layers ou com modelo divergente; devem falhar antes de anunciar prontidão. A variante `image_divergent` também retornou ready/0, porém sua divergência de imagem é conhecida pelo baseline controlado: nenhuma imagem Docker real foi inspecionada neste ensaio.

2. **Códigos fora da especificação:** lock ausente/modelo ausente retornam 64; a spec §5 define 2 para pré-requisito ausente. JSON inválido, digest/versão divergentes e capacidade visual ausente retornam 64; a mesma tabela define 1 para falha de validação. `operations.md` informa 64, mas isso diverge da spec preservada e não muda o requisito canônico desta avaliação.

3. `local_ai prepare` sem `--download` retorna 64 e `CommandError: Local AI: artifact_mismatch`. O efeito seguro de recusar preparo foi confirmado; o código difere da pré-condição ausente/uso inválido descrito pela spec.

O código 1 de `gpu_unavailable` para **reserva temporária ausente** é um caso operacional controlado. A matriz JSON registrou expectativa 2 pela leitura de pré-requisito ausente; essa interpretação é discutível porque não se simulou ausência física de GPU. Esse caso não sustenta isoladamente a reprovação dos códigos. O bloqueio de prontidão nele passou.

## Verificações que passaram

- Controle de metadados válido: ready/0, modelo com digest completo e capacidades completion/vision fornecidos pelo fake; somente controle do laboratório, sem prova real de GPU ou de pesos em disco.
- Lock ausente/JSON inválido, digest de modelo e versão do servidor divergentes, modelo ausente e capability visual ausente impediram ready.
- HTTP 500 com erro de checksum/tensor produziu `model_corrupt` e CLI 1. O canário sintético privado incluído na resposta HTTP não apareceu na saída da CLI.
- Não houve atualização silenciosa: nenhum caminho de pull/chat/create foi chamado e o comando de preparo sem download falhou.

## Reprodução

Na worktree F19, com a instância D livre:

```bash
PYTHONPATH="$PWD/apps/backend" uv run --project apps/backend --frozen --no-sync python .runtime/f19-pins-20261112.py
```

O runner sempre usa D e um diretório temporário novo, limpa seus recursos e grava um novo `pins-<timestamp>.json`. Não o execute simultaneamente com outra execução D. A saída JSON mantém esperado/observado, código, stdout/stderr sanitizados e chamadas HTTP por caso. O runner termina com código 0 quando completou a matriz e o cleanup; **o veredito funcional está em `overall=FAIL`**, não nesse código de orquestração.

## Evidências e integridade

- [Matriz com comandos/códigos/saídas](pins-2026-11-12T03-38-57Z.json).
- [Saída da execução](pins-run.txt).
- `source_and_official_lock_unchanged=true`: hashes de fonte/testes, model-lock oficial, Compose, pyproject e uv.lock iguais antes/depois.
- `cleanup.code=0`; worker D retomado antes do stop; `stop.sh --clean` removeu apenas dados descartáveis D. Diretório temporário de segredos/locks/guard foi removido.
- Nenhuma edição em fonte, testes, progresso, especificação, plano, contrato, lock oficial, Compose ou artefatos controls-*.

## Limitações

Este ensaio não inspecionou imagem Docker, blobs ou tokenizer reais, não executou inferência e não consumiu VRAM. Metadados válidos do fake não comprovam pesos íntegros ou GPU disponível. O caso de pesos incompletos cobriu ausência do modelo no catálogo; corrupção cobriu erro HTTP explícito do serviço. A prova física e o preparo completo pertencem ao agente F19.
