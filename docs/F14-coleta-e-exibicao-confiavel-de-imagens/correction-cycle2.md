# F14 — Ciclo 2: disponibilidade após retenção

`UI-ATUALIZACAO-03`: no laboratório, o detalhe de C já removido mostrava corretamente dois tombstones e zero imagens, mas o rótulo geral ainda dizia “Fotos conservadas neste computador”. A projeção histórica mantém captura ready; a apresentação não considerava a disponibilidade atual sobreposta às fotos.

Correção focal: o rótulo distingue remoção concluída, remoção em andamento e galeria parcialmente removida. A evidência anterior fica em `evidence/controlled-removed.txt`; o resultado corrigido está em `evidence/controlled-removed-after.txt`. A regressão parametrizada nova reproduziu três falhas e um caso disponível aprovado antes da correção; depois, quatro casos passaram. Rodada dirigida de apresentação/política/financeiro: 14 PASS em 0,04s. Seis gates Python PASS.

A suíte completa de 533 testes refere-se aos 513 inputs congelados antes deste ciclo. Este delta posterior modifica somente `infra/http/media/presentation.py` na aplicação, e adiciona testes/evidências; não é apresentado como parte do full anterior. O relatório final discrimina as rodadas.
