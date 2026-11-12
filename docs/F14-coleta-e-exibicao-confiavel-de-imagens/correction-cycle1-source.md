# Ciclo1 — Galeria em fragmento separado da fonte

A prova real coordenada em12/11/2026 encontrou o carrossel em outro fragmento do MESMOid, separado do objeto com título/preço. Selecionar somente o maior objeto omitia fotos válidas; duas leituras anteriores produziram galeria desconhecida.

`FacebookMarketplace.detail` agora preserva o objeto verificado e acrescenta exclusivamente listing_photos/primary_listing_photo de fragmentos com idexatamenteigual. Outro anúncio/recomendação é excluído em regressão. O fastpathPDP só retorna quando também há evidência de galeria desseid; sem ela a página completa é lida no mesmo navegador e com o tempo restante. Lista vazia comprovada continua válida como ausência, sem obrigar navegaçãoextra.

A correlação de variantes usa somente iddefoto explícito (nuncaNone ou posição). Variante da principal e da galeria para o mesmoid são combinadas e ordenadas por área conhecida; preservam-se no máximo3candidatas, com parcialidade se excedido.

Gates6PASS.22testes de fonte/browser/mídia/assinatura passaram em49,30s na branch com os demais ajustes do ciclo1 ainda pendentes de commit; a prova controlada não substitui a obtenção real. A avaliação completa e a suíte da união final ainda estão pendentes.
