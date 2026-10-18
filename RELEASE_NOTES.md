# Release notes

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
