# Avaliação visual — F20

Modo Operate, direção Mineral existente. Inspeção por playwright-cli e exame das capturas reais em evidence/. O escopo é apresentar a composição e sua atualização; as imagens vazias refletem o cenário sintético/F14 pendente.

| Dimensão | Nota | Evidência |
|---|---:|---|
| Design | 8/10 | Verde mineral/papel claro, tipografia existente e grupo compra→venda→lucro coerentes em lista/detalhe; lucro destacado sem transformar estimativa em promessa. |
| Originalidade | 7/10 | A primeira oferta mantém composição editorial da identidade existente; os cards seguintes são convencionais. Nenhuma nova paleta ou efeito decorativo foi introduzido. |
| Acabamento | 8/10 | Rótulos integrais, centavos e sinais; reflow de uma coluna em largura estreita; medição sem overflow e com lucro maior que os demais valores. A foto ausente ocupa área considerável antes do resumo, estado aceito do cenário e não prova de F14. |
| Funcionalidade | 8/10 | Taxa e referências separadas; ausências/incompatibilidades explícitas; configuração sem logística; sondagem conserva foco/contexto e falha503 conserva leitura; aplicar exige clique. |

Média ponderada: **7,67/10** = (2×8 + 2×7 +8+8)/6. Os números documentam julgamento visual, sem substituir os observáveis do contrato.

## Evidências e medidas

- [Medições](evidence/browser-layout-observed.txt): lista/detalhe360/768/1440; no360, corpo dos valores16px, lucro27px no card e35,2px no detalhe; rótulos DOM na ordem correta, valores conhecidos completos e overflow=false.
- As capturas `*-zoom200.png` usam viewport CSS com metade da largura, equivalente ao reflow a200%. Não se afirma ter acionado zoom nativo do browser.
- [Sinais](evidence/signs-details-observed.txt) e [fração](evidence/fraction-browser-observed.txt): zero,−50 e18,37 visíveis em detalhes separados; taxa12,50%/12,63 preservada.
- [Revisões da lista](evidence/list-revisions-observed.txt): IDs/ordem/valores/foco/recorte iguais antes/depois da sondagem; clique aplica a nova revisão conservando busca e página2.
- [Falha no detalhe](evidence/detail-failed-update.txt):1000/1500/350 e revisãoA mantidos durante503, com erro e recuperação. [E2E B](evidence/e2e-revision-b-observed.txt):900/1600/380 e taxa20%/320 na revisão aplicada.
- Casos de identidade/avaliação/variante/ausência foram abertos em páginas reais separadas, mantendo compra e motivo explícito: `evidence/incompatible-*-observed.txt`.
- Configuração concluída por navegador, reaberta e reiniciada com CEP/interesses/taxa preservados. [Estado após reinício](evidence/configuration-after-restart.txt).

Capturas examinadas: `detail-360.png`, `detail-1440.png`, sinais/fração e revisãoB. Não houve menu/modal/overlay na superfície modificada; interação por teclado usa controles nativos, foco visível e atualização explícita. Tokens verificados por generate_tokens.py --check, sem alteração de sua fonte.
