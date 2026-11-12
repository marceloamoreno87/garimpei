# Suplemento da calibração F17

O commit `e6bbc22` corrige a execução direta do comando de calibração do laboratório próprio. A importação dos adaptadores ocorre no contexto Django da instância; a limpeza do destino acontece uma vez por repetição. Encerrar novamente um laboratório já limpo verifica a ausência de recursos antes de aceitar um manifesto ausente.

O teste de regressão `test_direct_calibration_keeps_five_recovery_controls_and_closes_clean_destination` executou a CLI real em 321,47 s. Foram produzidas 30 medições dos adaptadores (cinco controles e cinco timeouts para fonte, valoração e canal) e cinco percursos de cópia, exportação, restauração e reconciliação verificada. Todos preservaram os recibos e registraram zero POSTs duplicados. Os recursos próprios foram encerrados, incluindo duas chamadas consecutivas de fechamento.

Evidências: [falha anterior](evidence/calibration-cli-before.txt), [regressão aprovada](evidence/calibration-cli-after.txt), [seis gates](evidence/calibration-cli-gates.txt), [medições](evidence/calibration-cli-calibration.json) e [inventário final](evidence/calibration-cli-fixture-manifest.json).

O timeout de 600 s pertence somente ao comando agregado de medição do laboratório. Os limites reais dos adaptadores permanecem 20/30/10 s; a medição agregada inclui quinze timeouts reais. Nenhuma política de produção foi habilitada.

Este suplemento supera somente a falha de execução direta e limpeza repetida registrada na avaliação de `2026-11-12T22-04-00Z`. O relatório histórico permanece intacto. `profile_confirmed=false` e `operational_enablement=false`: a matriz completa do subcomando `fault`, a confirmação do perfil e a avaliação contratual integral continuam pendentes. O sucesso desta regressão não conclui F17.
