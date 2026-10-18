# Plano de testes de áudio v1.3

Cada teste físico precisa registrar data, modelo/firmware, entidade HA, versão do App, passos, resultado, evidência real e commit corretivo. Nesta execução nenhum comando físico de áudio foi enviado.

## Gates

- G0: **PARCIAL** — áreas e players atuais lidos; novo amplificador Piscina não identificado.
- G1: **PARCIAL** — entidades canônicas cadastradas; volume da Cozinha aceito e confirmado pelo HA, grupo e teste acústico ainda pendentes.
- G2: **BLOQUEADO** — sem destino físico LinkPlay confirmado, a ponte PCM não pode ser validada.
- G3: **BLOQUEADO** — depende de G2 e do amplificador Piscina com ARC.
- G4: **BLOQUEADO** — depende de duas saídas físicas e iPhone real.
- G5: **NÃO TESTADO** — depende da ponte e do app Casa.
- G6: **PARCIAL** — regressão automatizada do código v1.2 passou; homologação física permanece manual.

## Matriz B01–B45

| ID | Resultado atual | Evidência / bloqueio |
|---|---|---|
| B01 | PASSOU | Descoberta por área implementada e coberta por teste; leitura real separou Cozinha/Piscina |
| B02 | PARCIAL | O novo equipamento aparece como `media_player.piscina_room` e não foi confundido com o M5 antigo; o HA ainda reporta modelo `Generic`, sem firmware detalhado |
| B03 | PARCIAL | Entidade canônica foi escolhida para cada zona; reconciliação completa com eventuais espelhos Music Assistant ainda não foi executada |
| B04 | PASSOU (controle HA) | v1.3.2: volume 30% enviado pelo App, `audio_volume_set` registrado e `volume_level: 0.3` confirmado no Template nativo; escuta acústica ainda pendente |
| B05 | NÃO TESTADO | Player `media_player.piscina_room` existe, mas nenhum comando de volume foi enviado para preservar o HDMI ARC durante esta correção |
| B06 | NÃO TESTADO | Mudo e recuperação aguardam alvo real |
| B07 | BLOQUEADO | Grupo físico indisponível |
| B08 | PARCIAL | Fontes observadas apenas nos players atuais; fontes do amplificador pendentes |
| B09 | NÃO TESTADO | ARC não foi acionado |
| B10 | NÃO TESTADO | CEC não foi acionado |
| B11 | NÃO TESTADO | Nenhuma troca física de fonte |
| B12 | BLOQUEADO | Sem player LinkPlay Piscina/Cozinha |
| B13 | BLOQUEADO | Sem grupo físico |
| B14 | BLOQUEADO | Spotify Connect do amplificador não identificado |
| B15 | NÃO TESTADO | AudioCast externo não usado |
| B16 | BLOQUEADO | Shairport Sync AirPlay 2 não compilado |
| B17 | NÃO TESTADO | NQPTP/mDNS não iniciado |
| B18 | NÃO TESTADO | iPhone não utilizado |
| B19 | BLOQUEADO | Ponte física sem destino |
| B20 | BLOQUEADO | Identidade Piscina não criada |
| B21 | BLOQUEADO | Áudio Piscina sem alvo |
| B22 | BLOQUEADO | Sem duas saídas |
| B23 | BLOQUEADO | Sem duas saídas |
| B24 | NÃO TESTADO | Sem reprodução simultânea |
| B25 | NÃO TESTADO | Volume Apple não testado |
| B26 | BLOQUEADO | Piscina sem endpoint |
| B27 | BLOQUEADO | Política implementada, cenário físico não executado |
| B28 | NÃO TESTADO | Troca explícita ARC→música não executada |
| B29 | NÃO TESTADO | TV/stream não executados |
| B30 | NÃO TESTADO | Sem grupo e AirPlay simultâneos |
| B31 | NÃO TESTADO | Casa não emparelhado |
| B32 | NÃO TESTADO | Casa não emparelhado |
| B33 | NÃO TESTADO | Bridge de áudio não homologado |
| B34 | PARCIAL | Código MQTT Discovery de áudio e testes de contrato preparados; broker físico não retestado nesta rodada |
| B35 | NÃO TESTADO | Sem stream físico |
| B36 | NÃO TESTADO | Sem player LinkPlay |
| B37 | NÃO TESTADO | Reinício com pareamento ainda não aplicável |
| B38 | NÃO TESTADO | Ponte de stream não iniciada |
| B39 | NÃO TESTADO | Não houve reprodução de 30 minutos |
| B40 | PASSOU (software/instalação) | Migração coberta por teste; atualização HAOS para v1.3.2 preservou as zonas e o perfil existente |
| B41 | PARCIAL | Regressão automatizada; teste IR físico permanece manual |
| B42 | PARCIAL | Regressão automatizada; clima/luzes físicos permanecem manuais |
| B43 | PARCIAL | v1.3.2 publicada, CI/imagem concluídos e atualização HAOS instalada; screenshots/documentação física completa ainda pendentes |
| B44 | PARCIAL | Sem segredos no conjunto alterado; SBOM da ponte só será criado quando ela for empacotada |
| B45 | PASSOU como bloqueio | Limitação comprovada no HAOS atual; LinkPlay não foi mascarado como AirPlay homologado |

