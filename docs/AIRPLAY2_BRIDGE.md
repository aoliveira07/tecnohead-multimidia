# Ponte AirPlay 2 virtual

## Estado desta versão

A implementação está empacotada na release `v1.4.3`, mas a homologação física continua pendente. O App não marca áudio físico como concluído só porque um nome mDNS apareceu no iPhone. A prova precisa confirmar áudio audível no amplificador, volume/parada e a política HDMI ARC.

## Componentes fixados

- Shairport Sync: `cf6998daa1876c5a8f97128a960c8afc0e731841`, compilado com `--with-airplay-2`, OpenSSL, Avahi, FFmpeg/metadata e stdout. A imagem usa a interpolação básica embutida, porque `libsoxr-dev` não está disponível no Alpine 3.23 atual.
- NQPTP: `ab8fb67483411640fd7f1e193889482f2421c37c`, uma única instância compartilhada nos UDP 319/320.
- Duas identidades persistentes: `TecnoHead Cozinha` e `TecnoHead Piscina`, com portas RAOP distintas escolhidas pelo App (preferências 7000/7001, com varredura de conflito).
- O App usa `host_network`, `host_ipc`, `host_dbus` e `realtime` no metadata do HAOS. O mDNS continua sendo o serviço Avahi do host; o App não inicia um segundo Avahi nem altera o serviço global.
- O Ingress e a rota de stream local usam a porta 18199 no host; ela foi escolhida para não colidir com o serviço que ocupava 8099 durante a atualização.

## Caminho do áudio

1. Shairport Sync recebe AirPlay 2 e entrega PCM S32_LE, 48 kHz, estéreo ao stdout.
2. FFmpeg interno converte esse PCM para MP3 contínuo de 192 kbps.
3. O App oferece o fluxo somente durante a sessão, por uma URL local com token aleatório e validade implícita pela sessão.
4. O player LinkPlay é solicitado por `media_player.play_media` via API autenticada do Home Assistant. Não há cliente proprietário LinkPlay nem conexão direta ao BroadLink.
5. Ao parar, o App solicita `media_player.media_stop` apenas se a zona não tiver retornado para ARC; não retoma a fonte anterior automaticamente.

O formato/codec aceito pelo firmware do player ainda é critério de prova física. Se `play_media` aceitar o comando mas não houver áudio, o diagnóstico será `AIRPLAY_BRIDGE_UNSUPPORTED`, sem declarar sucesso.

## Política da Piscina

`media_player.piscina_room` permanece com prioridade `HDMI ARC` e `airplay_may_override_arc=false`. Se a fonte observada for TV/ARC/HDMI, o App bloqueia a tomada silenciosa da fonte. O teste da Piscina só deve ocorrer com ARC inativo ou depois de o operador habilitar explicitamente a substituição, em volume baixo.

## Diagnóstico e aceite

O painel informa versão dos binários, estado do NQPTP, mDNS, porta (sem publicar IP privado), endpoint por zona, clientes, bytes e último erro. Ainda assim, `streaming` significa apenas que PCM foi recebido e a chamada HA foi aceita; `physical_audio` só pode ser atualizado após o operador ouvir as caixas.

O teste deve ser executado nesta ordem: Cozinha individual, Piscina com ARC protegido, dois destinos simultâneos, volumes separados e depois app Casa. Não se deve chamar `media_player.join` durante uma seleção dupla do iPhone.

Referências: [AIRPLAY2.md](https://github.com/mikebrady/shairport-sync/blob/master/AIRPLAY2.md), [múltiplas instâncias](https://github.com/mikebrady/shairport-sync/blob/master/ADVANCED%20TOPICS/RunningMultipleInstances.md) e [integração ao app Casa](https://github.com/mikebrady/shairport-sync/blob/master/ADDINGTOHOME.md).

