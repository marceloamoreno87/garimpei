# Avaliação visual e de jornadas F17

Aplicado o design Mineral de docs/design e os critérios frontend-ui-design. Capturas desktop,390px e195px em evidence/ui-*.png foram inspecionadas. A captura195 é um ensaio adicional de zoom/largura extrema; não representa ergonomia confortável para uso prolongado.

| Dimensão | Nota | Evidência observada |
|---|---:|---|
| Design, peso2 |7| Fundo mineral, verde profundo e tipografia consistente; contagens e definições formam hierarquia clara no desktop/390px. A lista de diagnósticos é longa. |
| Originalidade, peso2 |6| Texto e composição específicos do funil; disposição em colunas e botões é convencional, seguindo o design existente. |
| Acabamento, peso1 |7|390px medidos com scrollWidth390; estados possuem texto, botões com foco.195px usa uma coluna, mas quebra títulos e produz rolagem vertical extensa. Não foi medida razão numérica de contraste de todos os estados. |
| Funcionalidade, peso1 |8| Counts reais, retomada, download e offline/retry funcionaram; aviso distingue confirmação no servidor de entrega/leitura. |

Média ponderada:6,83/10. Nenhuma dimensão≤3. Este julgamento subjetivo não substitui o aceite do contrato.

Playwright verificou12 armazenados/10 revalidados/8 detalhes/0 fotos atuais/6 reconhecidos/5 amostras/4 estimativas/3 elegíveis/2 confirmações em snapshot identificado. Os conjuntos se sobrepõem e a interface informa essa relação. O novo seed protege uma foto histórica sem alterar o recorte atual.

Na exploração, seis cards com filtro PlayStation conservaram texto, ordem, URL, página e versão durante perda de conexão e após Tentar novamente; evidence/ui-counts-offline.txt. No Acompanhamento, falha de rede conservou leitura anterior; banco próprio parado resultou503 na mesma rota sem primeira instalação. Retomada explícita removeu suspensão sem trocar checkpoint. Exportação gerou download completo no mesmo contexto, tráfego observado apenas127.0.0.1 e catálogo continuou informando restauração não testada.

A aplicação explícita de nova revisão disponível não foi integralmente repetida pelo navegador nesta rodada. A matriz de estados/overlays e foco de todos os elementos também não foi integralmente percorrida; permanecem pendências de avaliação, sem PASS amplo de acessibilidade. Problemas acionáveis: confirmar contraste medido e teclado completo; reduzir densidade vertical em195px mantendo as definições; completar a jornada nova revisão após retry.
