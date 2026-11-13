# F15 — Pacote de revisão humana prévia

O pacote utilizável desta retomada está fora do versionamento em `/home/marce/.cache/garimpei-evaluations/f15-human-review/index.html`. Abre arquivos locais sem aplicação, coletor ou inferência. O coordenador também disponibiliza um servidor estático próprio para revisão. O manifesto congelado e o esquema de entrega estão em `human-review-manifest.json` e `human-review-template.json`; o formulário é preparado pelo coordenador. Nenhuma predição nem rótulo humano foi preenchido pelo agente.

São23 casos:21 controles existentes (18 ilustrações sintéticas identificadas das seis categorias e três regressões textuais) e dois casos reais com9originais recuperados da prova atual F14, todos com SHA256 conferido. `controls.html` abre os controles; o índice contém os reais. O pacote antigo `human-review-real.html` fica como histórico e aponta a13assets antigos de uma instalação hoje parada; esses links não são a entrada recomendada para esta revisão.

| Caso real | Conteúdo preservado | Limite |
|---|---|---|
| `source-1633686958401669` | Título “Hot wheels T hunt supra tooned”,5 fotos locais | Brinquedo fora das seis famílias; não classificar como eletrônico. |
| `source-1502910511735697` | Título “Ps5 com 2 controles 1 Tera”,4 fotos locais | Família console pelo título; aparência não comprova funcionamento. |

A prova F14 capturou o título, mas não descrição/condição originais destes dois casos; esses campos são `null`, com nota explícita. Não preencher declaração de funcionamento por aparência. Se corrigir texto, informar a fonte autorizada e o trecho literal. Não consultar a fonte Facebook nem executar o modelo apenas para preencher a revisão. Lacunas reais em eletrônicos gerais, câmeras, computadores, fones e TVs serão declaradas no relatório de qualidade; o contrato não define um mínimo adicional de anúncios reais por categoria. Os controles das seis categorias permanecem separados de fotografia real.

Para cada caso, o humano informa `reviewer`, `reviewed_at` (RFC3339), `category`, `label=good|defect|uncertain`, `findings` e `limitations`; cada sinal contém dimensão, gravidade `light_wear|clear_defect|suspected|unknown`, componente `main|accessory|unknown` e foto/trecho que o sustenta. O template conserva `text_corrections` opcional e `split`; casos reais começam sem divisão fechada. Fechar ajuste/reservado antes de executar modelo, sem alterar rótulos após consultar predições reservadas.

Rubrica `condition-policy-v1`: `good` exige declaração explícita válida e fotos úteis suficientes sem conflito; desgaste leve permite ressalva; dano relevante claro/falha funcional é defeito; suspeita, funcionamento desconhecido ou material insuficiente exigem abstenção. Manual prevalece na aba sem fabricar análise suficiente. O usuário pediu revisar o pacote preparado; isso autoriza a preparação e apresentação, sem preencher labels por inferência nem executar reservado antes de recebê-los e validá-los.


## Método da referência — instrução atual

O usuário autorizou Codex a revisar o pacote com auxílio de IA. A autoria deve ser explícita (`Codex (IA)`) e o export usa `reference_method=ai_assisted`; isso gera concordância entre IAs, sem alegação de revisão humana independente. O método é obrigatório no arquivo e não é inferido por reviewer. O template começa nulo e não pode executar o corpus. Referências declaradas humanas usam `reference_method=human`. O relatório separa esses métodos e usa `reference` por caso; a opção assistida registra `independent_human_review=false` e não satisfaz automaticamente E2E-QUALIDADE-01 legado. Ver `reference-method.md`. Os exemplos de CLI continuam iguais; método vem do arquivo exportado, nunca de um argumento que substitua sua autoria.


## Estado final da referência e do ensaio

O usuário aprovou a referência assistida por IA em substituição ao aceite humano anterior. A revisão de23 casos foi concluída com autoria explícita, export SHAe13d908534c856b30ff2713f8383dea8b10fe8c4d803e84de7ef992c891bb496, agora preservado exatamente em evidence/ai-reference-reviewed-2026-11-13.json. O template humano/geral continua com labels nulos para preservar sua função; ele não é o arquivo preenchido de referência. Nenhum humano independente foi inventado.

A referência mantém4 good/7 defect/12 uncertain. Somente16 reservados foram executados, com0 good/7 defect/9 uncertain;7 casos de ajuste ficaram fora do benchmark. Os4 good estão no ajuste. Os hashes/splits não foram modificados após consulta ao Qwen. Origem da referência assistenteIA não tem execução local/revisão exata de serviço atestadas; F19 avaliado executou localmente em GPU própria.

O driver físico terminou, mas13 respostas foram rejeitadas, nenhuma aceita e3 partes do caso real ficaram pendentes. A medição quantitativa fria/quente de inferência nas falhas não ficou comprovada. O ensaio e os780 testes/gates são publicados em quality-report.md e no novo eval-report; F15 permanece implemented/BLOCKED no item E2E, sem nova solicitação de rótulos humanos como bloqueio.
