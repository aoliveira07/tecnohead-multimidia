# Release notes

## v1.4.14 — leitura redundante do volume AirPlay

Quando o volume era alterado no slider do iPhone, algumas sessões atualizavam o áudio audível sem entregar ao App um evento utilizável pelo gancho ou pelo `ssnc/pvol`. A v1.4.14 mantém esses caminhos e acrescenta a leitura periódica da propriedade `AirplayVolume` no D-Bus isolado de cada receptor. A primeira leitura de uma sessão apenas estabelece referência; somente alterações posteriores são enviadas por `media_player.volume_set` ao amplificador da mesma zona.

O retorno AudioCast/LinkPlay → AirPlay e a janela anti-eco permanecem ativos. A validação física ainda é obrigatória, zona por zona.

## v1.4.13 — estabilização do retorno de volume AirPlay

Corrige a oscilação observada no teste físico: o amplificador LinkPlay pode devolver o volume arredondado ou repetir o mesmo evento depois de uma chamada. O App agora reconhece esses retornos dentro de uma janela curta e com tolerância de dois pontos, sem iniciar uma nova correção no iPhone. A sincronização continua bidirecional e limitada à sessão AirPlay ativa da zona.

O aceite desta versão deve repetir o teste em Cozinha e Piscina: alterar o slider do iPhone, conferir o AudioCast, alterar o AudioCast e conferir o slider do iPhone; em cada mudança o valor deve estabilizar sem subir e descer sozinho.

## v1.4.12 — sincronização bidirecional do volume AirPlay

A alteração do volume no AudioCast/LinkPlay agora é observada pelo stream de estados do Home Assistant e enviada ao iPhone/iPad da sessão AirPlay ativa pela interface nativa `SetAirplayVolume` do Shairport Sync. O comando usa o mesmo mapeamento linear do slider AirPlay (`0..100%` para `-30..0 dB`, com `-144 dB` para zero).

Cada zona recebeu um barramento D-Bus de sessão privado para manter os comandos de Cozinha e Piscina independentes. O App não envia nada quando a sessão AirPlay terminou, não mexe na arbitragem HDMI ARC sem uma sessão AirPlay ativa e evita eco quando a mudança original veio do iPhone.

O aceite físico desta versão exige: reproduzir em uma zona, alterar o slider do iPhone e confirmar o player; depois alterar o volume pelo AudioCast e confirmar que o slider do iPhone acompanha. Repetir na outra zona.

## v1.4.11 — sincronização física do volume AirPlay

O caminho anterior dependia exclusivamente do leitor de metadados `ssnc/pvol`. A versão 1.4.11 usa também o gancho nativo `run_this_when_volume_is_set` do Shairport Sync: cada valor enviado pelo iPhone é entregue por um socket Unix privado ao App e convertido em `media_player.volume_set` para a entidade LinkPlay da mesma zona. O PCM continua em ganho pleno, sem dupla atenuação.

A homologação permanece física: o valor do AudioCast/LinkPlay deve acompanhar o slider do AirPlay em Cozinha e Piscina, uma zona por vez.

## v1.4.10 — ponte de volume resiliente

Corrige a falha observada em teste real: uma mensagem grande de metadados do Shairport Sync podia exceder o limite padrão do leitor assíncrono e interromper a leitura dos eventos `pvol`. O App agora usa um limite controlado de 4 MiB para o leitor FIFO; o volume recebido do iPhone continua sendo encaminhado à entidade física LinkPlay pela API do Home Assistant.

O teste de aceitação permanece físico: o número exibido pelo AudioCast/LinkPlay deve acompanhar as alterações do slider AirPlay, em uma zona por vez.

## v1.4.9 — volume AirPlay no player LinkPlay

Corrige o caso em que o slider do AirPlay alterava somente o ganho digital do receptor virtual, enquanto o AudioCast/LinkPlay permanecia no mesmo valor. O Shairport Sync agora mantém o PCM em ganho pleno, lê o evento de volume `ssnc/pvol` por uma FIFO exclusiva e encaminha a porcentagem à entidade `media_player` da mesma zona pela API autenticada do Home Assistant.

O limite máximo configurado continua sendo aplicado. Com o teto em 100%, o valor escolhido no iPhone é enviado ao player; o teste físico deve confirmar que o número do AudioCast/LinkPlay acompanha o slider e que não há dupla atenuação audível.

## v1.4.8 — volume AirPlay ativo

Corrige o caso em que Cozinha e Piscina reproduziam áudio, mas não respondiam ao volume do iPhone. O receptor AirPlay 2 agora aplica o volume recebido no PCM antes do encoder/stream LinkPlay. O volume da zona pelo TecnoHead continua sendo enviado separadamente por `media_player.volume_set`.

O primeiro teste deve ser feito em volume baixo, verificando uma zona por vez e depois as duas simultaneamente.

## v1.4.7 — AirPlay explícito e HDMI ARC observado

A Piscina não bloqueia mais uma seleção AirPlay/Spotify quando a última fonte observada é HDMI/ARC. O App encaminha a solicitação ao `media_player` do Home Assistant e deixa o amplificador fazer sua própria arbitragem de fonte. Ao ligar a TV, o comportamento CEC/ARC permanece intocado; ao parar uma sessão que já voltou a ARC, o App evita enviar `media_stop`.

Esta versão não altera o controle BroadLink/IR, o HomeKit Bridge, o LinkPlay físico ou as cenas Cinema/TV. O teste físico da Piscina deve ser repetido em volume baixo e com a seleção AirPlay feita pelo operador.

## v1.4.6

Corrige a política do D-Bus privado usado pelo responder Avahi interno. A versão anterior iniciava o processo, mas rejeitava respostas de método e sinais necessários para a publicação dos serviços AirPlay 2. A correção permanece isolada ao barramento interno do App e não altera o serviço mDNS global do HAOS.

Após a atualização, a prova ainda exige que `TecnoHead Cozinha` e `TecnoHead Piscina` apareçam no iPhone e que o áudio seja ouvido fisicamente nas respectivas zonas.

## v1.4.5

Corrige o bloqueio observado na rede real: os processos Shairport Sync estavam ativos, mas o host não publicava os serviços TecnoHead no mDNS. O App agora consulta o Avahi do host; se o serviço não existir, sobe um único D-Bus/Avahi compartilhado dentro do próprio App, sem iniciar um Avahi por zona e sem alterar o serviço global do HAOS. O painel passa a mostrar o modo e o diagnóstico do responder mDNS.

A descoberta AirPlay 2 e o áudio físico continuam pendentes até a seleção no iPhone, entrega ao amplificador e escuta nas caixas.

## v1.4.4

Esta atualização corrige a verificação operacional dos endpoints AirPlay 2. O App não apresenta mais um processo encerrado como se estivesse anunciado: o endereço LAN é aplicado somente em runtime, o registro `_airplay._tcp` é explícito e o diagnóstico mantém as últimas linhas sanitizadas do Shairport Sync.

O seletor Apple ainda precisa ser testado com áudio real. `Cozinha Room` e `Piscina Room` continuam sendo os receivers LinkPlay existentes no HomeKit Bridge; eles não são usados como prova de que `TecnoHead Cozinha` e `TecnoHead Piscina` foram anunciados.

## v1.4.3 — porta dedicada para AirPlay 2 em rede do host

A imagem usa a porta 18199 para o Ingress e para o stream local do App. A mudança resolve o conflito de bind observado quando a rede do host é necessária para mDNS/RAOP/NQPTP. Não altera a lógica de cenas, IR, LinkPlay, HDMI ARC ou HomeKit Bridge.

## v1.4.2 — imagem AirPlay 2 compatível com Alpine 3.23

Corrige o build da imagem removendo `libsoxr-dev`, pacote que não existe no Alpine 3.23 atual. O Shairport Sync continua compilado com AirPlay 2, NQPTP, Avahi, stdout e FFmpeg; a saída usa a interpolação básica embutida. Não altera cenas, IR, LinkPlay, HDMI ARC, HomeKit Bridge ou a política de homologação física.

## v1.4.1 — build instalável do AirPlay 2

Rebuild da v1.4.0 com o nome correto do pacote Alpine necessário pelo compilador AirPlay 2. Nenhuma lógica de cena, áudio, ARC ou HomeKit foi alterada.

## v1.4.0 — receptor AirPlay 2 virtual

Esta versão mantém as cenas, IR via Home Assistant, LinkPlay, MQTT e HomeKit Bridge e adiciona a implementação do receptor AirPlay 2 no próprio App. Shairport Sync e NQPTP são compilados a partir de revisões upstream fixadas; Cozinha e Piscina têm identidades e portas independentes. O áudio recebido é convertido em PCM→MP3 e encaminhado ao `media_player` LinkPlay pela API autenticada do Home Assistant.

O release ainda não representa homologação física. O operador precisa confirmar no iPhone que `TecnoHead Cozinha` aparece no seletor AirPlay e que o som sai nas caixas; depois repetir para a Piscina com HDMI ARC protegido. O app Casa/HomeKit Bridge deve ser avaliado separadamente. Nenhuma seleção dupla, grupo LinkPlay ou tomada da fonte ARC será feita automaticamente.

## v1.3.2 — correção do volume LinkPlay

Esta versão corrige o erro `401 Unauthorized` ao aplicar volume no painel de áudio. O App agora envia chamadas `media_player` pela API WebSocket autenticada do Home Assistant, sem retry REST ambíguo. O teste físico continua sendo feito em volume baixo e com confirmação do operador.

## v1.3.1 — intervalo IR do handoff

Corrige o default do desligamento do projetor para OFF → espera de 5,0 s após o retorno da primeira chamada → OFF. Nenhuma chamada IR é realizada durante a atualização; a confirmação física continua pendente.

## v1.3.0 — módulo Áudio Multiroom

Esta release preserva Cinema/TV/IR/clima/luzes/MQTT da v1.2 e adiciona o painel de áudio para zonas por área. Volume, mudo, fontes e agrupamento só usam entidades `media_player` reais do Home Assistant; não há cliente LinkPlay proprietário e HDMI ARC da Piscina não é alterado automaticamente.

O HAOS real consultado em 18/10/2026 não apresentou integração LinkPlay nem o `media_player` do amplificador novo da Piscina. Consequentemente, a ponte AirPlay 2 virtual não foi iniciada, nenhum destino Apple foi anunciado e nenhum teste físico de áudio foi alegado. O desbloqueio requer o modelo/entidade do amplificador atual e, depois, iPhone para a homologação G2–G5.

Testes automatizados desta alteração: `15 passed`, Ruff e sintaxe JavaScript passaram. A instalação/atualização e os testes físicos permanecem uma etapa posterior ao commit/release.

## v1.2.11

Correção operacional observada no comissionamento: uma cena Cinema com degradação opcional (por exemplo, posição de aleta não confirmada) agora permanece logicamente ativa e executa o temporizador cancelável de iluminação. O intervalo padrão entre as duas chamadas independentes de desligamento IR foi ajustado para 4,0 s, mantendo a validação por entidade `remote` do Home Assistant e sem `num_repeats`.

O teste físico do projetor, das luzes, do telão e das cenas continua dependendo da observação manual; a API aceita pela integração não é tratada como confirmação física.

## v1.2.10

## v1.2.10

Revisão operacional para comissionamento: validação do emissor sem transmissão, degradação controlada de equipamentos opcionais e área sugerida no MQTT Discovery. Nenhuma chamada física é realizada na instalação durante a atualização.

Esta release corrige a entrada do contêiner para carregar o `SUPERVISOR_TOKEN` pelo ambiente do Home Assistant. Ela mantém as correções de empacotamento e MQTT das versões anteriores. O BroadLink existente continua sendo responsabilidade da integração do Home Assistant; o App não fala diretamente com o equipamento.

Antes de marcar a instalação como homologada, o instalador deve executar o checklist físico de [TEST_PLAN.md](docs/TEST_PLAN.md), registrar a versão instalada e anexar capturas reais. Sem acesso ao HAOS e aos equipamentos, a release deve ser tratada como instalável e parcialmente testada.
## v1.2.8

Correção operacional do editor Ingress: o polling de diagnóstico não sobrescreve mais um cadastro de área enquanto ele está sendo preenchido.
## v1.2.9

Alinha a versão exibida no painel e nos metadados internos com a versão instalada pelo catálogo HAOS.
