# Correção independente dos pins/CLI F19

Escopo: `CLI-PREPARO-01` e higiene do smoke conforme spec §5. Este relatório não declara clean global da F19. Trabalho em `/home/marce/.codex/worktrees/6c3f/garimpei`, branch `feat/F19-inferencia-multimodal-local`; sem commit/merge/push/PR.

## Alterações e fronteiras

- Novo `artifact_policy.py`: valida a imagem oficial aprovada exata, plataforma, versão, tag/modelo, quantização, capacidades e IDs de prompt/schema. Calcula SHA256 do manifesto minificado completo; qualquer alteração de blob, tamanho ou projetor diverge do digest aprovado. Distingue ausência/incompletude de pin inválido.
- Tokenizer: exige repositório/revisão/URL aprovados coerentes e SHA256 completo. O arquivo físico e sua correspondência com esse SHA continuam responsabilidade do preparador; o helper não faz I/O ou download.
- `local_ai.py`: sucesso 0, pré-requisito ausente 2, validação/inferência 1. `prepare` exige `--download` e serviço habilitado antes de iniciar serviço. Smoke imprime somente IDs, estado, cobertura, contagens de resultado e métricas sanitizadas; nunca conteúdo/findings/quotes/thinking. Amostras GPU expõem somente números.
- `tests/factories/inference.py`: mesmas assinaturas/APIs `OllamaGatewayFake`, `serve_inference`, `inference_settings`; metadata positiva completa vem de cópia do lock oficial, sem medições históricas para preservar a quota da fixture. Versão/digest do fake correspondem ao pin aprovado.
- Novo `tests/unit/test_inference_artifacts.py`: regressões na fronteira `read_lock`, comando CLI e smoke com fakes nomeados. Wiring de `read_lock`, ajuste do setup de tokenizer e demais módulos são do responsável F19.

## RED/GREEN e qualidade focada

1. Antes do produto: 24 FAIL / 3 PASS, pytest exit 1. Falhas reproduzem pins aceitos, códigos incorretos e canário privado impresso. Log original: [pins-correction-red.txt](pins-correction-red.txt).
2. Após wiring/correção: `apps/backend/.venv/bin/python -m pytest apps/backend/tests/unit/test_inference_artifacts.py apps/backend/tests/unit/test_inference_gateway.py apps/backend/tests/unit/test_inference_inputs.py -q`: 40 PASS, 2.12 s, exit 0. [Log GREEN](pins-correction-green.txt).
3. Ruff nos quatro arquivos e mypy focado nas duas fontes: exit 0. [Log](pins-correction-quality.txt). Nenhuma suíte ampla/gate global foi executado por este agente durante escrita concorrente.

## Reexecução observável em D2

Comando: `PYTHONPATH="$PWD/apps/backend" apps/backend/.venv/bin/python .runtime/f19-pins-20261112-fixed.py` (orquestração exit 0, veredito funcional PASS).
Instância própria `eval_wave11_f19_pins_fix2`, web 22747, `GARIMPEI_AI_SERVICE_ENABLED=false`, segredos novos privados. `init.sh --disposable` exit 0 e ready 200. Nenhum recurso A/C, GPU ou Ollama real foi usado.
OllamaGateway e HTTP loopback reais contra `PinsMetadataHttpFake`; reserva de GPU somente em arquivo privado temporário. Diagnóstico persistido no PostgreSQL de D2 pelo repositório real; subprocesso CLI real leu esse estado. A CLI não foi substituída. Locks privados nunca alteraram o lock oficial.

| Caso | Diagnóstico esperado/observado | CLI esperado/observado | Resultado |
|---|---|---|---|
| valid_metadata_control | ready / ready | 0 / 0 | PASS/PASS |
| lock_absent | artifact_missing / artifact_missing | 2 / 2 | PASS/PASS |
| lock_invalid_json | artifact_mismatch / artifact_mismatch | 1 / 1 | PASS/PASS |
| model_digest_divergent | artifact_mismatch / artifact_mismatch | 1 / 1 | PASS/PASS |
| server_version_divergent | artifact_mismatch / artifact_mismatch | 1 / 1 | PASS/PASS |
| image_latest_unpinned | artifact_mismatch / artifact_mismatch | 1 / 1 | PASS/PASS |
| image_divergent | artifact_mismatch / artifact_mismatch | 1 / 1 | PASS/PASS |
| image_digest_incomplete | artifact_mismatch / artifact_mismatch | 1 / 1 | PASS/PASS |
| image_pin_absent | artifact_incomplete / artifact_incomplete | 2 / 2 | PASS/PASS |
| manifest_layers_incomplete | artifact_incomplete / artifact_incomplete | 2 / 2 | PASS/PASS |
| model_tag_divergent | artifact_mismatch / artifact_mismatch | 1 / 1 | PASS/PASS |
| weights_missing | model_missing / model_missing | 2 / 2 | PASS/PASS |
| weights_corrupt | model_corrupt / model_corrupt | 1 / 1 | PASS/PASS |
| vision_missing | artifact_mismatch / artifact_mismatch | 1 / 1 | PASS/PASS |
| gpu_reservation_absent | gpu_unavailable / gpu_unavailable | 2 / 2 | PASS/PASS |

15/15 casos PASS, incluindo controle positivo `ready`/0. `local_ai prepare` sem `--download`: 2 esperado/observado. Zero chamadas `/api/chat`, `/api/pull`, `/api/create`, zero recuperação e nenhum canário privado exposto.
[Matriz completa com stdout/stderr, comandos, esperado/observado e hashes antes/depois](pins-2026-11-12T03-58-49Z.json); [saída](pins-correction-run.txt).

## Estabilidade e limpeza

Todos os hashes de fonte/testes/lock oficial/Compose/pyproject/uv.lock eram idênticos no início e fim da matriz (`source_and_official_lock_unchanged=true`). [Hashes dos arquivos da correção e lock oficial](pins-correction-hashes.json). Não houve alterações no produto F20.
Worker D2 retomado apenas para parada; `stop.sh --clean` exit 0 removeu processos/serviços/dados descartáveis próprios. Consulta Docker filtrada por D2 retornou zero contêineres. Servidor HTTP, reserva temporária e diretório privado de segredos foram encerrados/removidos.

## Limitações e histórico preservado

Este laboratório comprova rejeição de pins e contratos de diagnóstico/CLI em dependência HTTP controlada. Não comprova presença real de blobs, identidade da imagem executada no Docker ou uso de GPU/VRAM real. A CLI status lê o diagnóstico persistido; o gateway recebeu as cópias privadas do lock. Os gates completos e demais itens do contrato pertencem ao responsável F19.
O FAIL histórico continua em [pins-report.md](pins-report.md), [pins-run.txt](pins-run.txt) e [pins-2026-11-12T03-38-57Z.json](pins-2026-11-12T03-38-57Z.json). Uma tentativa inicial da reexecução, sem PYTHONPATH dos testes, encerrou antes do init com ModuleNotFoundError e não criou recursos; [log preservado](pins-correction-launch.txt).
