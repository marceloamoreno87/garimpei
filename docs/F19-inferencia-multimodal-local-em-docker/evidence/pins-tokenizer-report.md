# Adendo de correção: SHA exato do tokenizer

Escopo dirigido: `CLI-PREPARO-01`, anterior ao congelamento final F19. Corrige uma lacuna adicional ao relatório `pins-correction-report.md`; não substitui ou apaga a evidência histórica de D2 e não declara clean global.

O helper anterior fixava repositório/revisão/URL e aceitava qualquer SHA256 de 64 caracteres. O diagnóstico não conferia o arquivo físico antes de `ready`: a conferência ocorria depois no preparador. Portanto um lock com `tokenizer.sha256='0'*64` passava indevidamente; o achado é confirmado.

`artifact_policy.py` agora exige o SHA oficial já capturado no lock aprovado: `5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42`. O lock oficial não foi editado. Não houve consulta a fontes novas, download ou criação de hash substituto.

A regressão nova em `test_inference_artifacts.py` usa OllamaGateway real, fake HTTP nomeado e HostGpuGuard apenas em arquivo temporário. Primeiro confirma `ready` com lock completo aprovado; depois modifica somente tokenizer.sha256 para 64 zeros e exige `artifact_mismatch` sem chamada HTTP, além de exigir rejeição em read_lock. A reserva temporária é liberada em finally. Nenhuma GPU/Ollama real ou ambiente A/C/D2 foi usado.

RED antes da correção: o gateway devolveu `ready` em vez de `artifact_mismatch`, 1 FAIL, 29 deselected, 0.59 s, exit 1. [Log RED](pins-tokenizer-red.txt).

GREEN: `apps/backend/.venv/bin/python -m pytest apps/backend/tests/unit/test_inference_artifacts.py apps/backend/tests/unit/test_inference_gateway.py -q`: 37 PASS, 2.62 s, exit 0. Inclui o controle positivo e a rejeição do tokenizer divergente, além das regressões anteriores de pins/CLI. [Log GREEN](pins-tokenizer-green.txt).

Ruff dos dois arquivos alterados e mypy focado no helper: exit 0. [Qualidade](pins-tokenizer-quality.txt). [Hashes atuais](pins-tokenizer-hashes.json). O hash do lock oficial permanece `20dc912d31503a748f30b4101dcdf352cd10ec7c01f978ec7b560c5f7950aa4a`.

Somente helper e teste de pins foram editados nesta rodada. O responsável F19 isolou o tokenizer sintético de seu teste de orçamento com fake nomeado, sem afrouxar a política de produção; alterações desse teste e gates globais pertencem a ele. A matriz D2 não foi repetida: o acréscimo só restringe o SHA do tokenizer, comprovado pelo gateway focado com controle positivo. A prova é de metadata/diagnóstico e não substitui inferência GPU ou prova física do arquivo do tokenizer.

Adendo de tipos do teste: o gate global do responsável detectou 3 erros mypy no teste novo (retorno json.loads e indexação de object). Corrigidos somente com casts explícitos no teste, sem mudança de comportamento. Reexecução final dos mesmos 37 testes passou; Ruff e mypy --strict incluindo helper E teste passaram, exit 0. [Log final com tempo e códigos](pins-tokenizer-final.txt). Os hashes deste adendo refletem esse estado final. Nenhuma edição adicional de produto/testes pendente.
