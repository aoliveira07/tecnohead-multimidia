# Apple AirPlay, app Casa e HomeKit Bridge

São três superfícies diferentes:

1. O seletor AirPlay do iPhone descobre receptores mDNS/RAOP.
2. O app Casa aceita acessórios e expõe apenas controles que a implementação do receptor oferece.
3. O HomeKit Bridge do Home Assistant expõe entidades HA, que não são automaticamente o mesmo acessório AirPlay virtual.

Nesta execução não houve iPhone disponível para emparelhamento e a ponte AirPlay não foi compilada, portanto nenhum destino foi declarado como visível ou compatível com Casa. O HomeKit Bridge existente não é prova de que um `media_player` seja alto-falante AirPlay.

Quando a ponte for desbloqueada, o teste deve registrar separadamente: descoberta no seletor, áudio audível, volume por destino, seleção simultânea, adição à Casa, cômodo Apple e controles efetivos. Não se deve criar acessório duplicado com o mesmo nome para mascarar uma limitação.

