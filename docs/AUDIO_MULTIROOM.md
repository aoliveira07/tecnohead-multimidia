# Áudio Multiroom

O áudio v1.3 é um módulo do mesmo TecnoHead Multimídia. Ele cadastra zonas por área HA, controla entidades `media_player` reais e registra a estratégia de grupo separadamente de uma eventual sessão AirPlay.

## Regras

- Cozinha e Piscina são zonas independentes e expansíveis.
- Uma zona só aceita `media_player` da própria área efetiva.
- Volume, mudo, fonte e grupo são enviados pela API oficial do Home Assistant.
- `media_player.join`/`unjoin` só são chamados após confirmação explícita do operador.
- A Piscina observa HDMI ARC. Quando a TV liga, o próprio amplificador pode assumir ARC via CEC; o App não reconfigura CEC. Uma seleção AirPlay/Spotify explícita também é encaminhada ao player, sem bloqueio adicional no App.
- O agrupamento LinkPlay e a seleção dupla do iPhone são estratégias distintas; não são executados juntos automaticamente.
- Após reinício, o App restaura configuração, mas não retoma stream, grupo ou fonte por conta própria.

## Estados expostos

O painel mostra fonte, volume observado, mudo, capabilities, grupo, disponibilidade, diagnóstico por zona e estado da ponte AirPlay. “Aceito pelo Home Assistant” não significa “som ouvido nas caixas”.

As identidades AirPlay 2 virtuais são ativadas individualmente no cadastro da zona. O App inicia Shairport/NQPTP apenas para zonas habilitadas e encaminha o PCM recebido ao respectivo `media_player` LinkPlay por uma URL local temporária. A seleção dupla no iPhone não cria grupo LinkPlay; são estratégias diferentes e mutuamente exclusivas no motor.

O MQTT publica sensores de estado e, quando a capability real é anunciada, controles Discovery de volume e mudo. Comandos MQTT não são retidos. O HomeKit Bridge/Alexa só podem expor o que o HAOS e a integração realmente suportarem.

## Compartilhar TV Piscina → Cozinha

Essa ação deve usar a Piscina como líder de `media_player.join` e a Cozinha como membro, somente depois de o novo amplificador ser identificado e anunciar suporte. Ela não converte ARC em AirPlay e não deve ser usada simultaneamente com duas saídas AirPlay do iPhone.

