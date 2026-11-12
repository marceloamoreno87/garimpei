# Catálogo Facebook Marketplace — verificação F03

Observação UTC: 2026-11-10T21:40:14Z. Driver: `playwright-cli -s=garimpei-F03-catalog` em Chromium isolado, sem importar sessão pessoal.

A consulta por ferramenta web redirecionou para login/bloqueio; isso não foi usado como prova de categoria. O navegador real abriu https://www.facebook.com/marketplace/category/electronics/ com título “New and used Electronics for sale | Facebook Marketplace | Facebook” e heading “Electronics”. O diálogo de login foi examinado e fechado pelo botão Close. A navegação lateral mostrou o link **Electronics** para `/marketplace/category/search/?category_id=479353692612078&query=Electronics&referral_ui_component=category_menu_item`.

O link foi acionado no DOM. O navegador navegou para a busca com esse `category_id`, heading “Search results” e link “Electronics” ainda presente. O trecho sanitizado está em [catalog-navigation.txt](catalog-navigation.txt). Assim, `CATEGORIA-REAL` é `479353692612078`, rótulo original `Electronics`, categoria selecionável sem ancestral necessário. 

A fonte apresentou localização pública padrão fora do Brasil; a observação comprova o filtro de categoria, não anúncios disponíveis em São Paulo, abrangência, entrega, estabilidade futura ou acesso autenticado. Nenhum anúncio foi coletado ou persistido. URLs de anúncios, informações de vendedores, cookies e material de sessão foram excluídos desta evidência. A verificação de cobertura territorial pertence à F04.

## Subcategorias navegáveis

Revisão UTC: 2026-11-10T21:58:38Z. No mesmo hub público de Electronics, o grupo “Shop by Category” apresentou estes links. O Chromium abriu cada destino com HTTP 200, URL preservada e heading igual ao rótulo. As chaves são os slugs originais observados na URL; o agrupamento vem do hub de origem.

| Chave | Rótulo/heading | URL comprovada |
|---|---|---|
| `cameras` | Cameras | https://www.facebook.com/marketplace/category/cameras/ |
| `cell-phones` | Cell Phones | https://www.facebook.com/marketplace/category/cell-phones/ |
| `computers` | Computers | https://www.facebook.com/marketplace/category/computers/ |
