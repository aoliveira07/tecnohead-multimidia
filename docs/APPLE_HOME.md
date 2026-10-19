# Apple AirPlay, app Casa e HomeKit Bridge

São três superfícies diferentes:

1. O seletor AirPlay do iPhone descobre receptores mDNS/RAOP.
2. O app Casa aceita acessórios e expõe apenas controles que a implementação do receptor oferece.
3. O HomeKit Bridge do Home Assistant expõe entidades HA, que não são automaticamente o mesmo acessório AirPlay virtual.

O HomeKit Bridge existente não é prova de que um `media_player` seja alto-falante AirPlay. Um receptor AirPlay 2 precisa aparecer no seletor AirPlay do iPhone e entregar áudio; a adoção como acessório no Casa é uma verificação separada.

### Estado real da instalação

Os players LinkPlay canônicos foram cadastrados no TecnoHead e o HomeKit Bridge exibiu os receivers `Cozinha Room` e `Piscina Room` como acessórios HomeKit. O operador adotou somente esses dois e confirmou volume da Cozinha pelo iPhone. Isso é a exposição de entidades HA pelo Bridge, não um receptor AirPlay virtual; não se devem adotar os demais media_players duplicados sem necessidade.

As entradas reais observadas no Home Assistant são `Cozinha Room:21080` e `Piscina Room:21081`, ambas `ReceiverMediaPlayer`. O HomeKit Bridge não transforma esse receiver no cartão de reprodução nativo de um HomePod: o controle disponível depende do tipo de acessório, dos recursos anunciados pelo `media_player` e da superfície Apple usada (cartão Casa ou Remote do iPhone).

Os destinos virtuais `TecnoHead Cozinha` e `TecnoHead Piscina` são identidades diferentes. Eles aparecem no seletor AirPlay quando a ponte está anunciando e podem ser adotados separadamente no Casa, se o iOS oferecer a opção:

1. No app Casa, abra `+` → `Adicionar Acessório` → `Mais opções`.
2. Se os destinos não aparecerem, confira primeiro se o iPhone está na mesma rede e se o App anuncia as zonas. Não reduza a política de acesso a alto-falantes e TVs nem remova senha sem avaliação e autorização específicas; a Cozinha já foi adotada sem exigir nova mudança nesta rodada.
3. Adicione cada destino AirPlay virtual uma vez. Não remova os receivers `Cozinha Room`/`Piscina Room` que já funcionam pelo HomeKit Bridge.

O teste de reprodução deve ser feito com uma faixa ativa no iPhone: selecione `TecnoHead Cozinha` ou `TecnoHead Piscina` no seletor AirPlay, confirme áudio físico, abra o painel de reprodução e teste volume e parar. A seleção de ambos é feita no seletor AirPlay e não deve ser acompanhada de `media_player.join` no LinkPlay.

Com a ponte v1.4, o teste deve registrar separadamente: descoberta no seletor, áudio audível, volume por destino, seleção simultânea, adição à Casa, cômodo Apple e controles efetivos. Um destino AirPlay 2 pode não se apresentar no Casa com o mesmo cartão/slider que o receiver exposto pelo HomeKit Bridge; isso é uma limitação de superfície Apple, não deve ser mascarada com acessório duplicado.

Para um painel mais rico dentro do Home Assistant, use as entidades físicas `media_player.cozinha_room` e `media_player.piscina_room`. O HomeKit Bridge pode expor play/pause, play/stop, mudo e volume conforme os recursos anunciados; alterações na configuração de um acessório existente só aparecem no iPhone depois de remover e readicionar o acessório. Isso não cria, por si só, o cartão “Now Playing” nativo de um HomePod.

### Resultado do teste real no iPhone — Cozinha, 18/10/2026

- Captura privada às 23:03: `TecnoHead Cozinha` selecionado no seletor AirPlay; `TecnoHead Piscina` também anunciado. O operador já havia confirmado áudio físico e efeito do slider AirPlay nas zonas. A captura isolada não prova som audível nem sincronia.
- Captura privada às 23:04: no app Casa, acessório `TecnoHead` contém `TecnoHead Cozinha`, no cômodo Cozinha, modelo `ShairportSync`. O pareamento de **Cozinha passou**. Ainda não há captura do pareamento de Piscina.
- Na mesma sequência, o cartão de mídia do Casa exibiu “Controles não disponíveis”, sem capa, transporte ou volume operacionais. Portanto, **controle de mídia pelo cartão Casa não passou**. Não o confundir com o slider do seletor AirPlay, que é outra interface.

Isto é compatível com a [documentação da revisão Shairport Sync fixada](https://github.com/mikebrady/shairport-sync/blob/cf6998daa1876c5a8f97128a960c8afc0e731841/CONFIGURATION%20FLAGS.md), que declara a integração com o app Casa e o controle remoto incompletos; o [mantenedor relata status de reprodução inconsistente](https://github.com/mikebrady/shairport-sync/issues/1543). Não há um ajuste do HomeKit Bridge que injete capa, faixa, transporte ou volume dentro do **mesmo** cartão ShairportSync. Expor mais entidades do AudioCast no Bridge criaria acessórios separados, não um HomePod virtual. Não alterar pareamentos nem substituir a versão Shairport em produção apenas para tentar simular uma interface que o upstream não garante.

O controle confiável de reprodução/volume da sessão Apple deve ser testado no seletor AirPlay/Central de Controle; fonte, volume físico e grupos LinkPlay ficam no App TecnoHead ou nas entidades HA canônicas. A adoção da Piscina no Casa e o comportamento do cartão durante uma sessão ativa devem ser registrados separadamente, sem prometer controles que não apareceram.

