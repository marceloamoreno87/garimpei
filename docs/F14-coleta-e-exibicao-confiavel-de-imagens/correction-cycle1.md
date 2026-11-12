# F14 — Ciclo1: recuperação, isolamento e apresentação

Além das correções focais de assinatura e fragmentos já registradas, foram corrigidos:

- galeria por lote com duas consultas, preservando o limite de dez consultas da projeçãoF08; nenhuma consulta preguiçosa de JSON de ciclo;
- capture_id técnico fora da assinatura pública, conservando a revisão quando só há reobservação idêntica;
- testes de migração leem modelos históricos enquanto o schema é antigo e restauram a ponta antes de chamar aplicação atual; preservadas todas as verificações de recibos/histórico;
- órfãos temporários/renames sem commit só são removidos após o lease e sem operação ativa, sob a mesma trava de quota; versões confirmadas são conservadas;
- raiz de mídia tem marcador privado environment_id: outra instância não pode adquirir/gravar/limpar essa raiz. Raiz personalizada preexistente sem proprietário exige verificação antes da adoção; cópias antigas continuam legíveis. A raiz padrão identificada por environment_id aceita adoção da instalação anterior;
- renovação em menor resolução conserva a melhor cópia e não deixa asset disponível sem associação, preservando enumeração de backup;
- recuperação de observação ultrapassada retorna409;
- estado desconhecido continua explícito quando o armazenamento ainda aguarda configuração;
- quebra do valor financeiro indisponível remove overflow no detalhe estreito; galeria continua com imagens e ações contidas.

Validação:6gatesPASS;16testes de transporte/propriedade/PostgreSQLPASS27,97s; regressãoF08completaPASS48,38s. Outras três regressões de migração/projeção passaram na rodada dirigida anterior; o único FAIL dessa rodada era texto de estado desconhecido, posteriormente corrigido e reexecutado em F08.

A suíte completa anterior foi interrompida após4FAIL/53PASS em14m12s e teve entradas alteradas durante correção; seu resultado é diagnóstico, não evidência de aprovação global. As quatro causas estão descritas acima. Suíte final exige sincronização com master e congelamento dos inputs.

Verificação visual:390/1440px, imagens originais1280×960 e1000×800 locais e thumbnails640px; erroHTTP503 de imagem conservou texto/origem e mostrou fallback. CSSzoom200% foi ensaio auxiliar; reflow foi verificado separadamente em viewportCSS195/720px (equivalência geométrica de390/1440 a200%, não automação do zoom nativoChrome), sem overflow e com fotos/ações contidas. Capturas foram inspecionadas; não há certificação formal de acessibilidade.

Fonte real: as leituras coordenadas demonstraram o fragmento de mesmoid e motivaram a correção; carregamento real/variantes ainda aguardam a instalação principal atualizada. Não há done.
