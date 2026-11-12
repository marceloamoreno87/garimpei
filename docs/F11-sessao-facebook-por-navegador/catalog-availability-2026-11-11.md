# Limitação operacional observada no catálogo Facebook

Na reavaliação conjunta F09/F10/F11, o perfil autenticado foi reaberto, a fonte leu 24 anúncios de uma categoria nativa válida, abriu um detalhe com preço/identidade válidos e a aplicação persistiu 141 ofertas. Nenhum login/checkpoint apareceu nesses probes. Isso comprova continuidade de perfil e coleta real, sem garantir completude de todo o catálogo F04.

A categoria configurada `cell-phones` redireciona para o browse geral, sem template/feed de busca. A rota nativa declarada no catálogo e a variante regional foram conferidas com o perfil autenticado; a sessão continuou válida, mas a categoria não foi exposta. Não foi encontrado um identificador nativo substituto verificável. Não foi fabricado um resultado vazio ou substituída a categoria por busca textual mais ampla.

O ciclo que contém essa unidade permanece parcial. O marco inicial completo ainda não estava registrado na observação real; portanto, esta avaliação não atesta que os alertas de uso normal já tenham ultrapassado a carga inicial silenciosa. Os testes F09 comprovam essa regra, e o envio real ocorreu com evento sintético elegível e banco isolado, sem alterar os dados de operação.

Próxima investigação operacional: atualizar o mapeamento dessa categoria a partir de um vínculo/ID efetivamente disponibilizado pela fonte, ou obter decisão explícita do operador sobre seus interesses. Não remover automaticamente uma categoria escolhida, não liberar a carga inicial manualmente e não tratar uma rota indisponível como sessão expirada. Essa limitação F04 foi mantida separada dos critérios F11 de login/persistência/retomada e foi divulgada no relatório e na resposta ao usuário.

Evidências sem credenciais: `evidence/revalidation-2026-11-11T21-16-51Z/{facebook-real-source,facebook-app-observation,unavailable-cell-category}.json`.
