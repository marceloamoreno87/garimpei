# Red → green

Teste inicial `pytest tests/unit/test_exploration.py`: exit 2, módulo da F08 ainda ausente. Após implementar contratos, validação de contexto e formatação BRL: 2 passed.

Integração real `pytest tests/integration/test_exploration.py -q -s`: 1 passed em 30,00 s. Exercitou PostgreSQL/worker, 42 ofertas filtradas em 20/20/2, valores de F07, revisão anterior estável, publicação A, evento consumido antes de aplicar na web, classificação manual, mudança B, rollback da publicação e indisponibilidade confirmada. Massa em testes/factories/exploration.py; nenhum I/O de marketplace/WhatsApp real.

Gates locais após correções de implementação: seis grupos Python aprovados (tipos, lint/templates, limites, arquitetura, ciclos, não utilizados). A avaliação final ainda precisa registrar evidências frescas.
