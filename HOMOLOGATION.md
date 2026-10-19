# Relatório de instalação e homologação — TecnoHead Multimídia

## Estado mais recente — v1.4.15 (18/10/2026)

Última versão confirmada instalada no HAOS: `v1.4.15`. Cozinha e Piscina têm players LinkPlay canônicos e destinos virtuais AirPlay 2. O operador relatou áudio audível e ação do volume do iPhone no amplificador nas duas zonas; aceitou a limitação remanescente de sincronização bidirecional de volume como provisória. A TV da Piscina continua assumindo HDMI ARC ao ligar, pelo próprio hardware; a seleção explícita de música não é bloqueada pelo App.

Capturas privadas do iPhone às 23:03–23:04 mostram `TecnoHead Cozinha` selecionado no seletor AirPlay e adotado no app Casa como acessório modelo `ShairportSync`, associado à Cozinha. O cartão do Casa mostra “Controles não disponíveis” mesmo após a seleção no AirPlay. Isto confirma a adoção, **não** o painel de reprodução HomePod; as capturas não são publicadas por conterem dados de uso pessoal. `TecnoHead Piscina` aparece como destino AirPlay, mas seu pareamento no Casa ainda não foi comprovado. O projeto upstream reconhece suporte incompleto à interface Casa/controle remoto nesta revisão fixada; o HomeKit Bridge do HA não consegue alterar o cartão do acessório ShairportSync. Ver [docs/APPLE_HOME.md](docs/APPLE_HOME.md) e [docs/AUDIO_TEST_PLAN.md](docs/AUDIO_TEST_PLAN.md).

Ainda pendem a seleção Apple das duas zonas ao mesmo tempo, a sincronia física, compartilhar TV Piscina→Cozinha via grupo LinkPlay, a prova prolongada de estabilidade, o pareamento Piscina no Casa e a regressão física completa das cenas v1.2. **Não há homologação integral v1.3.** As seções abaixo são registros históricos das releases anteriores, não o status atual.

## Addendum v1.4.5 — responder mDNS

A v1.4.4 deixou os processos Shairport Sync ativos, porém a consulta mDNS na LAN continuou sem os nomes TecnoHead. A v1.4.5 adiciona a verificação do Avahi do host e fallback para um único D-Bus/Avahi compartilhado dentro do App quando o serviço não estiver disponível. A release precisa ser instalada e o mesmo teste mDNS repetido antes de iniciar a prova no iPhone.

## Addendum v1.4.4 — anúncio AirPlay 2

Durante a validação em 18/10/2026, uma consulta mDNS na LAN não encontrou `TecnoHead Cozinha` nem `TecnoHead Piscina`; encontrou somente os receivers LinkPlay já existentes. A release v1.4.4 corrige o diagnóstico de encerramento precoce, vincula cada endpoint ao endereço LAN resolvido em runtime e explicita `_airplay._tcp`. A etapa de descoberta e áudio físico permanece NÃO TESTADA até novo teste no iPhone.

## Addendum v1.4.3 — correção de conflito de porta

A atualização v1.4.2 iniciou a imagem, mas falhou ao abrir o serviço porque a porta 8099 já estava ocupada no modo `host_network`. A v1.4.3 move o Ingress e o endpoint de stream local para a porta 18199. A correção não modifica entidades, integrações, LinkPlay, ARC ou configurações do cliente.

## Addendum v1.4.2 — correção do empacotamento AirPlay 2

O build foi ajustado para a disponibilidade real do Alpine 3.23: a biblioteca opcional `libsoxr-dev` não é instalada e a configuração usa a interpolação básica embutida do Shairport Sync. Os testes automatizados continuam obrigatórios; a prova no iPhone e o áudio audível permanecem pendentes.

## Addendum v1.4.1 — AirPlay 2 virtual (implementação, sem falsa homologação)

O mesmo App recebeu duas identidades AirPlay 2 virtuais, compiladas com Shairport Sync upstream e NQPTP fixados. A ponte PCM→stream usa `media_player.play_media` pela API do Home Assistant e a Piscina conserva a prioridade HDMI ARC. Esta alteração foi validada por testes automatizados; a publicação e a atualização do HAOS ainda precisam ser comprovadas nesta rodada, e a prova física no iPhone continua pendente até o operador selecionar os destinos e ouvir as caixas.

O fato de `Cozinha Room` e `Piscina Room` aparecerem no app Casa como receivers HomeKit Bridge não equivale a AirPlay 2. O aceite AirPlay exige descoberta no seletor AirPlay e som real em cada zona; o aceite Casa é separado.

## Addendum v1.3.2 — correção do volume LinkPlay e teste pelo App (18/10/2026)

A captura enviada pelo operador mostrou `401 Unauthorized` ao aplicar volume no painel. A causa foi isolada no caminho de chamada de serviço: leituras de estado funcionavam, mas o POST REST de serviço não era aceito pelo endpoint usado pelo App. A v1.3.2 passou a chamar `media_player` pela sessão WebSocket autenticada do Home Assistant, sem fallback REST automático (evitando duplicar qualquer comando físico).

Publicação e instalação confirmadas:

- commit: `21a6aea44920d5cea2a9c9f1869f7a62ac0c673f`
- tag/release: `v1.3.2`
- CI e imagem de App: concluídos com sucesso
- HAOS: atualização concluída; Ingress exibindo `v1.3.2` e `HAOS online`

Teste real executado com cautela:

1. No App, zona **Cozinha**, entidade `media_player.cozinha_room`, foi aplicado volume limitado de 30%.
2. O App registrou `audio_volume_set`, exibiu “Volume enviado ao Home Assistant” e releu a zona em 30%.
3. Na ferramenta nativa **Ferramentas → Template** do Home Assistant, a leitura independente retornou `volume_level: 0.3` para `media_player.cozinha_room`, com estado `idle`.
4. Piscina não foi acionada; fonte HDMI/ARC, reprodução, agrupamento, troca de fonte, IR e cenas não foram tocados nesta prova.

Resultado: **PASSOU para chamada autenticada e retorno de estado do volume da Cozinha; resposta acústica física ainda requer escuta do operador**. O limite de segurança do App permanece em 30%.

## Registro inicial v1.3.0 — áudio multiroom (18/10/2026, superseded)

A implementação v1.3 foi adicionada ao mesmo App e passou nos testes automatizados. O painel de áudio, migração de configuração, controles `media_player`, filtro estrito por área e estados MQTT foram instalados no HAOS em 18/10/2026. Este registro descreve a leitura inicial, anterior à inclusão dos dois equipamentos no LinkPlay; a descoberta atual está no addendum v1.3.1 abaixo. A versão ainda não pode ser chamada de “fisicamente homologada”: nenhum comando físico de áudio ou AirPlay foi enviado.

O resultado fiel é: **código implementado e testado localmente; AirPlay 2/LinkPlay bloqueados por alvo físico ausente; v1.2 física ainda pendente de intervenção manual**. A evidência sanitizada está em [docs/AUDIO_DISCOVERY_REPORT.md](docs/AUDIO_DISCOVERY_REPORT.md) e a matriz B01–B45 em [docs/AUDIO_TEST_PLAN.md](docs/AUDIO_TEST_PLAN.md).

O próximo dado impeditivo é o modelo atual do amplificador da Piscina ou a entidade `media_player` que o Home Assistant criou para ele. Depois disso, será possível testar G1 antes de decidir as permissões de rede necessárias para G2. Não foi alterado HDMI ARC/CEC.

## Addendum v1.3.1 — correção do intervalo e atualização live (18/10/2026)

A release `v1.3.1` restaura no código o default exigido pelo handoff: OFF uma vez, espera monotônica de 5,0 s após o retorno da chamada e OFF uma segunda vez. O perfil Cinema persistido no HAOS foi alinhado para `ON 1`, `OFF 2`, `5,0 s` sem transmitir IR.

## Addendum v1.3.1 — descoberta LinkPlay e preparação HomeKit (18/10/2026)

Após os dois equipamentos serem adicionados ao LinkPlay, a descoberta somente leitura confirmou:

| Zona | Área HA efetiva | Entidade canônica | Observação observada |
|---|---|---|---|
| Cozinha | `Cozinha` | `media_player.cozinha_room` | AudioCast M5; fonte `Wifi`; estado `idle`; volume reportado em 71% |
| Piscina | `Externo Piscina` | `media_player.piscina_room` | modelo reportado como `Generic`; fontes `Wifi`, `Line In`, `Bluetooth`, `Optical`, `HDMI`; fonte atual `HDMI`; volume reportado em 100% |

O App foi configurado e salvo com essas duas entidades, mantendo o filtro estrito por área. A zona Piscina usa a área real `Externo Piscina` — o rótulo operacional continua “Piscina” — e a prioridade HDMI ARC permanece ativa. O limite de segurança do App ficou em 30%; nenhum comando de volume, fonte, reprodução ou agrupamento foi enviado nesta rodada. O volume reportado de 100% na Piscina exige redução manual e conferência auditiva antes de qualquer teste físico.

O HomeKit Bridge passou a apresentar os receivers `Cozinha Room` e `Piscina Room` como acessórios, além das entradas já existentes. Isso prepara a adoção no app Casa sem criar um controle LAN paralelo. O pareamento/adopção no iPhone e os comandos efetivos ainda não foram testados.

AirPlay 2 virtual continua **NÃO HOMOLOGADO**: Shairport Sync/NQPTP não foram iniciados e nenhum áudio foi encaminhado às caixas. A presença dos receivers no HomeKit Bridge não é prova de AirPlay 2.

## Status real em 18/10/2026 — atualizado pela v1.3.2

**Instalado e configurado no HAOS; pronto para testes físicos manuais. Ainda não homologado fisicamente.**

O App foi atualizado pelo catálogo de Apps a partir do repositório autorizado, de 1.3.1 para 1.3.2, e confirmado como “Em funcionamento”. O Ingress abriu com o indicador `v1.3.2` e “HAOS online”; a descoberta real do Home Assistant respondeu, o painel de áudio apareceu e as duas zonas LinkPlay permaneceram cadastradas com validação de área. O perfil Cinema permaneceu persistido. O MQTT Discovery reconectou após a atualização. O intervalo OFF do perfil Cinema está em 5,0 s e foi salvo sem iniciar uma cena ou teste IR.

Durante esta revalidação do Denon, não foi acionado botão de cena nem teste IR; a etapa executada foi cadastral/operacional.

## Entidades mapeadas no ambiente Cinema

| Função | Entidade | Situação observada |
|---|---|---|
| TV física | `media_player.tv_cinema` | selecionada; estado reportado pelo HA |
| Receiver | `media_player.denon_cinema` | selecionado; dispositivo Denon Cinema ligado, na área Cinema, com conexão restabelecida |
| Telão | `switch.tela` | selecionado; operação física pendente |
| Apple TV opcional | `media_player.cinema_cinema` | selecionada |
| Ar-condicionado | `climate.ar_cinema` | selecionado; 22 °C, alto `very high`, baixo `low` |
| Emissor IR | `remote.ir_cinema` | validado na área Cinema; sem IP/MAC/driver no App |
| Luzes automáticas | `light.luz_cinema`, `light.luz_pipoca`, `light.sanca_cinema` | descobertas dinamicamente |

O sensor `sensor.ir_cinema_temperatura` não foi vinculado porque a leitura real observada não era válida; o perfil usa a temperatura anunciada pelo próprio climate. A posição fixa superior da aleta permanece sem valor configurado porque a integração anuncia posições numéricas e ainda falta confirmação física do valor correto.

### Revalidação do Denon — 18/10/2026

A integração **Denon AVR Network Receivers** voltou a apresentar um dispositivo. O dispositivo **Denon Cinema** está associado à área Cinema e reporta estado ligado no Home Assistant. A entidade `media_player.denon_cinema` foi confirmada no editor do TecnoHead. A lista real de fontes do receiver contém `Apple TV` e `TV Audio`; o perfil foi salvo com `Apple TV` para Cinema, `TV Audio` para TV e volumes conservadores de 0,25 e 0,20.

Essa validação confirma a conexão, a associação de área, a entidade e os rótulos de fonte. Ainda não confirma a troca física de fonte, volume ou resposta acústica; essas ações permanecem para o teste manual acompanhado.

### Observação da rodada física anterior e correção — 18/10/2026

O operador acionou Cinema e observou que as luzes não foram apagadas após o atraso configurado e que o projetor não respondeu ao desligamento. O diagnóstico registrou a chamada HA de ON e a execução das etapas do receiver; a confirmação da API não foi tratada como confirmação física. A causa do timer de luzes foi identificada: a cena ficou em fase degradada por não confirmar a aleta e o modo lógico permaneceu OFF, bloqueando o timer. A v1.2.11 corrige esse estado parcial e mantém as luzes agendadas. O intervalo entre as duas chamadas OFF foi alterado de 5,0 s para 4,0 s; o comportamento físico precisa ser retestado.

## Checklist de aceite

Legenda: `PASSOU` = evidência observada; `PARCIAL` = parte validada, parte pendente; `NÃO TESTADO` = requer intervenção física; `PENDENTE` = integração externa ou equipamento indisponível.

| ID | Resultado atual | Evidência |
|---|---|---|
| A01 | PASSOU | App instalado pelo catálogo, Ingress aberto, atualização 1.2.10 concluída e serviço em funcionamento |
| A02 | PASSOU | descoberta real por área; Cinema ofereceu somente entidades efetivamente associadas à área, incluindo `remote.ir_cinema` |
| A03 | PARCIAL | entidade remote validada pelo HA sem nova transmissão nesta etapa; chamada física ainda não executada |
| A04 | NÃO TESTADO | requer observação do telão |
| A05 | NÃO TESTADO | requer envio ON autorizado e observação do projetor |
| A06 | FALHOU — reteste | na rodada anterior o projetor não respondeu ao desligamento; v1.2.11 usa duas chamadas independentes com 4 s, aguardando nova observação |
| A07 | PARCIAL — reteste | Cinema acionado e etapas HA registradas, mas luzes e desligamento físico do projetor não atenderam ao aceite anterior |
| A08 | NÃO TESTADO | cena TV completa aguarda teste manual; Denon agora conectado e fonte configurada |
| A09 | NÃO TESTADO | evento de TV física aguarda teste manual |
| A10 | NÃO TESTADO | proteção durante Cinema aguarda teste manual |
| A11 | NÃO TESTADO | ar e aleta aguardam observação em temperatura real |
| A12 | NÃO TESTADO | histerese e vento baixo aguardam observação |
| A13 | FALHOU — reteste | luzes não apagaram na rodada anterior; correção do estado degradado instalada em v1.2.11, aguardando nova observação após 30 s |
| A14 | NÃO TESTADO | cancelamento de timer aguarda teste de cena |
| A15 | PARCIAL | dispositivo MQTT real com 3 switches + 3 sensores, estado `idle/off` e firmware 1.2.11; birth/restart do broker ainda não observado |
| A16 | PENDENTE | HomeKit Bridge e Alexa estão disponíveis, mas as entidades TecnoHead ainda não foram incluídas/expostas para teste de voz |
| A17 | PARCIAL | isolamento por área implementado e Cinema configurado; segundo ambiente ainda não comissionado |
| A18 | PARCIAL | proteção contra repetição cega coberta por testes; queda real durante sequência ainda não observada |
| A19 | PASSOU | repositório, commit `d415d33`, tag/release `v1.2.11`, CI e imagem multiarch publicados |
| A20 | PASSOU | nenhuma alteração em outros Apps, banco, automações antigas ou arquivos `.storage`; nenhum segredo no repositório |
| A21 | PASSOU | campo aceita somente `remote` da área e sugere `remote.ir_cinema`; nenhum campo IP/MAC |
| A22 | PASSOU | presets e parâmetros persistentes, editor avançado e restauração disponíveis; valores sensíveis não aparecem nos diagnósticos |
| A23 | PASSOU | BroadLink permanece integrado no HA; o App não possui driver LAN/IP |
| A24 | PASSOU | formatos BroadLink Base64, Pronto Hex e comando nomeado separados; troca de entidade não presume compatibilidade de payload |
| A25 | PASSOU (simulado) | testes automatizados medem 5,0 s após o retorno da primeira chamada; medição física de portadora não é alegada |
| A26 | PARCIAL | cancelamento seguro coberto em código/testes; reinício real durante OFF ainda não observado |

## Evidências técnicas

- `python -m pytest -q`: **12 passed**.
- `python -m ruff check app tests`: passou.
- `python -m compileall -q app`: passou.
- CI GitHub: sucesso no commit `79e7295`.
- Release multiarch: `v1.2.11`, publicada após build `amd64`/`aarch64` bem-sucedido.
- Validação no painel: `remote.ir_cinema` associado a Cinema; nesta revalidação do Denon não foi acionado botão de cena nem teste IR.
- Denon real: integração com um dispositivo ativo, dispositivo na área Cinema, `media_player.denon_cinema` selecionado e fontes `Apple TV`/`TV Audio` gravadas no perfil.
- Configuração real: perfil Cinema salvo com ON 1, OFF 2 e intervalo OFF de 5,0 s; atraso de luzes permanece 30 s.
- MQTT real: dispositivo TecnoHead na área Cinema, seis entidades, estado inicial Desligado/idle/Pronto.

## Próximo passo manual

O bloqueio de conexão do receiver foi removido e as zonas de áudio estão cadastradas. Antes de testar áudio, reduzir manualmente o amplificador Piscina de 100% para um nível baixo e seguro, mantendo a TV/ARC como está. Depois, o operador pode executar o checklist físico em [docs/TEST_PLAN.md](docs/TEST_PLAN.md), começando pelo teste ON autorizado e observação direta do projetor; em seguida testar o LinkPlay zona por zona. A adoção no HomeKit exige ação manual no iPhone. A troca física de fonte/volume, o compartilhamento TV→Cozinha, AirPlay 2 e a homologação completa continuam pendentes até a observação manual.
