# Implementação — F23 Docker completo e IA integrada

Implementação inicial produzida para avaliação; não é aceite completo. Fontes canônicas spec/plan/contract foram preservadas. F21 continua implemented e corpus humano independente F23 permanece ausente.

## Fases e artefatos

1. Runtime: Dockerfile runtime/quality com bases resolvidas por digest, Compose completo e redes, wrappers Docker padrão, login/WSLg sandbox, preparo/recuperação host com ownership. Legado host é opção explícita somente compatibilidade das regressões anteriores.
2. Persistência: migrations 0028/0029 para alvo tipado e revisões/consumidores; backup F17 allowlist explícita. Helper de adoção fria com inventário/checksum, pausa, cópia/restauração somente recursos próprios e destino eval vazio; ensaio mecânico real documentado, sem alegar migração real anterior.
3. Perfis e consumo: identidade, comparáveis, investigação e operação na fila F19 por HTTP privado, schemas/referências finitos, cache completo, precedência manual, rastreabilidade, filtro pré-F06 e qualificação conservadora. F15 mantém multimodal; perfis novos são textuais e declaram mídia não examinada.
4. Consulta: admissão assíncrona idempotente, CSRF, conflitos, evidência/cobertura por interesse e diagnóstico local nas páginas existentes, sem inferência GET.
5. Qualidade: testes/factories/cases produzidos. Corpus humano está explicitamente pending, sem rótulos inventados. GPU/perfis, suite quality e verificação visual em andamento na avaliação.

## Evidências preliminares

- 537 testes unitários iniciais aprovados; 19 regressões HTTP/navegação aprovadas após corrigir fallback DB e temporário externo curto.
- 4 testes tipados+hashes legados e 2 testes PostgreSQL tipados aprovados.
- 15 testes backup/privacidade aprovados após reproduzir e corrigir archive_business_schema_incomplete.
- Runtime real documentado em evidence/runtime-docker-2026-11-13.json e operations.md; helper de adoção em migration-runbook.md/evidence/migration-mechanics-*.json.
- Avaliação inicial quality: tipos PASS697 arquivos, lint FAIL5 imports. Demais gates/itens bloqueados nesta avaliação inicial; correção autorizada ciclo1.

## Limitações e pendências

Prova humana independente, aceite real positivo F21 e cadeia completa com GPU/WAHA/corpus não são substituídos por fixtures. Perfis novos usam evidência textual e referência determinística sem fotos novas; condição F15 permanece multimodal. Restauração F17 da instalação anterior e rollback completo de versão precisam prova própria além do helper mecânico. Nenhum alerta real ou login em conta real foi usado nesta implementação.
