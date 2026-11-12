# Garimpei — uso e testes para revisão de robustez

Data: 2026-11-12 UTC / 2026-11-11 em São Paulo. Escopo: verificar o produto existente para melhorar o [PRD](PRD.md). **Resultado: testes selecionados aprovados e lacunas de produto confirmadas.** Não é uma reavaliação completa de feature nem declaração de correção do aplicativo.

## Achados que mudam o planejamento

| ID | Evidência observada | Requisito resultante |
|---|---|---|
| U01 | Dos 1.563 anúncios avaliados no banco, 1.546 tinham produto indeterminado e 17 amostra insuficiente; zero estimativas calculáveis nesse conjunto | F18 deve obter atributos e comparáveis úteis e medir cobertura. Ampliar a coleta ou mudar o WhatsApp sozinho não resolve a indisponibilidade |
| U02 | Todos os 1.563 anúncios estavam sem imagem vigente; lista e detalhe real mostraram fallback | F14 exige coleta e carregamento reais vinculados ao item, além de fixture e presença de URL |
| U03 | Oferta sem identidade reconhecida mostrou “A avaliação disponível corresponde a outra variante”; o código agrupa ausência de identidade e incompatibilidade no mesmo motivo | F18 deve distinguir produto indeterminado, atributo ausente e divergência real até a mensagem apresentada ao usuário |
| U04 | A primeira abertura de ofertas respondeu 503/CONFIGURATION_READ_FAILED e “Tentar novamente” apontou para a raiz; recarga seguinte retornou 200 | F17 deve permitir recuperação na própria jornada e preservar dados já carregados, filtros e contexto. Causa do episódio permanece indeterminada |
| U05 | Acompanhamento mostrava “Coleta inicial em andamento” e horários, sem contagens por etapa ou último progresso útil. A revisão visível continha 100 ofertas enquanto o banco conservava 1.563 | F17 deve explicar estoque, revalidação de escopo e processamento, distinguindo serviço vivo de progresso útil. A diferença não prova perda de dados |
| U06 | Três descrições contraditórias foram promovidas a boa condição pela regra atual | F15 exige proteção para ressalvas/contradições também sem IA e regressões obrigatórias do corpus abaixo |
| U07 | Nenhuma intenção ou tentativa de alerta na leitura agregada; exclusões continuavam antes do canal | F16 deve mostrar motivo e acompanhar a primeira elegibilidade; F17 deve expor o funil sem equiparar grupo ativo a mensagem enviada |

Prioridade recomendada: proteger a classificação contra falsos positivos textuais, obter fotos reais, tornar os bloqueios visíveis e melhorar a identificação/amostra. A mudança de política de primeiro alerta deve conservar recibos e usar a janela de 48 horas aprovada. Ampliar autonomia somente dentro dos interesses ativos; novos nichos serão sugestões, conforme resposta do usuário nesta revisão.

## Verificações executadas

| Verificação | Resultado | Alcance |
|---|---|---|
| Unitários existentes | 196 passaram; exit 0 | Regras e adapters cobertos pela suíte atual; não abrangem automaticamente novas sondagens |
| Integrações selecionadas | 5 passaram em 119,28 s; exit 0 | PostgreSQL, worker e canal/fonte fake em ambientes descartáveis próprios |
| Gates Python | 6 grupos aprovados; exit 0 | Tipos, lint/templates, limites de dependências, arquitetura, ciclos, não utilizados |
| Testes do harness | 4 passaram; exit 0 | Regressões do harness; não comprovam qualidade de classificação ou cobertura de fonte |
| Uso da interface real | Lista, detalhe, acompanhamento, abas, paginação e filtro exercitados | Leitura sem alterar configuração, classificar ofertas ou enviar mensagens |
| Sondagens adicionais de condição | 2 controles corresponderam à expectativa; 3 casos contraditórios falharam | Experimento sintético adicional, fora da suíte pytest; falhas mantidas como evidência |

O resultado geral não é “tudo passou”. A suíte selecionada e os gates aprovados convivem com três falhas nas sondagens e as lacunas observadas no uso. Nenhuma expectativa foi afrouxada para obter aprovação.

### Integrações e propriedades verificadas

- `test_repeated_detail_errors_pause_after_three_attempts_and_recover`: três falhas consecutivas de detalhe interrompem a tentativa; a fonte recuperada volta a produzir observações.
- `test_rollback_and_restart_after_first_batch`: rollback e retomada preservam fronteiras de publicação e identidades.
- `test_killed_worker_reconciles_authorized_post_and_continues_new_deliveries`: um worker do ambiente de teste recebeu SIGKILL após autorizar o POST; retomada reconciliou o mesmo envio sem segundo POST e permitiu nova entrega independente.
- `test_incremental_comparables_complete_the_same_waiting_discovery`: a chegada tardia dos comparáveis completa a avaliação de uma descoberta aguardando dados, sem duplicar o evento.
- `test_slow_identity_analysis_does_not_hold_the_collection_publication_lock`: análise lenta de identidade não segura a trava que a coleta precisa para publicar.

A seleção verifica cinco comportamentos concretos; a suíte completa de integração/lifecycle não foi executada nesta revisão. O SIGKILL ocorreu somente no worker descartável do teste, sem interromper o worker real do usuário.

### Corpus adicional de condição

Expectativa de produto: uma ressalva explícita de funcionamento ou contradição relevante não deve ser automaticamente promovida para boa condição. A escolha final entre defeito e incerteza precisa da política correspondente; a sondagem exige apenas que o resultado não seja `good` nesses casos.

| Caso | Descrição sintética | Resultado atual | Avaliação |
|---|---|---|---|
| Controle positivo | O aparelho funciona perfeitamente. | `good` | Compatível |
| Controle negativo | O aparelho não liga. | `defect` | Compatível |
| Falha intermitente | Funciona perfeitamente, mas desliga sozinho depois de dez minutos. | `good` | Falha |
| Restrição de energia | Funciona perfeitamente, mas só funciona conectado na tomada. | `good` | Falha |
| Declarações contraditórias | Não foi testado. Funciona perfeitamente. | `good` | Falha |

A sondagem chamou diretamente `automatic_condition(Evidence(title="Aparelho usado", description=...))`, preservando o código atual. Entradas e resultados estão no [JSON do corpus](validacao-produto-2026-11-12/sondagens-condicao.json). Não foi treinado ou contratado modelo de IA, e esses casos não foram apresentados como prova de qualidade visual.

### Navegação e apresentação

A sessão própria `garimpei-prd-robustness` usou `playwright-cli` e foi encerrada ao final. O perfil Facebook e a sessão WhatsApp do usuário não foram manipulados.

- Primeira requisição de ofertas: 503; a [evidência da falha](validacao-produto-2026-11-12/falha-inicial.yml) registra mensagem e destino da ação de repetição. Medições posteriores: `/health` 200 em 0,003 s, `/health/ready` 200 em 0,028 s, `/ofertas/` 200 em 0,034 s e `/acompanhamento/` 200 em 0,020 s. São amostras isoladas, sem inferência causal sobre o 503 e sem promessa de desempenho.
- A lista recarregada mostrou dez ofertas na aba de funcionamento, todas sem imagem e estimativa. Os números das abas mudaram depois enquanto novas observações eram publicadas; não comparar instantes como se fossem uma mesma revisão.
- Detalhe consultado mostrou fallback de foto, motivo de variante incompatível, texto do vendedor e composição indisponível. Não havia diagnóstico do alerta por oferta.
- Na aba incerta, foram percorridas duas páginas de 20 ofertas cada: zero identidades repetidas entre essas páginas e mesma versão da lista. Isso verifica a amostra, sem provar todas as páginas possíveis.
- Um filtro deliberadamente sem correspondência produziu zero cards e a ação Limpar filtros recuperou o recorte. As ações não alteraram dados de negócio.
- Em 390 × 844 px, largura do documento foi 390 px: sem overflow horizontal nesse estado. O fluxo estreito é teste de reflow local, sem acrescentar acesso por celular/rede ao produto.

Screenshots inspecionados: [lista desktop](validacao-produto-2026-11-12/ofertas-desktop.png), [detalhe](validacao-produto-2026-11-12/detalhe-desktop.png), [acompanhamento](validacao-produto-2026-11-12/acompanhamento-desktop.png) e [lista estreita](validacao-produto-2026-11-12/ofertas-390px.png). Esta é verificação de jornadas e estados; não atribui nota de design nem substitui avaliação visual de uma implementação futura.

## Como reproduzir as verificações

Na raiz, com dependências e imagens do ambiente já preparadas:

```bash
uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests/unit -q
node scripts/run-gates.mjs
node --test scripts/test/harness.test.mjs
node scripts/check-harness.mjs
```

Os cinco node IDs de integração, contagens, resultados e fingerprint conjunto dos arquivos Python/testes estão no [resumo estruturado](validacao-produto-2026-11-12/resumo.json). Passar os cinco caminhos de `cases` ao mesmo comando pytest, prefixando-os por `apps/backend/`, reproduz a seleção.

Saídas preservadas: [unitários](validacao-produto-2026-11-12/unitarios.log), [integrações](validacao-produto-2026-11-12/integracoes.log), [gates](validacao-produto-2026-11-12/gates.log) e [estado agregado](validacao-produto-2026-11-12/estado-agregado.json). A leitura real usou a configuração privada existente e transação somente de leitura; seu conteúdo não está nos artefatos.

## Critérios para a próxima implementação

As etapas novas devem provar invariantes de progresso, integridade, recuperação e utilidade, conforme R01–R10 no PRD. Casos obrigatórios incluem limite de 48 horas, publicação desconhecida/futura, dados chegando fora de ordem, decisão manual concorrente, imagem ausente/trocada, contradição textual, amostra insuficiente, URL de mídia vencida, timeout de canal e queda antes/depois da autorização do envio.

É preciso especificar limites técnicos de fila, execução, recurso, retenção e custo antes de implementar os trechos correspondentes. Não há orçamento, precisão, throughput, RPO ou RTO numéricos aprovados. Os testes deverão incluir cenários com dados suficientes para produzir uma oportunidade e cenários adversos que exigem abstenção; só resultados indisponíveis não demonstram a utilidade pretendida.

O runtime e seus dados foram preservados. As mudanças desta rodada são de requisitos e evidências; fotos, classificação, identificação e política nova de alertas ainda precisam de implementação e avaliação próprias.
