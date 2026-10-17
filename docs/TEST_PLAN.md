# Plano de testes e checklist de aceite

Legenda: `PASSOU` = evidência disponível; `NÃO TESTADO` = requer HAOS/equipamento; `BLOQUEADO` = não há acesso autorizado; `FALHOU` = comportamento incorreto.

## Automatizados locais

| ID | Resultado local | Evidência |
|---|---|---|
| A02 | PASSOU (simulado) | filtro usa área efetiva de entidade/dispositivo |
| A03 | PASSOU (simulado) | payload `remote.send_command` por entidade, sem `num_repeats` |
| A05 | PASSOU (simulado) | prefixo `b64:` aplicado no limite do transporte |
| A06 | PASSOU (simulado) | duas chamadas e gap após retorno de 5,0 s |
| A07/A08 | PASSOU (simulado) | motor Cinema→TV e sequência de equipamentos |
| A09 | PASSOU (simulado) | TV física inativa não move telão/projetor |
| A17 | PASSOU (simulado) | profiles/engines separados por área |
| A18/A26 | PARCIAL | proteção de sequência implementada; queda real ainda não observada |

## Aceite físico/HAOS

| ID | Resultado atual | Prova necessária |
|---|---|---|
| A01 | BLOQUEADO | instalação limpa no HAOS, Ingress e restart observados |
| A02 | NÃO TESTADO | captura da descoberta real Cinema/fora da área |
| A03 | NÃO TESTADO | log real do serviço HA |
| A04 | NÃO TESTADO | observação do telão e estado do switch |
| A05 | NÃO TESTADO | log real + observação do projetor |
| A06 | NÃO TESTADO | duas chamadas reais + observação física |
| A07 | NÃO TESTADO | checklist Cinema completo |
| A08 | NÃO TESTADO | checklist TV explícita completo |
| A09 | NÃO TESTADO | evento de TV física com Cinema OFF |
| A10 | NÃO TESTADO | evento de TV física com Cinema ON |
| A11 | NÃO TESTADO | temperatura ~26 °C, vento alto e aleta |
| A12 | NÃO TESTADO | temperatura estável em 22 °C e vento baixo |
| A13 | NÃO TESTADO | luzes e switch explicitamente classificado |
| A14 | NÃO TESTADO | troca/cancelamento de timers em equipamento real |
| A15 | NÃO TESTADO | broker, birth, restart e estados retidos |
| A16 | BLOQUEADO | HomeKit/Alexa do cliente não disponíveis nesta execução |
| A17 | NÃO TESTADO | segundo ambiente real |
| A18 | NÃO TESTADO | queda/restart HA durante OFF |
| A19 | PARCIAL | código/docs/CI preparados; release e screenshots reais dependem de publicação/HAOS |
| A20 | PASSOU (revisão local) | sem backup, `.storage`, token, IP/MAC ou log bruto no repo |
| A21 | PASSOU (simulado) | somente `remote` da área; UI não possui campos IP/MAC |
| A22 | PASSOU (simulado) | validação de formato e restauro implementados |
| A23 | PASSOU (revisão local) | nenhuma dependência/driver BroadLink LAN |
| A24 | PASSOU (revisão local) | formato separado e documentação de Pronto/nomeado |
| A25 | PASSOU (simulado) | gap de 5,0 s medido entre retorno e segunda chamada |
| A26 | PARCIAL | cancelamento seguro implementado; restart real ainda não observado |

## Procedimento de captura

Capturar a tela do Ingress, registros do HA e painel de diagnóstico sem incluir códigos IR, tokens, IPs privados ou dados pessoais. Colocar as imagens reais em `docs/screenshots/` somente após a execução física; não preencher esse diretório com mockups.
