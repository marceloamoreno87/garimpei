# F15 — Correção 2 e fonte estabilizada

A verificação visual demonstrou cobertura0/0 enquanto uma foto aguardava inferência. A consulta agora congela todas as fotos pendentes com examinedFalse; a interface distingue cobertura ainda não preparada, traduz os campos citados e não declara data de análise quando nenhuma solicitação F19 ocorreu. Rótulos de tentativa/parcial/conclusão permanecem distintos.

Uma regressão adicional demonstrou que o adaptador aceitava model_digest divergente e podia atribuir o resultado ao modelo solicitado. A agregação agora confere observação/revisão, digest completo, prompt/schema e coorte/geração da resposta F19. Revisão divergente produz invalid_analysis; fakes declaram o digest alvo exato e continuam explicitamente controlled_fake, sem alegar modelo real. Nenhuma modificação em assessment_inputs.py/assessment_validity.py ou seam de identidade sob propriedade do coordenador.

Foco desses novos comportamentos:3PASS13,41s; cobertura pendenteRED→GREEN; seis gatesPASS. Rodada anterior à guarda final:16 integraçõesPASS109,72s; incluem fluxo de alerta fake semfotos→pendente→suficiente→1 mensagem com financeiro existente, adoção de recibos/transmissão incerta/terminal, reuso após fronteira de processo antes da publicação e coleta/HTTP progredindo com inferência bloqueada. Full unido é responsabilidade do coordenador e continua pendente até sua evidência; não repetido nesta worktree.

Fonte estabilizada após este checkpoint; documentação/evidências finais serão concluídas sem editar código de aplicação durante o full do coordenador. Usuário optou explicitamente por deixar labels para depois; não foi executado modelo reservado nem solicitado novo rótulo. F14/qualidade humana continuam bloqueios.
