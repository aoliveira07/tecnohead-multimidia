# Matriz de compatibilidade v1.3

| Componente | Estado observado | Compatibilidade desta release |
|---|---|---|
| Home Assistant API / Supervisor | Disponível no App instalado | Usado para descoberta e serviços |
| MQTT | Integração disponível | Discovery de cenas preservado; estados de áudio preparados |
| HomeKit Bridge | Integração disponível | Não homologado para áudio ou Casa |
| LinkPlay | Não encontrado | Bloqueia G1 e ponte física |
| Cozinha | Player Apple TV/HomePod com volume observado | Cadastro possível como `media_player`, mas não validado como amplificador LinkPlay |
| Piscina | TV universal + entidade Samsung; amplificador ausente | Modelo/firmware/codec pendentes |
| HDMI ARC/CEC | Preservado; nenhuma chamada foi enviada | Nenhuma regressão observada nesta leitura |
| Shairport Sync / NQPTP | Não iniciado | AirPlay 2 bloqueado, sem anúncio falso |
| iPhone / app Casa | Não testado nesta execução | Requer dispositivo Apple real após G2 |

