# Coleta — conteúdo Unicode inválido não bloqueia o detalhe

Base: `c8ca8ae`, branch `fix/collection-invalid-unicode`. Correção preparada em ambiente isolado, em 12/11/2026 UTC.

O diagnóstico da instalação principal encontrou U+0000 na descrição de uma lente Canon. O PostgreSQL rejeita esse caractere no JSONB de `runtime_collectioncandidate`; a transação não registra o detalhe como concluído. A expiração do lease permite nova tentativa do mesmo detalhe, reabrindo o navegador sem avanço.

A fronteira de entrada agora representa U+0000 e surrogates Unicode isolados como U+FFFD (`�`) em título, descrição, condição e rótulos geográficos. A posição danificada continua visível, sem concatenar palavras. Acentos, emojis e o texto literal `\u0000` permanecem intactos. A normalização é compartilhada pelo parser Relay e pela fonte de avaliação; mídia com esses caracteres é rejeitada, sem reescrever URL. Identidade, link canônico e cursor mantêm suas regras anteriores. Não há captura genérica de erros do banco ou simulação de checkpoint bem-sucedido.

## Reprodução e regressão

- [RED unitário](collection-invalid-unicode-evidence/unit-red.txt): 3 FAIL e 1 PASS antes da correção; o texto de evidência conservava o caractere inválido.
- [RED do worker](collection-invalid-unicode-evidence/worker-red.txt): ciclo não terminou no prazo de 22 segundos; log privado do laboratório confirmou `DataError`. A entrada é inteiramente sintética.
- [RED do gateway de detalhe](collection-invalid-unicode-evidence/live-checkpoint-red.txt): `FacebookMarketplace.detail` → parser Relay → `PostgresCollectionRepository.stage` reproduziu `DataError: unsupported Unicode escape sequence`, com `\u0000 cannot be converted to text`, no UPDATE do JSONB. Somente a navegação externa é fake; gateway, parser, repositório e PostgreSQL são reais.
- [GREEN direcionado](collection-invalid-unicode-evidence/targeted-green.txt): **12 PASS em 23,15 s**, incluindo os testes anteriores do parser/gateway e duas integrações PostgreSQL. O worker publicou quatro anúncios, alcançou o item posterior ao detalhe danificado e publicou quatro novas observações após parada/inicialização normal. O anúncio preservou o mesmo UUID e link canônico, com uma leitura de detalhe por ciclo. A prova do gateway real gravou dois detalhes e finalizou o ciclo, com ambos os checkpoints persistidos.
- [Seis gates Python](collection-invalid-unicode-evidence/gates.txt): tipos, lint, limites, arquitetura, ciclos e código/dependências não utilizados aprovados, sem alterar gates ou registros de exceção.

Comando direcionado: `uv run --project apps/backend --frozen --no-sync pytest apps/backend/tests/unit/test_listing_unicode.py apps/backend/tests/unit/test_marketplace_parser.py apps/backend/tests/unit/test_marketplace_source.py apps/backend/tests/integration/test_collection_unicode.py -q`.

As saídas públicas apenas removem cores/espaços de fim de linha e representam NUL como `\x00`; contagens, erros e asserções são preservados.

Gates: `node scripts/run-gates.mjs`.

Os laboratórios próprios eram descartáveis, receberam segredos novos e foram encerrados com `scripts/stop.sh --clean`; nenhum manifesto próprio permanece. Não usaram Facebook autenticado, GPU ou grupo WhatsApp real. O teste não reutiliza a descrição real da lente. Nenhuma migração, contrato, progresso de feature ou fonte da instalação principal foi alterado nesta branch.

A suíte completa combinada e a retomada observada da instalação principal ficam para a integração coordenada na master; esta avaliação direcionada não declara essas etapas executadas.
