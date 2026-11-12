# Verificação visual — F12

Direção preservada: editorial clara com verde mineral, Bricolage Grotesque e Manrope conforme docs/design. Jornada via playwright-cli em ambiente descartável; 1440×1000 e 390×844. Dados e imagens são sintéticos, provenientes do cenário F08. A prova de fonte real está em arquivo separado, sem screenshots de conta autenticada.

| Dimensão | Nota | Evidência |
|---|---:|---|
| Design | 7 | Hierarquia de título, compra e lucro preservada; lucro único reduz competição entre modalidades. |
| Originalidade | 6 | Identidade editorial consistente, com navegação e formulário convencionais herdados do produto. |
| Acabamento | 8 | Sem overflow horizontal nas verificações; rótulo longo de lucro e opções de categorias quebram corretamente em celular. |
| Funcionalidade | 8 | Taxa salva sem campo de frete; seis categorias válidas e rota indisponível identificada; detalhes exibem cinco referências e fórmula coerente. |

Média ponderada: 7,0, com peso dois para design/originalidade. Não equivale a auditoria integral de acessibilidade.

Evidências: `ui-offers-desktop.png`, `ui-settings-desktop.png`, `ui-settings-mobile.png`, `ui-offer-detail-desktop.png`, `ui-offer-detail-mobile.png` e `ui-validation.json`. Exemplo observado após salvar taxa de 12,50%: revenda R$ 1.700, compra R$ 1.000, taxa R$ 212,50, lucro potencial R$ 487,50 antes de frete/transporte.

Pontos de atenção: o aviso de conexão ocupa área relevante antes das ofertas quando a sessão não está configurada no cenário; muitos interesses tornam o formulário móvel longo. Nenhuma dessas observações impediu a jornada de configuração, exploração ou acesso aos detalhes.
