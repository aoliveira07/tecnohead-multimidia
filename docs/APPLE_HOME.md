# Apple AirPlay, app Casa e HomeKit Bridge

São três superfícies diferentes:

1. O seletor AirPlay do iPhone descobre receptores mDNS/RAOP.
2. O app Casa aceita acessórios e expõe apenas controles que a implementação do receptor oferece.
3. O HomeKit Bridge do Home Assistant expõe entidades HA, que não são automaticamente o mesmo acessório AirPlay virtual.

Nesta execução não houve iPhone disponível para emparelhamento e a ponte AirPlay não foi compilada, portanto nenhum destino foi declarado como visível ou compatível com Casa. O HomeKit Bridge existente não é prova de que um `media_player` seja alto-falante AirPlay.

### Preparação real em 18/10/2026

Os players LinkPlay canônicos foram cadastrados no TecnoHead e o HomeKit Bridge passou a exibir os receivers `Cozinha Room` e `Piscina Room` como acessórios HomeKit. Isso é a exposição de entidades HA pelo Bridge, não um receptor AirPlay virtual. A adoção no app Casa, a atribuição dos cômodos Apple e os controles efetivos ainda exigem confirmação manual no iPhone.

O volume reportado pela entidade da Piscina estava em 100% no momento da descoberta. Nenhum comando foi enviado automaticamente; reduzir o volume manualmente antes do primeiro teste.

Quando a ponte for desbloqueada, o teste deve registrar separadamente: descoberta no seletor, áudio audível, volume por destino, seleção simultânea, adição à Casa, cômodo Apple e controles efetivos. Não se deve criar acessório duplicado com o mesmo nome para mascarar uma limitação.

