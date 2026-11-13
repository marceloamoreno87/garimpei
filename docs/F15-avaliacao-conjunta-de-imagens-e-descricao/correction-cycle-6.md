# F15 — correção 6, primeira da nova onda

Base `4216a13`; orçamento desta onda: uma correção de três consumida. O relatório anterior e seus resultados permanecem históricos. Item tratado: `E2E-QUALIDADE-01`, sem novo veredito de aceite neste checkpoint.

A sondagem física controlada de uma parte real já persistida confirmou `done_reason=length`, `eval_count=512` e JSON truncado. O gateway rejeitava corretamente o resultado, porém descartava a razão detalhada e as métricas do envelope. A [sondagem sanitizada](evidence/wave2-baseline-length-summary.json) e a [auditoria de artefatos](evidence/wave2-baseline-length-artifacts.json) registram origem e hashes; o corpo gerado permanece privado. Essa chamada usa o perfil v1 e não constitui benchmark de qualidade.

O perfil `condition-evidence-v2` orienta concisão e agrupamento de sinais redundantes, mantendo cada defeito, ressalva e conflito decisivo com referência literal/exata. Ausência de funcionamento declarado ou identidade vira limitação, sem inventar suspeita. Estrutura do schema permanece igual, exceto const da versão. Mantidos política `condition-policy-v1`, modelo, digest, contexto 4096 e saída máxima 512. A revisão e13 e seus splits não mudaram.

O erro agora transporta subcódigo e metadados numéricos seguros até persistência/consulta pública: durações, contagens, residência anterior com correspondência de digest, tempo monotônico, contexto/VRAM e amostras GPU. Texto gerado, ferramentas e conteúdo privado não são retidos nessa telemetria. Saídas rejeitadas continuam rejeitadas, sem promoção de condição ou alerta.

Perfis antigos persistidos ficam identificados no histórico e são rejeitados antes do gateway; não podem cair no validador legado F19. Reanálise v2 cria fingerprint, geração e request próprios, preservando corpos e resultado histórico v1 sem reutilização incompatível.

Verificação:

- [Reprodução inicial de perda de telemetria](evidence/wave2-telemetry-red.txt) e [reprodução do desvio v1 para o legado](evidence/wave2-v1-profile-red.txt).
- [28 testes unitários aprovados](evidence/wave2-telemetry-unit.txt), com HTTP controlado e casos de residência ausente, digest correspondente e não verificado.
- [13 testes de integração PostgreSQL aprovados](evidence/wave2-telemetry-integration.txt): validação JSON/schema/referências, métricas consultáveis sem conteúdo privado e migração lógica v1→v2.
- [Seis gates Python aprovados](evidence/wave2-six-gates.txt). O arquivo checkpoint preserva a falha intermediária de formatação, corrigida antes da execução final.
- [Auditoria offline de tokens](evidence/wave2-profile-budget.json): 23 textos de fixture, máximo 1505 tokens com margem, estrutura do schema comparada ao baseline. Não prova que a saída física v2 caberá em 512 tokens; a preparação real ainda verifica contexto completo.

Pendentes: revisão independente, par físico frio/quente coordenado com perfil v2, eventual repetição declarada do corpus já exposto e suíte integral do coordenador. Este checkpoint não declara F15 concluída nem elimina o bloqueio histórico por antecipação.
