# F15 — Avaliação real da referência assistida por IA

**Estado:** E2E-QUALIDADE-01 permanece BLOCKED pela ausência de comprovação quantitativa de latência fria/quente de inferência nas falhas. A execução física terminou; a suíte integral de 780 testes passou integralmente nas três partições, sem omissão ou alteração das 660 entradas de código verificadas. [Resumo completo](evidence/full-2026-11-13-suite-summary.json). Nenhum done/clean é declarado aqui.

O usuário aprovou substituir o aceite humano pela referência assistida por IA. A canon 9ce6a75 preserva os IDs/8ACs e exige origem/método explícitos; `independent_human_review=false` e `legacy_human_acceptance_satisfied=false` permanecem verdadeiros e não são a causa do bloqueio atual. A referência foi produzida por Codex em sessão assistente; a revisão exata do serviço e sua execução local não foram atestadas. O motor F19 efetivamente avaliado é separado dessa origem e usa Qwen local na RTX5070.

A cópia exata da referência está em [evidence/ai-reference-reviewed-2026-11-13.json](evidence/ai-reference-reviewed-2026-11-13.json), SHA256 `e13d908534c856b30ff2713f8383dea8b10fe8c4d803e84de7ef992c891bb496`. O manifesto permanece `26c3ee5e9d34a51b8d3827e9700134e7e45d6cea3dbf2f86a0c81f3f05c3a59b`. Freeze às14:59:39UTC, última revisão registrada14:57:10.635UTC; primeiro request local às15:19:29.452838UTC. O [audit](evidence/ai-reference-freeze-audit-2026-11-13.json) e o registro original de freeze conservam essa separação. Não houve alteração de labels/splits após consultar o modelo.

## Composição e limites

| Universo | Total | good | defect | uncertain |
|---|---:|---:|---:|---:|
| Revisado por IA |23|4|7|12|
| Ajuste, não executado neste benchmark |7|4|0|3|
| Reservado, executado |16|0|7|9|

O pacote contém 18 ilustrações sintéticas,3 regressões textuais e2 casos reais/9originais autorizados de F14. O reservado tem1 anúncio real PS5 (4 fotos),12 controles visuais sintéticos e3 textos. Hot wheels (5 fotos, fora das famílias suportadas) está no ajuste e não foi executado. Há controles nas seis categorias, mas o material real reservado cobre somente console; outras categorias reais são lacunas declaradas, sem inventar um mínimo contratual de 6 categorias reais.

Nenhum good está no reservado. Sua linha vazia é ausência de suporte para avaliar essa classe, não precisão 100%, acerto ou estimativa de sensibilidade. Os controles positivos de Service continuam demonstrando a regra determinística no seu próprio escopo; não substituem uma amostra visual positiva reservada nem viram avaliação independente.

## Execução e concordância observada

Fonte de código 2453f5f,707 arquivos iguais na cópia, sem alteração backend. F19 usou `qwen3.5:4b-q4_K_M`, digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`, política `condition-policy-v1`, prompt/schema `condition-evidence-v1`. As cópias locais/hash/pins F14 foram preservadas. Root/cota F14 foram corrigidos apenas no env privado (64 MiB); a tentativa anterior configuration_required/zero chamadas não foi contada como inferência.

CLI exit0 em 89.658 s; driver complete=true significa término de processamento, não aprovação. Foram 13 partes realmente enviadas, todas rejeitadas como invalid_output;0 partes sucedidas. No caso real havia4 fotos fornecidas:1 parte enviada/falha e3 pendentes, não examinadas. As três regressões textuais não chamaram o modelo. O banco/fila foram preservados para auditoria.

| Referência IA → condição automática | good | defect | uncertain |
|---|---:|---:|---:|
| good (sem suporte reservado) |0|0|0|
| defect |0|2|5|
| uncertain |0|0|9|

A matriz descreve a condição automática do pipeline conservador. São 11 concordâncias de rótulo,5 divergências (defect→uncertain) e14 abstenções automáticas; **nenhuma resposta visual do modelo foi aceita**. Os 2 defect vêm de proteção textual determinística. Esses números não são acurácia do Qwen contra verdade humana nem demonstram suficiência visual do modelo. Não há meta numérica de qualidade aprovada.

## Erros e cobertura visual

| Categoria de referência, somente casos visuais | Casos | Fotos fornecidas | Partes enviadas | invalid_output | Pendentes |
|---|---:|---:|---:|---:|---:|
| Eletrônicos gerais |2|2|2|2|0|
| Câmeras |2|2|2|2|0|
| Computadores |2|2|2|2|0|
| Consoles (inclui PS5 real) |3|6|3|3|3|
| Fones |2|2|2|2|0|
| TVs |2|2|2|2|0|
| Total |13|16|13|13|3|

`invalid_output` não preservou submotivo exato de stop/token/envelope/schema. Não foi feita chamada extra para diagnóstico, e não se atribui uma causa não comprovada. Fotos fornecidas, partes enviadas e respostas aceitas são diferentes: os hashes/IDs e as filas por caso estão em [quality-real-case-coverage-2026-11-13.json](evidence/quality-real-case-coverage-2026-11-13.json). As3 partes pending pertencem a request failed; sua presença no catálogo não as torna examinadas.

## Recursos e tempo: medidas e ausência de prova

| Medida | Observação | Escopo/limite |
|---|---|---|
| Ollama no runtime próprio |3.1 GB,100% GPU,context 4096 | Snapshot de offload;100% não é taxa de utilização do chip. |
| NVIDIA RTX5070 no host |6481 MiB usados,19% utilização | Snapshot exato versionado; inclui outros usos do host e não é pico do modelo. |
| RAM host |pico observado23.874.101.248 bytes |800 amostras; alvo100 ms, mediana real100.280 ms. Não é RAM exclusiva do modelo. |
| RSS avaliador |pico183.148.544 bytes |Mesmo sampler; não é RSS do processo Ollama no contêiner. |
| Parede do primeiro caso após unload confirmado |19.779949 s |Caso real com 4 fotos fornecidas/1 parte enviada; inclui preparação/orquestração e resposta rejeitada. |
| Parede dos12 casos visuais posteriores |5.090829–5.696210 s; mediana5.203406 s |Materiais distintos; não é comparação controlada fria/quente nem load_duration. |
| Casos textuais sem inferência |0.032616–0.035966 s |Política determinística; não são latências de IA. |

A prova GPU é [f15-ai-media-ready-runtime-proof.json](evidence/f15-ai-media-ready-runtime-proof.json); RAM e wallclock estão no [resumo real](evidence/f15-ai-real-final-summary.json). Um sampler externo iniciado depois do CLI não foi usado como prova do período de inferência.

As partes falhas retiveram apenas sent=true, sem load_duration, métricas por chamada de GPU/VRAM ou tempo quantitativo de inferência fria/quente. A ordem after_verified_unload/subsequent_case não preenche sozinha essa lacuna; cargas distintas e parede do driver não serão promovidas a essa medição. Este é o observável ainda BLOCKED do contrato; não se exige pico de GPU, samplerGPU específico ou mínimo de acurácia inventado.

## Encerramento e próximo escopo

Contêineres próprios foram parados normalmente (exit0), reserva de GPU liberada; pesos/banco/fila preservados. Nenhum Facebook ou WAHA real foi utilizado. A inferência F19 ficou na rede interna local do contêiner, separada da origem não atestada local da referência de IA.

As três correções autorizadas desta retomada foram consumidas (cycles 5). Um próximo escopo deve investigar as13rejeições sem inventar funcionamento/identidade, preservar telemetria nas falhas, explicar/cobrir as 3 partes não examinadas e realizar medição fria/quente com condições documentadas. Não mudar labels/splits para obter resultado desejado; se houver ajuste com dados já consultados, declarar a nova rodada e sua exposição. Nova avaliação e eventual conclusão exigem autorização/orçamento próprio e os gates aplicáveis. F21/F22 continuam aguardando F15.


## Gates finais

Full 780:780 coletados/780 únicos/780 PASS, sem missing/not_passed/changed_inputs; partições 283/239/258, todas exit0 e sem falha/erro/skip nos XMLs. Artefatos em evidence/full-2026-11-13-*. Seis gates Python também passaram e a fonte permaneceu congelada. O bloqueio E2E de latência fria/quente e as limitações de resposta visual continuam apesar desses gates. Ver o relatório canônico eval-report-2026-11-13T15-39-09Z.md.
