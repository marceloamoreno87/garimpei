# IA local para ofertas — RTX 5070

Pesquisa em fontes primárias em 2026-11-12 UTC. Decisão documental para a evolução do [PRD](PRD.md): **Qwen3.5 4B, quantização Q4_K_M, servido pelo Ollama em Docker com GPU NVIDIA**. Tag selecionada: `qwen3.5:4b-q4_K_M`. O serviço será preparado e comprovado na etapa de infraestrutura de IA; esta pesquisa não instala software, baixa pesos nem declara inferência local testada.

## Hardware observado e alcance da escolha

A leitura local informada pela sessão principal encontrou NVIDIA GeForce RTX 5070, 12.227 MiB de VRAM total, aproximadamente 8.932–9.114 MiB livres, driver 621.01 e 31 GiB de RAM no WSL2. A memória livre é uma fotografia e varia com outros programas. A tabela oficial do Ollama lista a RTX 5070 em compute capability 12.0; o driver observado supera o mínimo publicado para a classe suportada. Isso fundamenta a compatibilidade documental do runtime, sem comprovar o caminho GPU dentro do Docker desta instalação. [Hardware suportado pelo Ollama](https://docs.ollama.com/gpu).

A opção de 4B prioriza margem para o processamento das imagens, contexto e uso simultâneo do computador. É uma inferência de engenharia baseada no hardware observado e nos artefatos abaixo, não um benchmark de velocidade, qualidade ou consumo final de VRAM.

## Modelo escolhido e alternativas

| Modelo e tag explícita | Registro consultado | Papel na decisão |
|---|---|---|
| **Qwen3.5 4B — `qwen3.5:4b-q4_K_M`** | 3,3 GB no catálogo; Q4_K_M; projetor visual; Apache 2.0 | Padrão selecionado para começar com margem de memória. [Artefato oficial](https://ollama.com/library/qwen3.5:4b-q4_K_M) |
| Qwen3-VL 4B Instruct — `qwen3-vl:4b-instruct-q4_K_M` | 3,3 GB; Q4_K_M; Apache 2.0; família requer Ollama 0.12.7 ou superior | Alternativa local de comparação se a validação do Qwen3.5 mostrar problema de qualidade ou de integração. Não fazer troca silenciosa. [Artefato oficial](https://ollama.com/library/qwen3-vl:4b-instruct-q4_K_M) |
| Qwen3-VL 8B Instruct — `qwen3-vl:8b-instruct-q4_K_M` | 6,2 GB; Q4_K_M; Apache 2.0 | Candidato a avaliação posterior. Deixa menos margem no estado de memória observado; não é o padrão. [Artefato oficial](https://ollama.com/library/qwen3-vl:8b-instruct-q4_K_M) |
| Qwen3.5 9B — `qwen3.5:9b-q4_K_M` | 6,6 GB; Q4_K_M; Apache 2.0 | Alternativa maior da mesma família, sujeita à medição de qualidade e memória. [Artefato oficial](https://ollama.com/library/qwen3.5:9b-q4_K_M) |

Esses números são os tamanhos exibidos no catálogo, sujeitos a revisão de tag. **Não são o consumo total em execução.** Registrar manifesto/digest completo efetivamente baixado na implementação; o digest curto exibido para o 4B nesta consulta foi `d8b0f5e9760c`. O valor de catálogo consultado pelo navegador foi 3,3 GB; outra revisão da tag pode exibir valor diferente. Não usar `latest`, pois não identifica a configuração escolhida. [Tag exata do modelo selecionado](https://ollama.com/library/qwen3.5:4b-q4_K_M).

O model card oficial confirma entrada multimodal de texto e imagem e licença Apache 2.0. A família declara cobertura multilíngue; a precisão em descrições de usados em português brasileiro e em fotos de danos ainda precisa ser medida no corpus do Garimpei. As tabelas de benchmarks de modelos grandes da família não comprovam o desempenho do 4B neste produto. [Model card Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B).

## Execução Docker e perfil inicial

Usar a imagem oficial `ollama/ollama`, com acesso NVIDIA e armazenamento persistente dos pesos. O procedimento oficial usa o NVIDIA Container Toolkit e a opção de GPU do Docker. No Docker Desktop para Windows, o caminho documentado de passagem da GPU para contêiner Linux usa backend WSL2. Na instalação futura, identificar primeiro qual daemon Docker atende o projeto e validar o caminho correspondente. [Ollama em Docker](https://docs.ollama.com/docker), [GPU no Docker Desktop](https://docs.docker.com/desktop/features/gpu/).

A versão **0.17.5** é o marco documental de disponibilidade da série pequena Qwen3.5 (incluindo 4B) nas notas oficiais; também trouxe correções de importação GGUF e divisão GPU/CPU. Isso não a torna a versão escolhida para uma instalação nova. A release estável consultada em 2026-11-12 foi **v0.40.16**, publicada em 2026-11-09; ela é a referência inicial para resolver a imagem por digest e executar o smoke test da F19. Evitar release candidate e não declarar digest de imagem antes de resolvê-lo. [Suporte aos pequenos modelos em v0.17.5](https://github.com/ollama/ollama/releases/tag/v0.17.5), [release estável v0.40.16](https://github.com/ollama/ollama/releases/tag/v0.40.16).

No WSL, o driver de GPU do Windows é o caminho documentado; não instalar um driver NVIDIA Linux de display dentro da distribuição para tentar habilitar a placa. A detecção atual por `nvidia-smi` não substitui o teste do contêiner. [Guia CUDA no WSL da NVIDIA](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).

Perfil técnico inicial proposto para validação:

- Um modelo carregado: `OLLAMA_MAX_LOADED_MODELS=1`.
- Uma inferência por vez: `OLLAMA_NUM_PARALLEL=1`; a fila persistente do Garimpei controla o trabalho de negócio.
- Contexto explícito de 4.096 tokens (`OLLAMA_CONTEXT_LENGTH=4096` e/ou `num_ctx` correspondente), com texto selecionado e entrada visual limitada. Não truncar evidência relevante silenciosamente; dividir a análise e conservar referências quando necessário.
- Começar com uma imagem por chamada e agregação versionada por anúncio. O número de fotos, resolução, tokens visuais, limite de saída e timeout precisam de teste e contrato antes da integração. Uma foto não examinada não pode ser apresentada como analisada.
- Solicitar resposta direta, sem raciocínio longo, quando o modelo/runtime fixado aceitar `think: false`; verificar os valores disponíveis por `/api/show` e exercitar a requisição. Isso é configuração de serviço, não prova de menor latência neste hardware.

Os controles de concorrência são documentados pelo Ollama. Contexto e paralelismo aumentam a memória necessária; o contexto máximo anunciado pelo modelo não é uma meta para esta placa. O perfil de 4K acompanha a faixa inicial documentada pelo runtime para VRAM abaixo de 24 GiB. [FAQ e controles do servidor](https://github.com/ollama/ollama/blob/main/docs/faq.mdx), [contexto e memória](https://docs.ollama.com/context-length), [parâmetro de thinking da API](https://docs.ollama.com/api/chat).

## Inferência local e contrato de análise

A aplicação envia texto e bytes das fotos ao endpoint local, mantendo cookies, perfil do navegador, QR e dados do grupo fora da entrada do modelo. A API REST do Ollama aceita imagens codificadas em base64 junto da mensagem; a validação exige fotos realmente obtidas e associadas à oferta correta. [Entrada de imagens na API](https://docs.ollama.com/capabilities/vision).

Exigir saída com schema e validação na aplicação: aparência provável, sinais de dano, trecho textual/foto que sustentam cada sinal, contradições, atributos comprovados/ausentes e necessidade de revisão. JSON válido não garante conclusão verdadeira. A decisão de condição, a regra de abstenção e a precedência da escolha manual pertencem ao Garimpei. [Saídas estruturadas do Ollama](https://docs.ollama.com/capabilities/structured-outputs).

O modelo não determina preços por conhecimento interno e não faz aritmética financeira autoritativa. Preço de compra vem do anúncio; preço estimado de venda continua dependente de comparáveis rastreáveis; lucro continua calculado pelo domínio. A IA pode ajudar a extrair atributos e examinar fotos, sem fabricar capacidade, SKU, funcionamento ou valor de venda quando faltam evidências. Estas são decisões de produto da presente revisão, não promessas do fornecedor.

A operação selecionada é estritamente local, com `OLLAMA_NO_CLOUD=1`, sem fallback remoto. O download inicial da imagem/pesos é uma etapa de preparação que requer rede; depois de preparado, testar inferência sem acesso externo. Se publicar a API no host, usar porta loopback isolada por ambiente; não expor a API diretamente ao navegador nem à rede. O modo local e a desativação de recursos cloud são documentados pelo projeto Ollama. [Modo local do servidor](https://github.com/ollama/ollama/blob/main/docs/faq.mdx).

## O que falta comprovar na implementação

1. Fixar versão e digest da imagem Ollama compatível com a tag selecionada, manifesto/digest dos pesos e versões do ambiente. Não confundir a versão mínima da família Qwen3-VL com um requisito suficiente para Qwen3.5.
2. Provar acesso à RTX 5070 dentro do contêiner e carregamento do modelo na GPU; inspecionar `ollama ps`, memória e estado antes/durante/depois da chamada. CPU ou divisão CPU/GPU deve aparecer como degradação, sem alegação de aceleração plena. O runtime documenta essa inspeção. [Contexto e offloading](https://docs.ollama.com/context-length).
3. Medir pico de VRAM, RAM, tempo frio/quente e comportamento com outros programas usando a placa. Medir fotos e descrições reais autorizadas, com dados sintéticos identificados nos controles. Não há latência ou consumo máximo comprovados nesta pesquisa.
4. Executar o corpus humano de F15, incluindo defeitos, textos contraditórios, fotos ausentes/genéricas, modelo/variante errados e danos não visíveis. Comparar erros e abstenções; modelo maior só é promovido se demonstrar melhoria útil e margem de memória.
5. Exercitar OOM, modelo ausente, resposta inválida, timeout, reinício e cache por entrada/modelo/prompt. Preservar dados, decisões manuais e recibos; análise indisponível não promove oferta a boa condição e não interrompe coleta ou leitura da interface.
6. Provar ausência de chamadas de inferência externa e que a análise usa somente o serviço local escolhido. Não enviar mensagens ao WhatsApp como efeito desta pesquisa ou do teste de inicialização do modelo.

A escolha concreta é Qwen3.5 4B Q4_K_M/Ollama Docker; sua aprovação operacional depende dessas provas na GPU real. O hardware e as fontes justificam a seleção inicial, mas não equivalem a benchmark ou implementação concluída.
