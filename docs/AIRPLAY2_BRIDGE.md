# Ponte AirPlay 2 virtual

## Estado desta versão

A implementação está empacotada na release `v1.4.13`. A homologação física continua sendo registrada por zona: o operador precisa confirmar seleção, áudio audível, volume e parada. O App não marca áudio físico como concluído só porque um nome mDNS apareceu no iPhone. Se o processo Shairport Sync morrer na inicialização, a interface mostra o código e a cauda sanitizada do diagnóstico em vez de manter “Visível no AirPlay”.

## Componentes fixados

- Shairport Sync: `cf6998daa1876c5a8f97128a960c8afc0e731841`, compilado com `--with-airplay-2`, OpenSSL, Avahi, FFmpeg/metadata e stdout. A imagem usa a interpolação básica embutida, porque `libsoxr-dev` não está disponível no Alpine 3.23 atual.
- NQPTP: `ab8fb67483411640fd7f1e193889482f2421c37c`, uma única instância compartilhada nos UDP 319/320.
- Duas identidades persistentes: `TecnoHead Cozinha` e `TecnoHead Piscina`, com portas RAOP distintas escolhidas pelo App (preferências 7000/7001, com varredura de conflito).
- O App usa `host_network`, `host_ipc`, `host_dbus` e `realtime` no metadata do HAOS. Primeiro tenta o Avahi do host pelo D-Bus; quando ele não existe, inicia um único D-Bus/Avahi compartilhado dentro do App. Nunca inicia um Avahi por zona nem altera o serviço global do HAOS.
- O painel e a API informam `host_avahi` ou `private_avahi`, a saúde do processo auxiliar e uma cauda de log sanitizada. Se o host Avahi existir mas negar acesso, a ponte fica bloqueada em vez de iniciar um segundo respondente.
- O Ingress e a rota de stream local usam a porta 18199 no host; ela foi escolhida para não colidir com o serviço que ocupava 8099 durante a atualização.

## Caminho do áudio

1. Shairport Sync recebe AirPlay 2 e entrega PCM S32_LE, 48 kHz, estéreo ao stdout, em ganho pleno.
2. FFmpeg interno converte esse PCM para MP3 contínuo de 192 kbps.
3. O App oferece o fluxo somente durante a sessão, por uma URL local com token aleatório e validade implícita pela sessão.
4. O player LinkPlay é solicitado por `media_player.play_media` via API autenticada do Home Assistant. Não há cliente proprietário LinkPlay nem conexão direta ao BroadLink.
5. Ao parar, o App solicita `media_player.media_stop` apenas se a zona não tiver retornado para ARC; não retoma a fonte anterior automaticamente.

## Volume AirPlay e volume físico LinkPlay

O fluxo PCM não aplica a atenuação do slider do iPhone. Cada instância usa `ignore_volume_control = "yes"`; o gancho nativo `run_this_when_volume_is_set` envia o valor AirPlay por socket Unix privado ao App, que o converte do intervalo `-30 dB..0 dB` para `0..100%` e faz uma chamada autenticada `media_player.volume_set` à entidade LinkPlay da mesma zona. O evento Shairport `ssnc/pvol` e a FIFO de metadados permanecem como fallback. Assim, o ganho digital permanece alto e o amplificador AudioCast/LinkPlay continua sendo o estágio que altera o volume audível.

O limite máximo configurado da zona continua valendo. Com limite de 100%, o valor do iPhone chega integralmente ao player; com limite menor, o App aplica o teto sem aumentar o ganho do PCM. O painel do App e o Home Assistant permanecem controles físicos equivalentes. O diagnóstico registra a última porcentagem recebida e o resultado da chamada, sem registrar payload de áudio ou dados privados.

Na v1.4.12 o caminho inverso também foi implementado: alterações observadas no `volume_level` do `media_player` — inclusive pelo AudioCast — são encaminhadas à sessão AirPlay ativa pelo comando nativo `org.gnome.ShairportSync.RemoteControl.SetAirplayVolume`. Na v1.4.13, o App só considera uma alteração nova quando ela supera a tolerância de arredondamento ou chega fora da janela curta de eco; isso impede que o valor corrigido pelo amplificador volte como uma nova ordem e cause oscilação. O App só faz isso enquanto aquela zona tem uma sessão AirPlay ativa; não altera o volume de uma sessão encerrada. Como os nomes D-Bus do Shairport Sync são fixos, cada endpoint usa um barramento de sessão privado, enquanto Cozinha e Piscina continuam compartilhando somente o barramento Avahi/mDNS.

O formato/codec aceito pelo firmware do player ainda é critério de prova física. Se `play_media` aceitar o comando mas não houver áudio, o diagnóstico será `AIRPLAY_BRIDGE_UNSUPPORTED`, sem declarar sucesso.

## Política da Piscina

`media_player.piscina_room` continua identificado com prioridade operacional `HDMI ARC`, mas essa prioridade é observada, não um bloqueio do App. Quando a TV liga, o amplificador pode assumir ARC por seu próprio CEC/ARC. Quando o operador seleciona AirPlay/Spotify explicitamente, o App encaminha `media_player.play_media` ao Home Assistant mesmo que a última fonte observada seja HDMI/ARC; o App não envia uma troca automática concorrente. Ao parar, se o player já tiver retornado a ARC, o App não envia `media_stop` para não interromper a TV.

## Diagnóstico e aceite

O painel informa versão dos binários, estado do NQPTP, mDNS, porta (sem publicar IP privado), endpoint por zona, clientes, bytes e último erro. Ainda assim, `streaming` significa apenas que PCM foi recebido e a chamada HA foi aceita; `physical_audio` só pode ser atualizado após o operador ouvir as caixas.

O teste deve ser executado nesta ordem: Cozinha individual, Piscina com o amplificador livre para arbitrar ARC, dois destinos simultâneos, volumes separados e depois app Casa. Em cada zona, mover o slider do iPhone deve alterar também o valor do player no AudioCast/LinkPlay; em seguida, alterar o volume no AudioCast e confirmar que o slider do iPhone acompanha. Não se deve chamar `media_player.join` durante uma seleção dupla do iPhone.

Referências: [AIRPLAY2.md](https://github.com/mikebrady/shairport-sync/blob/master/AIRPLAY2.md), [múltiplas instâncias](https://github.com/mikebrady/shairport-sync/blob/master/ADVANCED%20TOPICS/RunningMultipleInstances.md) e [integração ao app Casa](https://github.com/mikebrady/shairport-sync/blob/master/ADDINGTOHOME.md).

