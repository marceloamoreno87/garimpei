# F15 — Operação controlada e adoção

F15 é opt-in: `GARIMPEI_ASSESSMENT_ENABLED=false` por padrão. A ativação usa configuração central e migrations aditivas; não reescreve recibos, corpos enviados ou decisões terminais. A condição manual continua na fronteira F05, com revisão otimista e CSRF. Escolha manual boa não transforma análise ausente/parcial em suficiente.

O reconciliador separado prepara/conclui até 10 ofertas a cada rodada de 5 segundos. A execução de inferência permanece na fila/capacidade `inference` de F19. Cada requisição admite até quatro fotos; galerias maiores usam uma coorte por avaliação, com geração monotônica, sem invalidar lotes irmãos nem o perfil legado. O perfil é `condition-evidence-v1`; política `condition-policy-v1`. Prompt/schema e revisão exata do modelo participam da identidade. F19 mantém concorrência, contexto, saída, fila, timeout e tentativas limitados; nenhuma rota HTML chama inferência síncrona.

Originais F14 permanecem intactos e protegidos por pins versionados. JPEG/PNG/WebP estáticos são convertidos pelo adaptador F15 em PNG independente de até 512 px; EXIF é aplicado e transparência recebe fundo branco. Hash do original e identidade de cada foto permanecem nas referências. O derivado usa a quota/registro F19 existente; temporários saem de diretório privado. Duplicatas por hash usam a mesma inferência. Fotos omitidas mantêm motivo e impedem promoção automática a boa.

Para laboratório descartável, na raiz desta worktree:

```sh
uv run --directory apps/backend --frozen --no-sync python -m tests.factories.assessment_lab
```

O processo cria configuração privada, banco/portas/mídia próprios, executa `init.sh`, pausa seu worker e imprime manifesto sanitizado. Recebe JSON por stdin: `status`, `prepare_case` (ID do corpus), `collect`, `complete`, `change_input`, `fail`, `clear_fault`, `restart`, `quit`. `status` permite conferir observação, geração, avaliação, requisições, chamadas fake e transmissões. `quit` fecha fonte/temporários e executa `stop.sh --clean` somente na instância pertencente ao laboratório. Os fakes são nomeados e o resultado aparece explicitamente como controlado na interface.

Mudança física de política/modelo pelo protocolo do laboratório permanece bloqueada até existir artefato versionado correspondente; não basta informar uma string arbitrária. A implementação calcula fingerprint de política/prompt/schema/modelo, e a integração final do coordenador acrescenta testes de vigência de versões/identidade F18. Esta worktree não declara que executou upgrade real do modelo. O laboratório também bloqueia execução de corpus reservado sem revisão humana e coordenação de runtime real.

Adoção controlada verificou que recibo confirmado, transmissão incerta e exclusão terminal anteriores mantêm corpo/ID/estado/tentativa. A ativação sem avaliação concluída conserva a assinatura pré-F15. Nova análise suficiente pode reavaliar apenas decisões pendentes pelo fluxo existente. O financeiro continua em F06/F07/F20, sem preço sugerido pela IA. Nenhum envio WhatsApp real integra a validação.
