# Relatório de instalação e homologação — TecnoHead Multimídia v1.2.10

## Status real em 17/10/2026

**Instalado e configurado no HAOS; pronto para testes físicos manuais. Ainda não homologado fisicamente.**

O App foi instalado pelo catálogo de Apps a partir do repositório autorizado, atualizado de 1.2.8 para 1.2.10 e confirmado como “Em funcionamento”. O Ingress abriu, a descoberta real do Home Assistant respondeu, o perfil Cinema permaneceu persistido e o MQTT Discovery reconectou após a atualização.

Não foram acionados projetor, telão, TV, receiver, ar, aleta ou luzes durante esta sessão. A validação executada no emissor foi somente cadastral/operacional e não transmitiu IR.

## Entidades mapeadas no ambiente Cinema

| Função | Entidade | Situação observada |
|---|---|---|
| TV física | `media_player.tv_cinema` | selecionada; estado reportado pelo HA |
| Receiver | `media_player.denon_cinema` | selecionado, porém indisponível na integração Denon no momento |
| Telão | `switch.tela` | selecionado; operação física pendente |
| Apple TV opcional | `media_player.cinema_cinema` | selecionada |
| Ar-condicionado | `climate.ar_cinema` | selecionado; 22 °C, alto `very high`, baixo `low` |
| Emissor IR | `remote.ir_cinema` | validado na área Cinema; sem IP/MAC/driver no App |
| Luzes automáticas | `light.luz_cinema`, `light.luz_pipoca`, `light.sanca_cinema` | descobertas dinamicamente |

O sensor `sensor.ir_cinema_temperatura` não foi vinculado porque a leitura real observada não era válida; o perfil usa a temperatura anunciada pelo próprio climate. A posição fixa superior da aleta permanece sem valor configurado porque a integração anuncia posições numéricas e ainda falta confirmação física do valor correto.

## Checklist de aceite

Legenda: `PASSOU` = evidência observada; `PARCIAL` = parte validada, parte pendente; `NÃO TESTADO` = requer intervenção física; `PENDENTE` = integração externa ou equipamento indisponível.

| ID | Resultado atual | Evidência |
|---|---|---|
| A01 | PASSOU | App instalado pelo catálogo, Ingress aberto, atualização 1.2.10 concluída e serviço em funcionamento |
| A02 | PASSOU | descoberta real por área; Cinema ofereceu somente entidades efetivamente associadas à área, incluindo `remote.ir_cinema` |
| A03 | PARCIAL | entidade remote validada pelo HA sem transmissão; chamada física ainda não executada |
| A04 | NÃO TESTADO | requer observação do telão |
| A05 | NÃO TESTADO | requer envio ON autorizado e observação do projetor |
| A06 | NÃO TESTADO | requer duas chamadas OFF reais, intervalo de 5 s e observação física |
| A07 | NÃO TESTADO | cena Cinema completa aguarda teste manual |
| A08 | NÃO TESTADO | cena TV completa aguarda teste manual |
| A09 | NÃO TESTADO | evento de TV física aguarda teste manual |
| A10 | NÃO TESTADO | proteção durante Cinema aguarda teste manual |
| A11 | NÃO TESTADO | ar e aleta aguardam observação em temperatura real |
| A12 | NÃO TESTADO | histerese e vento baixo aguardam observação |
| A13 | NÃO TESTADO | temporizador de 30 s aguarda teste com luzes reais |
| A14 | NÃO TESTADO | cancelamento de timer aguarda teste de cena |
| A15 | PARCIAL | dispositivo MQTT real com 3 switches + 3 sensores, estado `idle/off` e firmware 1.2.10; birth/restart do broker ainda não observado |
| A16 | PENDENTE | HomeKit Bridge e Alexa estão disponíveis, mas as entidades TecnoHead ainda não foram incluídas/expostas para teste de voz |
| A17 | PARCIAL | isolamento por área implementado e Cinema configurado; segundo ambiente ainda não comissionado |
| A18 | PARCIAL | proteção contra repetição cega coberta por testes; queda real durante sequência ainda não observada |
| A19 | PASSOU | repositório, commit, tag/release, CI e imagem multiarch publicados |
| A20 | PASSOU | nenhuma alteração em outros Apps, banco, automações antigas ou arquivos `.storage`; nenhum segredo no repositório |
| A21 | PASSOU | campo aceita somente `remote` da área e sugere `remote.ir_cinema`; nenhum campo IP/MAC |
| A22 | PASSOU | presets e parâmetros persistentes, editor avançado e restauração disponíveis; valores sensíveis não aparecem nos diagnósticos |
| A23 | PASSOU | BroadLink permanece integrado no HA; o App não possui driver LAN/IP |
| A24 | PASSOU | formatos BroadLink Base64, Pronto Hex e comando nomeado separados; troca de entidade não presume compatibilidade de payload |
| A25 | PASSOU (simulado) | testes automatizados medem 5,0 s após o retorno da primeira chamada; medição física de portadora não é alegada |
| A26 | PARCIAL | cancelamento seguro coberto em código/testes; reinício real durante OFF ainda não observado |

## Evidências técnicas

- `python -m pytest -q`: **11 passed**.
- `python -m ruff check app tests`: passou.
- `python -m compileall -q app`: passou.
- CI GitHub: sucesso no commit `79e7295`.
- Release multiarch: `v1.2.10`, publicada após build `amd64`/`aarch64` bem-sucedido.
- Validação no painel: `remote.ir_cinema` associado a Cinema; nenhum IR transmitido.
- MQTT real: dispositivo TecnoHead na área Cinema, seis entidades, estado inicial Desligado/idle/Pronto.

## Próximo passo manual

Com receiver indisponível, o painel registra essa degradação e continua etapas independentes seguras; a integração Denon precisa estar disponível para validar fonte e volume. O operador deve executar o checklist físico em [docs/TEST_PLAN.md](docs/TEST_PLAN.md), começando pelo teste ON autorizado e observação direta do projetor. O App não deve ser classificado como homologado antes dessa observação.
