# MediaRemote no acessório AirPlay 2 do app Casa — investigação inicial

Estado em 19/10/2026: **investigação de código e fontes upstream; não é homologação física**. O handoff específico “v1.3.2 — MediaRemote” e suas definições D01–D24 ainda não estão disponíveis neste checkout. Não atribuir PASSOU/FALHOU a esses IDs até receber o arquivo e executar os passos correspondentes.

## Problema observado e escopo

O iPhone do operador descobriu `TecnoHead Cozinha` e `TecnoHead Piscina` no seletor AirPlay, e a Cozinha foi adicionada ao app Casa como acessório ShairportSync. Na captura privada, o cartão desse **mesmo acessório AirPlay** mostrou “Controles não disponíveis”. O histórico e o estado anterior estão em [APPLE_HOME.md](APPLE_HOME.md). O objetivo aqui é investigar esse cartão; criar um `media_player`, Receiver ou outro acessório HomeKit não satisfaz o requisito e está fora do escopo.

## Linha de base verificável no código

- O Dockerfile fixa Shairport Sync em `cf6998daa1876c5a8f97128a960c8afc0e731841`, revisão sete commits **após** a tag upstream `5.6` (`9118bbce71f287df2dfdfb5bed3911d92a9fdb0f`). O código MediaRemote examinado não difere da tag 5.6 nesses sete commits. Portanto, “atualizar para 5.6” isoladamente não é correção nova para este App.
- O Shairport 5.6 implementa comandos de controle remoto AirPlay 2 pelo D-Bus/MPRIS/MQTT e expõe `NowPlayingInformation`/`CommandInformation`, mas a própria [nota da release 5.6](https://github.com/mikebrady/shairport-sync/releases/tag/5.6) informa que as propriedades de disponibilidade remota ainda podem ficar `false` mesmo quando comandos funcionam. Isto descreve o controle **do emissor**; não promete um cartão de mídia no Casa.
- Nossa configuração gera uma instância por zona, D-Bus de sessão isolado, metadados habilitados e `include_cover_art = "no"`. O leitor atual consome `ssnc/pvol` para volume; não interpreta `ssnc/copl` como faixa/capa. Isto limita o diagnóstico e os metadados da interface TecnoHead, mas não demonstra ser a causa do cartão Casa: Shairport envia os dados a outras superfícies independentemente de o App lê-los.
- No código upstream fixado, `RTSP SETUP` aceita `isRemoteControlOnly`, abre uma porta de eventos e envia o `updateInfo` padrão. O `POST /command` recebido do iPhone é encaminhado para o pipe de metadados como `ssnc/copl`; o código padrão não retransmite `updateMRNowPlayingInfo`/`updateMRSupportedCommands` à conexão Remote Control Only. A rotina `ap2_event_port_post_command` usa buffer fixo de 4096 bytes, insuficiente para uma arte de álbum grande. Qualquer experimento de retransmissão precisaria limitar/alocar o payload corretamente e ter testes de regressão da reprodução.

## O que mostram as discussões técnicas

| Fonte | Resultado relevante | Limite da evidência |
| --- | --- | --- |
| [Shairport #2262](https://github.com/mikebrady/shairport-sync/discussions/2262) | `sendMediaRemoteCommand` pelo canal de eventos da sessão de áudio/PTP pode acionar play/pause/próxima/anterior no iPhone; o caminho Remote Control Only é outro protocolo. O mantenedor confirmou integração desses comandos na linha 5.6. | Prova de comandos receptor→emissor, **não** do cartão no Casa. |
| [Shairport #2182](https://github.com/mikebrady/shairport-sync/issues/2182) | Um experimento retransmitiu Now Playing e capa ao hub por uma compilação **modificada**; o hub reconheceu os eventos, porém o cartão continuou indisponível. O autor inicialmente descreveu isso como comportamento padrão, mas corrigiu explicitamente: o Shairport sem patch só envia `updateInfo`. | Experimento de terceiros, em outro iPhone/hub; não substitui captura na instalação TecnoHead. |
| [Pseudocódigo MediaRemote](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/90aa0cfe59d9682b4265e1354c8b19ec3c7823ab/System/Library/PrivateFrameworks/MediaRemote.framework/MediaRemote/MRAVConcreteOutputDevice.mm) e [mapeamento OwnTone](https://github.com/owntone/owntone-server/blob/master/src/outputs/airplay.c) | `isAddedToHomeKit` consulta `SupportsHangdogRemoteControl`; `isRemoteControllable` depende de outras capacidades. O mapeamento do bit 58 é condicionado à classe reconhecida do dispositivo. Na #2182, anunciar identidade de HomePod mostrou tokens no Mac, mas quebrou descoberta/aceitação no iPhone/hub. | Pseudocódigo reverso, não especificação oficial da Apple; forte indício de bloqueio de classificação, não prova local definitiva. |

## Decisão de segurança desta etapa

Não alterar `model`, features, flags, identidade, pairing, HomeKit Bridge, LinkPlay, HDMI ARC ou a saída PCM→HTTP com base apenas nessa pesquisa. Em particular, **não** anunciar o receptor como HomePod/Apple TV: a #2182 relata que isso pode fazer o iPhone ocultar ou abandonar o acessório. Não aplicar um patch de retransmissão Now Playing à instalação de produção antes de um protocolo de teste/rollback e da prova de que ele poderia atender ao objetivo.

## Próximas evidências indispensáveis

1. Receber o handoff v1.3.2 — MediaRemote para mapear exatamente D01–D24, critérios de passagem e qualquer discussão adicional indicada.
2. Confirmar versão realmente instalada no HAOS e manter backup recuperável da configuração/identidade das duas zonas. O repositório tem release v1.4.16, mas isso **não comprova** instalação no equipamento.
3. Com operador presente, reproduzir faixa no iPhone e registrar separadamente: seletor AirPlay, áudio físico, cartão Casa da Cozinha e Piscina, tipo/modelo exibido e comportamento com/sem reprodução. Não fotografar/publicar títulos, identificadores ou rede do cliente sem sanitização.
4. Se houver autorização e acesso de diagnóstico, observar **apenas eventos sanitizados** de `Remote Control Only`, `ssnc/copl`, D-Bus `NowPlayingInformation` e capacidades anunciadas; não gravar plists, capa, chaves ou endereços em logs públicos.
5. Classificar o resultado: falha de recepção/metadata local; falha do caminho Remote Control Only; ou cartão indisponível **apesar** dos eventos chegarem e serem reconhecidos. Esta última hipótese, junto ao gate de capacidade, requer consulta ao solicitante antes de qualquer alternativa de interface.

Kanban Smart House: nenhuma gravação efetuada nesta etapa. A API oficial/autenticação não foi encontrada no workspace nem entre as integrações conectadas; não usar PostgreSQL diretamente. Registrar ali esta investigação e os resultados D assim que o endpoint autorizado estiver disponível.
