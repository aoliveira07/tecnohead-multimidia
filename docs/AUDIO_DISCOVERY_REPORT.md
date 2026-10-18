# Relatório de descoberta de áudio — v1.3

Data da leitura: 18/10/2026. A leitura foi somente de registros, estados e integrações do Home Assistant; nenhuma fonte, volume, grupo, ARC, IR ou cena foi acionada.

## Resultado sanitizado

| Zona | O que o Home Assistant expôs | Conclusão |
|---|---|---|
| Cozinha | Um `media_player` associado à integração Apple TV/HomePod, com leitura de volume disponível | Não é possível tratá-lo como amplificador LinkPlay sem confirmação adicional |
| Piscina / Externo Piscina | Um wrapper de TV universal e uma entidade-base da integração Samsung TV, com fontes de TV/HDMI | O amplificador novo não apareceu como `media_player`; modelo, firmware e integração ainda não estão identificados |
| LinkPlay | Nenhuma integração LinkPlay foi encontrada na configuração atual | G1 físico e a ponte PCM estão bloqueados até existir um player físico canônico |
| MQTT / HomeKit Bridge | Integrações presentes no HAOS | Disponibilidade foi observada; comandos de voz, Casa e áudio físico não foram homologados |

O App mantém o filtro estrito por área. A lista de uma zona só inclui `media_player` cuja área efetiva vem do registro da entidade ou do dispositivo; não há fallback por nome ou por cômodo parecido.

## Bloqueio necessário

Para desbloquear a configuração real da Piscina, é necessário identificar o modelo atual do amplificador e a entidade `media_player` criada pela integração que o controla. O backup antigo não é usado como prova: o iEAST M5 não foi assumido.

O HDMI ARC/CEC não foi modificado. Enquanto a entidade do amplificador não for descoberta, o App não tenta trocar a fonte nem criar um agrupamento.

