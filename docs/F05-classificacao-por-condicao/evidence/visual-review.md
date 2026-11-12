# Avaliação visual F05 — design Mineral

Revisão por `frontend-ui-design`, com screenshots abertas e examinadas. As notas orientam acabamento; não substituem os resultados observáveis do contrato.

| Dimensão | Nota | Evidência e observação |
|---|---|---|
| Design (peso 2) | 8/10 | `tabs-1440.png` e `correction-failure.png`: hierarquia Bricolage/Manrope, fundo mineral, leitura de condição/manual/fonte separada; ações com rótulos claros. |
| Originalidade (peso 2) | 7/10 | Continuidade com o design aprovado; composição editorial de oferta e evidência. Fallback sem imagem é claro, porém ocupa área relevante na lista sintética. |
| Acabamento (peso 1) | 8/10 | `tabs-360.png`, `tabs-768.png`, `tabs-zoom-200.png`, `tabs-text-200.png`: sem clipping ou rolagem horizontal; nome longo preservado. Texto de 200% faz as abas empilharem sem fragmentar palavras. |
| Funcionalidade (peso 1) | 9/10 | `first-pending.png`, `correction-failure.png`, `restart-conflict.png`: espera perceptível, erro com foco, radio preservado e divergência atribuída à fonte. Setas/Home/End operados via teclado; navegação e formulário reais. |

Média ponderada: **7,83/10** = (8×2 + 7×2 + 8 + 9) / 6.

Os pares de cores reutilizam tokens do design aprovado. Foco tem contorno perceptível inclusive no aviso de erro; erro e conflito também são identificados por texto. Não há mídia quebrada: a ausência de foto coletada é apresentada com fallback textual e nome acessível. O diálogo de correção é um `details` nativo; seu estado aberto foi examinado antes de selecionar a próxima opção. Não há overlay a recortar na borda.

A verificação de zoom usa viewport de 720 CSS px e DPR 2 em contexto próprio (equivalente à área física de 1440 px em zoom de 200%); adicionalmente foi exercitado texto de 32 px em viewport de 360 px. `browser-zoom.txt` registra as medidas e os comandos. A primeira captura por override de emulação teve artefato do driver e foi substituída por contexto com viewport/DPR coerentes; a imagem final foi examinada.

Nenhum problema bloqueante de F05 observado. O espaço de imagem pode ser preenchido quando a coleta fornecer mídia utilizável; não foram inventadas fotos para os anúncios sintéticos. Favicon 404 herdado da base não interfere nas jornadas. Respostas 503 esperadas geram mensagens de rede no console, sem erro JavaScript observado.
