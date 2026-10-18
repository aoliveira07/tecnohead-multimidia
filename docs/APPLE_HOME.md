# Apple AirPlay, app Casa e HomeKit Bridge

São três superfícies diferentes:

1. O seletor AirPlay do iPhone descobre receptores mDNS/RAOP.
2. O app Casa aceita acessórios e expõe apenas controles que a implementação do receptor oferece.
3. O HomeKit Bridge do Home Assistant expõe entidades HA, que não são automaticamente o mesmo acessório AirPlay virtual.

O HomeKit Bridge existente não é prova de que um `media_player` seja alto-falante AirPlay. Um receptor AirPlay 2 precisa aparecer no seletor AirPlay do iPhone e entregar áudio; a adoção como acessório no Casa é uma verificação separada.

### Preparação real em 18/10/2026

Os players LinkPlay canônicos foram cadastrados no TecnoHead e o HomeKit Bridge exibiu os receivers `Cozinha Room` e `Piscina Room` como acessórios HomeKit. O operador adotou somente esses dois e confirmou volume da Cozinha pelo iPhone. Isso é a exposição de entidades HA pelo Bridge, não um receptor AirPlay virtual; não se devem adotar os demais media_players duplicados sem necessidade.

O volume reportado pela entidade da Piscina estava em 100% no momento da descoberta. Nenhum comando foi enviado automaticamente; reduzir o volume manualmente antes do primeiro teste.

Com a ponte v1.4, o teste deve registrar separadamente: descoberta no seletor, áudio audível, volume por destino, seleção simultânea, adição à Casa, cômodo Apple e controles efetivos. Um destino AirPlay 2 pode não se apresentar no Casa com o mesmo cartão/slider que o receiver exposto pelo HomeKit Bridge; isso é uma limitação de superfície Apple, não deve ser mascarada com acessório duplicado.

