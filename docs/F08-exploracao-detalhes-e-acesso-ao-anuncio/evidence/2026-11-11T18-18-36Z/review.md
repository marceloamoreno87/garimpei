# Revisão local da F08

Escopo: implementação, migração, composição web/worker, contratos F04–F07, falhas de I/O, concorrência, revisões e UI. Revisão feita nesta sessão, sem agente independente, conforme escopo solicitado. Não houve commit base no checkout; a inspeção usou os arquivos alterados e fontes canônicas, sem alegar diff contra um commit inexistente.

Conferidos: dependências voltadas ao domínio; DI na composição; migração aditiva; trava adquirida antes do snapshot; publicação/rollback atômicos; leitura e contagem na mesma transação; ordenação antes de paginação; overlay manual isolado; links HTTPS e escape de texto; falha 503 conserva DOM; abort de navegação/polling antigo; retenção preserva head; distribuição contém ativos e migration.

Achados corrigidos durante implementação: tratamento global de erro HTMX reativava swap da lista; imagem com aspect-ratio/min-height excedia sua coluna em 768 px; suíte F05 assumia leitura imediata de dados agora publicados no worker; relógio de F07 avançava durante scan degradado e congelava antes de next_attempt_at. As regressões reais e a espera pelo commit mantêm as expectativas de negócio originais.

Limites deliberados: projeções copiadas por revisão, medidas na massa de 59 registros; não há benchmark de grande escala. Fonte, catálogo Áudio e navegação externa são sintéticos conforme contrato. Não houve login ou acesso de marketplace/WhatsApp real. Sem questões de produto pendentes identificadas na inspeção; conclusão depende do gate Python completo final.
