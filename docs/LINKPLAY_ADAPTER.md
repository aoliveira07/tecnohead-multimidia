# Adaptador LinkPlay via Home Assistant

O adaptador v1.3 é deliberadamente limitado à entidade `media_player` exposta pelo Home Assistant. Não existe cliente TCP/HTTP proprietário no App, não há descoberta de IP para áudio e a restrição de não falar diretamente com BroadLink permanece intacta.

## Operações

Quando anunciadas pela entidade, o App pode usar `media_player.volume_set`, `media_player.volume_mute`, `media_player.select_source`, `media_player.join` e `media_player.unjoin`. A UI não cria fontes fictícias: `source_list`, `volume_level`, `group_members` e `supported_features` vêm do estado atual.

## Homologação atual

Nenhuma entidade LinkPlay foi descoberta na leitura real de 18/10/2026. Assim, o adaptador está implementado e testado com mock, mas não está homologado para os amplificadores físicos. O novo amplificador da Piscina precisa aparecer primeiro como player canônico, evitando duplicação entre LinkPlay, AudioCast e Music Assistant.

## Procedimento quando o player existir

1. Confirmar a área HA e o modelo/firmware.
2. Selecionar o player pela lista da zona, nunca digitar uma entidade fora da área.
3. Confirmar volume baixo e testar volume/mudo sem trocar fonte.
4. Ler as fontes anunciadas e observar a fonte ARC antes de qualquer troca.
5. Testar grupo Piscina líder → Cozinha, ouvir ambas e então separar.
6. Registrar retorno do HA e observação física separadamente.

