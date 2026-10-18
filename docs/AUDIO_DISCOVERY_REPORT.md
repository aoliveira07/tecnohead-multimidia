# Relatório de descoberta de áudio — v1.3

Data da leitura inicial: 18/10/2026. A descoberta cadastral foi somente de registros, estados e integrações do Home Assistant. O teste posterior de volume da Cozinha está registrado no addendum abaixo; nenhuma fonte, grupo, ARC, IR ou cena foi acionada.

## Resultado sanitizado — atualização após cadastro LinkPlay

| Zona | O que o Home Assistant expôs | Conclusão |
|---|---|---|
| Cozinha | `media_player.cozinha_room`, AudioCast M5, área `Cozinha`, fonte `Wifi`, volume 71%, estado `idle` | Player LinkPlay canônico confirmado e cadastrado no App |
| Piscina / Externo Piscina | `media_player.piscina_room`, modelo reportado `Generic`, fontes `Wifi`, `Line In`, `Bluetooth`, `Optical`, `HDMI`, fonte `HDMI`, volume 100% | Player LinkPlay canônico confirmado; prioridade HDMI ARC preservada |
| LinkPlay | Integração LinkPlay com 2 dispositivos e 6 entidades | G1 cadastral concluído; comandos físicos ainda aguardam teste manual |
| MQTT / HomeKit Bridge | MQTT conectado; HomeKit Bridge passou a exibir Cozinha Room e Piscina Room como receivers | Adoção no app Casa e comandos de voz ainda não foram homologados |

O App mantém o filtro estrito por área. A lista de uma zona só inclui `media_player` cuja área efetiva vem do registro da entidade ou do dispositivo; não há fallback por nome ou por cômodo parecido.

## Estado atual e bloqueios restantes

O amplificador atual da Piscina foi identificado pelo HA como `media_player.piscina_room`, mas o modelo detalhado continua reportado como `Generic`; o backup antigo não foi usado como prova e o iEAST M5 não foi assumido. O cadastro por área está concluído.

O HDMI ARC/CEC não foi modificado. O estado observado da Piscina era `HDMI`/`playing` com volume 100%; nenhum comando foi emitido pelo App. O primeiro teste físico deve reduzir o volume manualmente e confirmar o comportamento do ARC antes de qualquer troca de fonte ou agrupamento.

AirPlay 2 virtual ainda está bloqueado para a etapa de implementação/POC: Shairport Sync, NQPTP e a ponte PCM→LinkPlay não foram iniciados. Não há alegação de descoberta AirPlay, áudio audível ou sincronismo.

## Addendum v1.3.2 — volume da Cozinha

Após a correção do `401 Unauthorized`, o App foi atualizado para v1.3.2 e enviou `media_player.volume_set` para `media_player.cozinha_room` pela sessão autenticada do Home Assistant. O App releu 30% e a ferramenta nativa de Template confirmou `volume_level: 0.3`. Essa evidência valida o comando e o estado reportado pelo HA; não substitui a confirmação auditiva nas caixas. A Piscina permaneceu em HDMI/ARC e não foi comandada.

