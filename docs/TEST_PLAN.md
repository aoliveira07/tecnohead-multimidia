# Plano de testes e checklist de aceite

> O plano de áudio v1.3, com gates G0–G6 e a matriz B01–B45, está em [AUDIO_TEST_PLAN.md](AUDIO_TEST_PLAN.md). A regressão A01–A26 continua obrigatória; nenhum teste físico de áudio deve ser inferido a partir de um retorno HTTP.

Legenda: `PASSOU` = evidência disponível; `NÃO TESTADO` = requer HAOS/equipamento; `BLOQUEADO` = não há acesso autorizado; `FALHOU` = comportamento incorreto.

## Automatizados locais

| ID | Resultado local | Evidência |
|---|---|---|
| A02 | PASSOU (simulado + HAOS) | filtro usa área efetiva de entidade/dispositivo; Cinema real validado |
| A03 | PARCIAL (HAOS) | remote real validado sem transmissão; payload segue `remote.send_command` por entidade |
| A05 | PASSOU (simulado) | prefixo `b64:` aplicado no limite do transporte |
| A06 | PASSOU (simulado) | duas chamadas e gap após retorno de 4,0 s |
| A07/A08 | PASSOU (simulado) | motor Cinema→TV e sequência de equipamentos |
| A09 | PASSOU (simulado) | TV física inativa não move telão/projetor |
| A17 | PASSOU (simulado) | profiles/engines separados por área |
| A18/A26 | PARCIAL | proteção de sequência implementada; queda real ainda não observada |

## Aceite físico/HAOS

| ID | Resultado atual | Prova necessária |
|---|---|---|
| A01 | PASSOU | App instalado/atualizado no catálogo, Ingress aberto e serviço em funcionamento |
| A02 | PASSOU | descoberta real Cinema e validação de `remote.ir_cinema` na área |
| A03 | PARCIAL | entidade validada sem IR; chamada real ainda aguarda intervenção manual |
| A04 | NÃO TESTADO | observação do telão e estado do switch |
| A05 | NÃO TESTADO | log real + observação do projetor |
| A06 | FALHOU — reteste | na rodada anterior o projetor não respondeu ao desligamento; retestar OFF→4 s→OFF |
| A07 | PARCIAL — reteste | Cinema executou etapas HA, mas luzes e desligamento físico do projetor não atenderam ao aceite |
| A08 | NÃO TESTADO | checklist TV explícita completo |
| A09 | NÃO TESTADO | evento de TV física com Cinema OFF |
| A10 | NÃO TESTADO | evento de TV física com Cinema ON |
| A11 | NÃO TESTADO | temperatura ~26 °C, vento alto e aleta |
| A12 | NÃO TESTADO | temperatura estável em 22 °C e vento baixo |
| A13 | FALHOU — reteste | luzes não apagaram na rodada anterior; correção v1.2.11 instalada, repetir observação após 30 s |
| A14 | NÃO TESTADO | troca/cancelamento de timers em equipamento real |
| A15 | PARCIAL | dispositivo MQTT real com 6 entidades e firmware 1.2.11; birth/restart ainda pendente |
| A16 | PENDENTE | HomeKit Bridge/Alexa disponíveis, mas entidades TecnoHead ainda não expostas para voz |
| A17 | PARCIAL | isolamento real do Cinema; segundo ambiente ainda não configurado |
| A18 | PARCIAL | queda/restart durante OFF ainda não observado |
| A19 | PASSOU | código, docs, CI, release `v1.2.11` e instalação HAOS confirmados |
| A20 | PASSOU | sem backup, `.storage`, token, IP/MAC ou log bruto no repo |
| A21 | PASSOU | somente `remote` da área; UI não possui campos IP/MAC |
| A22 | PASSOU | validação de formato, persistência e restauração disponíveis no App instalado |
| A23 | PASSOU (revisão local) | nenhuma dependência/driver BroadLink LAN |
| A24 | PASSOU (revisão local) | formato separado e documentação de Pronto/nomeado |
| A25 | PASSOU (simulado) | gap de 4,0 s medido entre retorno e segunda chamada |
| A26 | PARCIAL | cancelamento seguro implementado; restart real ainda não observado |

## Procedimento de captura

Capturar a tela do Ingress, registros do HA e painel de diagnóstico sem incluir códigos IR, tokens, IPs privados ou dados pessoais. Colocar as imagens reais em `docs/screenshots/` somente após a execução física; não preencher esse diretório com mockups.
