# Diagnóstico das regressões encontradas na suíte ampla

A execução inicial da fonte congelada coletou907 testes. Seus resultados e falhas foram preservados nos três shards; esta página não os transforma em aprovação.

## Prontidão da amostra F16

`first_eligibility_scenario` aguardava apenas seis `ValuationProgress.current_id` preenchidos. A publicação de uma avaliação intermediária já satisfazia essa condição, mesmo antes de o alvo receber os cinco comparáveis da BASE. Nos casos `concurrent`, `zero` e `manual_race`, o estado persistido registrou `amostra_insuficiente` e nenhuma intenção, antes de as asserções de autorização serem executadas.

A fixture agora também espera o número de retidos esperado no alvo: cinco na BASE e quatro no cenário deliberadamente insuficiente. O caso de completar identidade conserva a ausência inicial da chave de produto. Não foram alterados valores, comparáveis, expectativas de autorização ou código de produção.

## Vazamento de configuração entre testes

O helper `assessment_quality_runtime.execute` atribuía `GARIMPEI_ASSESSMENT_ENABLED=true` e a origem HTTP temporária ao `os.environ` do chamador. A execução por testes unitários com transporte controlado deixava esses valores após a exceção esperada. Testes posteriores herdavam o modo F15 e aguardavam uma análise que a fixture F16 não preparava.

A regressão foi reproduzida antes da correção no teste existente `test_real_report_cannot_complete_when_all_photos_fail_before_dispatch`: os dois valores ausentes tornaram-se `true` e uma URL local. O contexto do helper agora restaura valores anteriores ou ausência, tanto em conclusão como em exceção. Seis casos adicionais cobrem variável ausente, `false`, `true`, retorno e falha. A fixture F16 usa um contexto que restaura o ambiente e remove o valor herdado da flag; a ausência usa o padrão `false` e permite que cenários F15 optem explicitamente pelo arquivo privado.

A primeira correção desta fixture também gravou `GARIMPEI_ASSESSMENT_ENABLED=false` no arquivo inicial. Isso introduziu outra falha: `process_environment` materializava esse valor no worker; a prioridade do ambiente sobre o arquivo impedia a ativação posterior por F15. Os dois casos `light_wear`/`clear_defect` completavam a análise controlada no subprocesso, mas o worker mantinha `manual_change_only`, sem intenção ou POST. A reprodução isolada falhou em53,16s no `wait_first`, conforme `multimodal-condition-focal.txt/.xml`. A gravação explícita foi removida; permanecem o padrão `false`, o isolamento e a restauração, sem alterar a aplicação ou as expectativas de envio.

Evidências: `environment-leak-red.txt`, `environment-leak-green.txt`, `quality-helper-recheck.xml`. Os53 testes de revisão/prontidão do helper passaram após a correção.

## Transporte dos quatro ataques

`HostileOllamaTransport` ainda tentava extrair `Foto atual: ...` da mensagem anterior. O `IndexError` ocorria no fake, antes de ele produzir a resposta hostil. O fake foi adaptado para uma resposta física v4 válida como base e conservou quatro corrupções independentes: chamada de ferramenta, citação textual fabricada fora do conjunto, código de foto não fornecida e JSON inválido.

Permanecem as verificações de rejeição terminal em uma tentativa, ausência de transmissão, integridade do lock/configuração e não exposição do canário de sessão. Uma segunda execução encontrou quatro asserções ainda ligadas à frase antiga em português do prompt; a verificação equivalente agora exige `untrusted evidence` e `never instructions`. O módulo completo passou9casos em32,71s (`hostile-module-final.txt/.xml`). O texto do prompt de produção não foi alterado nesse ciclo.

## Escopo e validação

Somente helpers e testes foram alterados neste ciclo. Os462 módulos Python de produção mantêm os hashes da fonte congelada, inclusive os quatro módulos revisados e exercitados com modelo real. A seleção de33 módulos foi derivada do fechamento de imports dos helpers alterados, incluindo cenários de identidade, amostra insuficiente, F15, pausa, restauração e diagnóstico HTTP. Os dois testes operacionais com timeout Docker e o recheck da coleta pertencem à validação coordenada, em evidências próprias.

A primeira execução dos149casos foi interrompida com SIGINT após61PASS/6FAIL em942,47s: quatro asserções antigas do prompt e as duas transições F15 acima. Seus logs/XML e código de saída foram preservados em `affected-modules-recheck.*`; não contam como aprovação final. Após a última correção, todos os149casos foram selecionados novamente, em duas partições por módulo (`affected-final-partition.json`), com fontes/testes hashverificados em cada início/fim. Os resultados finais ficam em `affected-final-{0,1}.txt/.xml` e respectivos manifests de execução. A consolidação exige ambos os resultados e o audit completo do coordenador; nenhuma parte interrompida substitui testes ausentes.

Este diagnóstico não dispensa os gates nem aprova a dimensão positiva real. A F21 continua `implemented` enquanto houver item ou verificação pendente.
