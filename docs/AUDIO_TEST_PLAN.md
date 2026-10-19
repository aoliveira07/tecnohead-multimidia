# Plano de testes de áudio v1.3

Cada teste físico precisa registrar data, modelo/firmware, entidade HA, versão do App, passos, resultado, evidência real e commit corretivo. Esta matriz substitui o retrato inicial v1.3.2; relatos físicos e capturas privadas recebidos em 18–19/10/2026, com App v1.4.15 durante o teste. A correção v1.4.16 requer reteste após instalação. `PASSOU (relato)` identifica observação do operador, não medição independente. As capturas do iPhone não entram no repositório por conterem dados de uso pessoal. Modelo/firmware detalhado da Piscina continuam não informados pelo HA.

## Gates

- G0: **PARCIAL** — áreas e players atuais mapeados; modelo/firmware detalhado da Piscina permanece `Generic` no HA.
- G1: **PARCIAL** — volume físico das duas zonas foi confirmado pelo operador; compartilhamento TV Piscina→Cozinha e retorno do grupo não testados.
- G2: **PASSOU (relato)** — Cozinha descoberta no iPhone e áudio audível relatado pelo operador; estabilidade prolongada pendente.
- G3: **PARCIAL** — Piscina anunciada e volume AirPlay com efeito físico relatado; retorno ARC durante stream ainda requer teste controlado.
- G4: **PARCIAL** — Cozinha+Piscina reproduziram juntas segundo o operador; volume oscilou no iPhone e não há medição de sincronia. Correção v1.4.16 aguarda reteste.
- G5: **PARCIAL** — `TecnoHead Cozinha` adotado no app Casa como ShairportSync; cartão sem controles; Piscina ainda não comprovada no Casa.
- G6: **PARCIAL** — release v1.4.15 instalada e testes automatizados anteriores; regressão física v1.2 e checklist completo pendentes.

## Matriz B01–B45

| ID | Resultado atual | Evidência / bloqueio |
|---|---|---|
| B01 | PASSOU | Descoberta por área implementada e coberta por teste; leitura real separou Cozinha/Piscina |
| B02 | PARCIAL | O novo equipamento aparece como `media_player.piscina_room` e não foi confundido com o M5 antigo; o HA ainda reporta modelo `Generic`, sem firmware detalhado |
| B03 | PARCIAL | Entidade canônica foi escolhida para cada zona; reconciliação completa com eventuais espelhos Music Assistant ainda não foi executada |
| B04 | PASSOU (relato) | Volume da Cozinha responde no App e no player físico; o operador também testou o slider do iPhone |
| B05 | PASSOU (relato) | Volume da Piscina responde no App e no player físico; o operador também testou o slider do iPhone |
| B06 | NÃO TESTADO | Mudo e recuperação aguardam alvo real |
| B07 | NÃO TESTADO | Grupo físico/volume relativo ainda requer teste acompanhado |
| B08 | PARCIAL | Fontes observadas apenas nos players atuais; fontes do amplificador pendentes |
| B09 | PASSOU (relato) | Operador confirmou que a TV, ao ligar, faz o amplificador assumir ARC automaticamente; o App não envia troca concorrente |
| B10 | NÃO TESTADO | CEC não foi acionado |
| B11 | NÃO TESTADO | Nenhuma troca física de fonte |
| B12 | NÃO TESTADO | TV Piscina→Cozinha por grupo LinkPlay ainda não foi executado |
| B13 | NÃO TESTADO | Desagrupamento após TV compartilhada ainda não foi executado |
| B14 | NÃO TESTADO | Spotify Connect individual funcionou; compartilhamento Spotify LinkPlay ainda não foi comprovado |
| B15 | PARCIAL | Alterar volume no AudioCast refletiu no slider AirPlay em teste da Cozinha; fonte/grupo externos não retestados |
| B16 | PARCIAL | Binário Shairport Sync fixado foi compilado com AirPlay 2 e destinos funcionam no iPhone; não há captura independente do handshake da sessão |
| B17 | PARCIAL | NQPTP/mDNS anunciaram duas identidades simultâneas; colisão/robustez prolongada ainda não medida |
| B18 | PASSOU | Capturas privadas mostram `TecnoHead Cozinha` no seletor do iPhone |
| B19 | PASSOU (relato) | Operador confirmou som audível na Cozinha usando o destino virtual |
| B20 | PASSOU | Capturas privadas mostram `TecnoHead Piscina` no seletor do iPhone |
| B21 | PARCIAL (relato) | Operador confirmou efeito audível do volume na Piscina; repetir prova com ARC livre e início/parada documentados |
| B22 | NÃO TESTADO | Dois streams independentes ainda não foram executados |
| B23 | PARCIAL (relato) | As duas saídas tocaram juntas; volume oscilou ao ajustar pelo iPhone na v1.4.15; retestar v1.4.16 |
| B24 | NÃO TESTADO | Houve reprodução simultânea, mas a diferença entre as saídas e eventual eco não foram medidos |
| B25 | FALHOU — reteste | Slider iPhone altera volume físico da Cozinha, mas durante seleção dupla houve oscilação; correção v1.4.16 ainda sem prova física |
| B26 | FALHOU — reteste | Slider iPhone altera volume físico da Piscina, mas durante seleção dupla houve oscilação; correção v1.4.16 ainda sem prova física |
| B27 | PARCIAL | TV assume ARC ao ligar; conflito com stream AirPlay ativo ainda não foi observado de ponta a ponta |
| B28 | NÃO TESTADO | Troca explícita ARC→música não executada |
| B29 | NÃO TESTADO | TV/stream não executados |
| B30 | NÃO TESTADO | Sem grupo e AirPlay simultâneos |
| B31 | PARCIAL | `TecnoHead Cozinha` foi adotado no Casa como ShairportSync, cômodo Cozinha; cartão mostra “Controles não disponíveis” (capturas privadas 23:04) |
| B32 | NÃO TESTADO | `TecnoHead Piscina` aparece no AirPlay; adoção no app Casa ainda não foi comprovada |
| B33 | PARCIAL | `Cozinha Room`/`Piscina Room` adotados como receivers via HomeKit Bridge; não criam cartão HomePod nem substituem o acessório ShairportSync |
| B34 | PARCIAL | Código MQTT Discovery de áudio e testes de contrato preparados; broker físico não retestado nesta rodada |
| B35 | NÃO TESTADO | Pausa/parada/desconexão sem áudio fantasma ainda requer teste específico |
| B36 | NÃO TESTADO | Falha de rede/player ainda requer teste controlado |
| B37 | NÃO TESTADO | Persistência de pareamento após reinício ainda requer teste controlado |
| B38 | PARCIAL | Rota local de stream com token implementada; auditoria da exposição LAN/WAN ainda pendente |
| B39 | NÃO TESTADO | Não houve reprodução de 30 minutos |
| B40 | PASSOU (software/instalação) | Migração coberta por teste; atualizações até v1.4.15 preservaram zonas e perfil existente |
| B41 | PARCIAL | Regressão automatizada; teste IR físico permanece manual |
| B42 | PARCIAL | Regressão automatizada; clima/luzes físicos permanecem manuais |
| B43 | PARCIAL | v1.4.15 publicada e instalada antes do teste; v1.4.16 depende de CI, publicação, atualização HAOS e reteste físico |
| B44 | PARCIAL | Sem dados privados no repositório; auditoria completa da ponte/licenças ainda pendente |
| B45 | NÃO SE APLICA | A ponte produziu áudio físico; o bloqueio observado agora é o cartão de controle do Casa, registrado em B31 |

