# Ciclo1 — Neutralidade de mídia na primeira elegibilidade

Causa: `automatic_signature` e `semantic_candidates` removiamimage_url, mas o novo campomedia (inclusiveNone) alterava o hash da entrada automática. Uma escolha manual consumida poderia perder sua exceção somente por adoção da chave, foto nova ou URL renovada.

Correção focal: excluirmedia das duas representações semânticas, preservando texto, preço, configuração e candidatos financeiros. A metadata de mídia permanece disponível na observação/galeria; somente não é uma nova causa de primeiro alerta.

RegressãoPostgreSQL com canalWAHAfake: reprodução RED (signature-red.txt) seguida deGREEN1test/11,02s. Cenário consome escolha manual, migra ausência→mediaNone, adiciona galeria e muda URLs assinadas tanto na observação quanto nos candidatos. Hash, manual_signature, razão manual_change_only e escolha permanecem; nenhum evento, intenção, tentativa ou envio alvo é criado. Seis gates completosPASS em signature-gates.txt.

Este commit é focal para restauração segura da instalação principal; acabamentoUI, órfãos e restante da avaliação continuam no ciclo1 da branch.
