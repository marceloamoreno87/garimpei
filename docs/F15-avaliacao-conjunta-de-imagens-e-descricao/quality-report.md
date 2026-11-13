# F15 — Qualidade real pendente

`E2E-QUALIDADE-01` continua BLOCKED. O usuário havia adiado rótulos e agora pediu revisar o pacote preparado. A preparação foi concluída; revisão humana efetiva ainda não foi recebida. Todos os rótulos continuam nulos, sem execução do conjunto reservado.

O pacote atual é descrito em `human-review-package.md`, com manifesto/template JSON congelados e cópias offline fora do Git. São21controles (18 ilustrações sintéticas identificadas nas seis categorias +3 regressões textuais) e dois casos reais/9 originais autorizados da prova F14 concluída. Há console PS5 e um brinquedo fora das famílias suportadas. Descrição/condição não capturadas permanecem desconhecidas. Categorias reais ausentes são limites a publicar, sem inventar número mínimo de anúncios reais por categoria nem promover controles sintéticos a fotografia real.

Alvo fixado: Qwen3.5 4B Q4_K_M, tag `qwen3.5:4b-q4_K_M`, digest `sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`; política `condition-policy-v1`; prompt/schema `condition-evidence-v1`. F14 e F19 estão done, comprovados por seus relatórios. Isso não substitui a comparação humana real de F15.

A retomada exerceu tokenização oficial e cadeia de validação com imagem/texto hostis sintéticos fora do corpus e transporte nomeado controlado. Essa prova comprova fronteiras, rejeição e ausência de efeitos; não comprova resistência semântica do modelo, uso da GPU ou qualidade visual. O daemon Docker observado inicialmente não tinha imagem/pesos Ollama. O coordenador preparou depois a instância F19 própria na GPU com pins aprovados e calibração exclusivamente image-a sintética; prontidão e contexto4096/VRAM estão em evidence/retomada-runtime-preparation.json. A instância foi parada normalmente, preservando pesos/banco e liberando reserva. Isso não executa exemplos humanos de F15.

Não há matriz de qualidade real, falsos bons/falsos defeitos, abstenções, GPU/RAM ou latências fria/quente medidos por F15. Campos permanecem pendentes, sem zeros fictícios. Após receber e validar rótulos, fechar ajuste/reservado e condições de execução, preparar runtime F19 próprio com artefato aprovado e coordenação exclusiva, executar o reservado real uma vez e publicar IDs/hashes/revisões, matriz, erros de evidência, limitações por categoria, recursos e latências. Não há meta numérica de precisão aprovada nem percentual de certeza a inventar.

O executor foi entregue nesta retomada (correction-cycle4.md): ingestão de export humano vinculada ao hash do manifesto, validação antes de runtime, caminho real de F14/F15/F19, relatório incremental/matriz/erros/métricas e recusa de fakes.19 unit PASS e1integração controlada comprovam preparação técnica, sem alegação de execução real do reservado.


## Método da referência — instrução atual

O usuário autorizou Codex a revisar o pacote com auxílio de IA. A autoria deve ser explícita (`Codex (IA)`) e o export usa `reference_method=ai_assisted`; isso gera concordância entre IAs, sem alegação de revisão humana independente. O método é obrigatório no arquivo e não é inferido por reviewer. O template começa nulo e não pode executar o corpus. Referências declaradas humanas usam `reference_method=human`. O relatório separa esses métodos e usa `reference` por caso; a opção assistida registra `independent_human_review=false` e não satisfaz automaticamente E2E-QUALIDADE-01 legado. Ver `reference-method.md`. Os exemplos de CLI continuam iguais; método vem do arquivo exportado, nunca de um argumento que substitua sua autoria.
