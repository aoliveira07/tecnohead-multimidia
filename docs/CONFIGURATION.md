# Configuração por ambiente

Cada perfil é salvo por `area_id` no arquivo privado `/data/config.json`. O nome da área é sempre resolvido novamente pelo registro atual do Home Assistant.

## Seletores

- TV: candidatos `media_player` da área.
- Receiver: `media_player` que anuncia fontes ou volume.
- Telão: `switch` ou `cover` da área. O Cinema atual usa `switch.tela`.
- Clima: `climate` da área.
- Luzes: todos os domínios `light` da área. Um `switch` somente entra quando o administrador o classifica explicitamente como iluminação.
- Remote: somente domínio `remote` da área. Não há campo de IP/MAC.

O App considera área explícita da entidade; se ausente, usa a área do dispositivo. Uma entidade fora da área nunca é oferecida nem aceita no salvamento.

## Defaults do Cinema atual

| Parâmetro | Padrão |
|---|---:|
| setpoint | 22 °C |
| luzes | 30 s após o pedido |
| projetor ON | 1 chamada HA |
| projetor OFF | 2 chamadas HA |
| intervalo OFF | 5,0 s após o retorno da primeira |
| modo padrão do mestre | TV |
| volume Cinema | 0,25 HA |
| volume TV | 0,20 HA |

Os valores de IR ficam no perfil do App e podem ser restaurados em Configurações avançadas. Restaurar não edita a integração BroadLink nem arquivos `.storage` do HA.

## Clima

O App usa somente `hvac_modes`, `fan_modes`, `swing_modes` e atributos anunciados. Acima do setpoint, escolhe o modo de ventilação alto configurado/detectado; no setpoint, escolhe o baixo. A histerese retorna ao alto somente acima do limite configurado por um período mínimo. Sem temperatura ou capacidade válida, a etapa é reportada como degradação.
