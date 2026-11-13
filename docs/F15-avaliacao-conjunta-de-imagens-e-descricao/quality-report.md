# F15 — Avaliação local e referência assistida por IA

**Estado:** avaliação do contrato concluída:31itens PASS/8ACs verificados. A prova física v3/1024 e a cobertura final de812testes passaram após reparo explícito de ambiente Chromium; o full bruto preserva811PASS/1FAIL e não foi reescrito. O ensaio publica erros e limitações e não declara suficiência visual do modelo nem acurácia contra verdade humana. O relatório anterior15:39:09 permanece histórico.

O usuário aprovou a referência de IA em F15-AC05 e depois saída até 1024 somente na F15, mantendo legado 512/contexto 4096. A canon integrada em b43092b preserva IDs/DAG e exige origem/método explícitos. `reference_method=ai_assisted`, `independent_human_review=false` e `legacy_human_acceptance_satisfied=false` permanecem verdadeiros. A referência foi produzida por Codex em sessão assistente; a revisão exata do serviço e sua execução local não foram atestadas. O F19 avaliado é separado dessa origem e usa Qwen local na RTX5070.

A [referência exata](evidence/ai-reference-reviewed-2026-11-13.json) conserva SHA256 `e13d908534c856b30ff2713f8383dea8b10fe8c4d803e84de7ef992c891bb496`; manifesto `26c3ee5e9d34a51b8d3827e9700134e7e45d6cea3dbf2f86a0c81f3f05c3a59b`. O [freeze original](evidence/ai-reference-freeze-audit-2026-11-13.json) é anterior à primeira execução local. Nenhum label/split foi alterado após as predições.

## Universo, exposição e cobertura

| Universo | Total | good | defect | uncertain |
|---|---:|---:|---:|---:|
| Revisado por IA |23|4|7|12|
| Ajuste, fora deste benchmark |7|4|0|3|
| Reservado, repetido nesta onda |16|0|7|9|

O reservado já foi consultado em rodadas anteriores. Este ensaio repete esses16 casos depois do ajuste de prompt/teto, sem alegar novo holdout independente. Há1anúncio real PS5/4 fotos,12 controles visuais sintéticos e3 textos. Hot wheels/5 fotos pertence ao ajuste, fora das famílias suportadas. Os controles cobrem seis categorias; material real reservado cobre somente console. Outras categorias reais são lacunas declaradas, sem meta contratual inventada de6 categorias reais.

Nenhum good está no reservado. Linha vazia não é precisão100% nem sensibilidade medida; controles positivos de Service demonstram regras no seu escopo, sem virar amostra visual positiva reservada ou validação humana independente. O campo legado de proveniência `kind=real_source_unreviewed` identifica a origem do snapshot, não nega a revisão posterior `ai_assisted` congelada.

## Fonte, limites e execução

Fonte `b43092b82ac7d034b5f967aa7fb930bdc2b77f4c`, backend tree `0b63d4db4cad9f74421d2ac4792b52bea6eb50e2`;721 arquivos da cópia verificados sem mudança. Modelo `qwen3.5:4b-q4_K_M`, digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`; imagem Ollama0.40.16 pinada. Perfil/schema `condition-evidence-v3`, política `condition-policy-v1`. O [resumo físico](evidence/wave2-v3-quality-summary.json) identifica nonce20bfbb180db84076b2778bec0a5d6255, revisões, métricas e cleanup; a [auditoria](evidence/wave2-v3-quality-artifact-audit.json) e o [mapa de cópias exatas](evidence/wave2-v3-quality-copy-map.json) mantêm os hashes das cópias sanitizadas.

Teto F15=1024, legado=512, contexto=4096. Preparador reserva1536para imagem e até1536para texto F15 multimodal, incluindo instruções/schema/margem; entrada que não cabe é recusada sem truncar. [Auditoria offline](evidence/wave2-profile-1024-budget.json): tokenizer oficial,23 textos, máximo1506 com identidade vazia. A [auditoria real das 14 partes enviadas](evidence/wave2-v3-real-budget-audit.json) registra máximo de 731 tokens de prompt, soma máxima com reserva 1755≤4096, inclusive nas saídas rejeitadas. O contexto real e a soma prompt_eval_count+reserva seguem verificados; nenhuma folga foi obtida alterando modelo/pins/schema estrito. Os perfis v1/v2 ficam históricos e incompatíveis com nova avaliação v3.

CLI exit 0 em 132.961269 s,16 casos. Foram14 partes enviadas:8 aceitas e6 rejeitadas;2 fotos da galeria real permaneceram pendentes. Driver completo significa término do ensaio, não aprovação das predições. As3 regressões textuais não chamaram o modelo. Nenhuma foto pendente/falha é apresentada como examinada.

| Referência IA → condição automática | good | defect | uncertain |
|---|---:|---:|---:|
| good, sem suporte reservado |0|0|0|
| defect |0|3|4|
| uncertain |0|0|9|

São12 concordâncias de rótulo,4 divergências defect→uncertain e13 abstenções. Três condições defect incluem2 guardas textuais determinísticas e1 caso visual. Isso não é acurácia do Qwen contra verdade humana nem comprovação de suficiência generalizada; não há meta numérica aprovada. Nenhum caso foi promovido automaticamente a good.

## Erros e cobertura por categoria

| Categoria, casos visuais | Casos | Fotos fornecidas | Enviadas | Aceitas | Rejeitadas | Pendentes |
|---|---:|---:|---:|---:|---:|---:|
| Eletrônicos gerais |2|2|2|1|1|0|
| Câmeras |2|2|2|1|1|0|
| Computadores |2|2|2|2|0|0|
| Consoles, inclui PS5 real |3|6|4|3|1|2|
| Fones |2|2|2|0|2|0|
| TVs |2|2|2|1|1|0|
| Total |13|16|14|8|6|2|

Cinco partes falharam por `generation_length_limit` (eletrônicos, câmera, console real, fone e TV); uma por `text_reference_mismatch` (fone). Saída incompleta e citação não literal continuam rejeitadas. Outras abstenções incluem cinco conflitos de identidade, evidência visual insuficiente e texto não testado; referências exatas não garantem correção semântica da interpretação de IA.

O PS5 real tem4 fotos: `d304…248b` examinada/succeeded; `c95c…` enviada/rejeitada por limite; `e078…` e `ffc3…` pendentes/não enviadas. Hashes completos, estados públicos e métricas numéricas estão em [cobertura por caso/parte](evidence/wave2-v3-quality-case-coverage.json). Requisição failed conserva as pendentes como não examinadas; não há reanálise ou envio extra ocultos.

## Frio/quente e recursos medidos

O [par controlado separado](evidence/wave2-v3-controlled-pair-summary.json) usou a mesma foto/texto/bodySHA duas vezes, sem alterar parte v1 histórica. Frio após unload verificado e residência ausente; quente com o digest pinado já residente. Ambos:959tokens, done_reason=stop, JSON/schema/referências aceitos pelo gateway e validador F15. Essas duas chamadas não se somam ao corpus.

| Medida | Fria | Quente | Condição/escopo |
|---|---:|---:|---|
| Total servidor |12.917914821s|8.312028550s|Envelope da mesma carga, inclui carregamento |
| Carregamento servidor |3.767243235s|0.003073627s|load_duration real |
| Parede monotônica gateway |12.928708116s|8.322323604s|Chamada pública, residência e validação |
| VRAM reportada pelo servidor |3.140.495.604B|3.140.495.604B|size_vram=size; contexto4096 |
| Pico GPUhost observado |7245MiB|7156MiB|44/29amostras, não exclusivo do modelo |
| Utilização GPUhost máxima observada |79%|79%|Não confundir com offload100% |
| Pico RAMhost observado |21.481.107.456B|22.177.738.752B|129/83amostras, outros programas inclusos |
| Pico RSS avaliador |77.746.176B|77.877.248B|Processo avaliador, não Ollama |

Durante o corpus:417 amostras GPUhost, pico7201MiB/81%;1232 amostras RAM, pico host23.417.470.976B e RSSavaliador183.414.784B. O sampler GPU usa intervalo alvo250ms mais a consulta, RAM alvo100ms; host compartilhado com outros programas e a suíte completa em paralelo. Esses picos são observados nas amostras, não garantias de pico absoluto nem memória exclusiva do modelo. O controle legado separado também foi aceito fisicamente com num_predict512/context4096, sem alterar seu perfil ou incluir a chamada na matriz F15.

## Isolamento, fila e encerramento

Runtime eval próprio com GPU guard, modelo/imagem pinados, root/cota F14 privada64MiB, alertas desabilitados e nenhum Facebook ou WAHA real. Origem da referência Codex é separada da inferência local F19; a [inspeção complementar somente leitura](evidence/wave2-v3-local-only-network-proof.json) confirma OLLAMA_NO_CLOUD=1, única rede interna e contêiner/run/nonce correspondentes. O caminho de código congelado injeta transporte Docker para REST em127.0.0.1:11434; falha lança InferenceError sem fallback remoto. Essa prova combina código e configuração preservada do contêiner parado, sem nova sondagem ativa de rede.

Snapshot final somente leitura:7 requisições succeeded e6 failed;8 partes succeeded,6 failed e2pending; active_request=null. Stop normal exit0, todos os contêineres próprios parados, reserva GPU liberada; pesos/banco/fila/histórico preservados. O principal não foi ativado.

## Gates e limites do aceite

Seis gates Python PASS e regressões focais atuais:50 unitários,14 integrações e9 do módulo final com repetição explícita. A [verificação final](evidence/wave2-full-final-verification-summary.json) cobre812IDs em813tentativas: full bruto811PASS/1FAIL por Chromium Socket path too long antes de abrir a página; o mesmo teste passou com TMPDIR curto em disco, sem alterar fonte/assertivas. Os [artefatos brutos](evidence/wave2-full-2026-11-13-suite-summary.json), [retry](evidence/wave2-tracking-short-tmp-retry.txt) e [audit de cópias](evidence/wave2-full-copy-audit.json) preservam a distinção. Não se somam as contagens focais sobrepostas como testes distintos. [Audit de reuso](evidence/wave2-evidence-reuse-audit.json) distingue fonte UI/migrations/pins inalterada e fronteiras de inferência reexecutadas.

As correções 6–8 consumiram3/3 desta onda, histórico cycles=8. Qualquer nova alteração de código exige escopo próprio. O veredito final aplica o contrato atual, que exige medidas/comparação/limitações publicadas, sem meta de acurácia ou validação humana independente fabricadas.

Relatório canônico final: [eval-report-2026-11-13T16-58-43Z.md](eval-report-2026-11-13T16-58-43Z.md).
