# Apple AirPlay, app Casa e HomeKit Bridge

São três superfícies diferentes:

1. O seletor AirPlay do iPhone descobre receptores mDNS/RAOP.
2. O app Casa aceita acessórios e expõe apenas controles que a implementação do receptor oferece.
3. O HomeKit Bridge do Home Assistant expõe entidades HA, que não são automaticamente o mesmo acessório AirPlay virtual.

O HomeKit Bridge existente não é prova de que um `media_player` seja alto-falante AirPlay. Um receptor AirPlay 2 precisa aparecer no seletor AirPlay do iPhone e entregar áudio; a adoção como acessório no Casa é uma verificação separada.

### Estado real da instalação

Os players LinkPlay canônicos foram cadastrados no TecnoHead e o HomeKit Bridge exibiu os receivers `Cozinha Room` e `Piscina Room` como acessórios HomeKit. O operador adotou somente esses dois e confirmou volume da Cozinha pelo iPhone. Isso é a exposição de entidades HA pelo Bridge, não um receptor AirPlay virtual; não se devem adotar os demais media_players duplicados sem necessidade.

As entradas reais observadas no Home Assistant são `Cozinha Room:21080` e `Piscina Room:21081`, ambas `ReceiverMediaPlayer`. O HomeKit Bridge não transforma esse receiver no cartão de reprodução nativo de um HomePod: o controle disponível depende do tipo de acessório, dos recursos anunciados pelo `media_player` e da superfície Apple usada (cartão Casa ou Remote do iPhone).

Os destinos virtuais `TecnoHead Cozinha` e `TecnoHead Piscina` são identidades diferentes. Eles aparecem no seletor AirPlay quando a ponte está anunciando e devem ser adotados separadamente no Casa, se o iOS oferecer a opção:

1. No app Casa, abra `+` → `Adicionar Acessório` → `Mais opções`.
2. Se os destinos não aparecerem, abra Configurações da Casa → acesso a alto-falantes e TVs e permita `Qualquer pessoa na mesma rede`; não defina senha durante este teste local.
3. Adicione cada destino AirPlay virtual uma vez. Não remova os receivers `Cozinha Room`/`Piscina Room` que já funcionam pelo HomeKit Bridge.

O teste de reprodução deve ser feito com uma faixa ativa no iPhone: selecione `TecnoHead Cozinha` ou `TecnoHead Piscina` no seletor AirPlay, confirme áudio físico, abra o painel de reprodução e teste volume e parar. A seleção de ambos é feita no seletor AirPlay e não deve ser acompanhada de `media_player.join` no LinkPlay.

Com a ponte v1.4, o teste deve registrar separadamente: descoberta no seletor, áudio audível, volume por destino, seleção simultânea, adição à Casa, cômodo Apple e controles efetivos. Um destino AirPlay 2 pode não se apresentar no Casa com o mesmo cartão/slider que o receiver exposto pelo HomeKit Bridge; isso é uma limitação de superfície Apple, não deve ser mascarada com acessório duplicado.

Para um painel mais rico dentro do Home Assistant, use as entidades físicas `media_player.cozinha_room` e `media_player.piscina_room`. O HomeKit Bridge pode expor play/pause, play/stop, mudo e volume conforme os recursos anunciados; alterações na configuração de um acessório existente só aparecem no iPhone depois de remover e readicionar o acessório. Isso não cria, por si só, o cartão “Now Playing” nativo de um HomePod.

