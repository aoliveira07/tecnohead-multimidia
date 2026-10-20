# Changelog

## 1.4.17-rc.6 — retomada limitada do áudio após falha temporária do HA

**Pré-release para atualização manual; não corrige os controles no app Casa.** Em um grupo AirPlay 2 iPhone→WiiM Amp + TecnoHead Cozinha, a primeira tentativa não iniciou a saída da Cozinha; o diagnóstico do App registrou WebSocket do Home Assistant temporariamente indisponível. Ao refazer a seleção pelo iPhone, o usuário confirmou áudio simultâneo nas duas caixas. Esta versão tenta novamente a mesma saída local somente enquanto a sessão AirPlay continua recebendo áudio, com intervalos e número de tentativas limitados. Falhas de área/capacidade não são repetidas e zonas com prioridade HDMI ARC (Piscina) **não** fazem retomada automática. Não mistura agrupamento AirPlay com LinkPlay, não altera Shairport/NQPTP, pareamento ou entidades, nem declara D20 ou o cartão Casa homologados. A instalação reinicia o App e interrompe sessões AirPlay ativas; requer reteste físico.

## 1.4.17-rc.5 — ensaio isolado de metadados clássicos AirPlay

**Pré-release para atualização manual; não é correção homologada do app Casa.** Adiciona a opção `apple_legacy_metadata_zone`, inicialmente `off`, que permite escolher **uma** zona (`kitchen` ou `pool`) para solicitar os metadados clássicos do Shairport Sync durante AirPlay 2, incluindo arte. O caminho é um modo de compatibilidade **deprecated** no upstream, usado apenas para investigar a diferença de capacidades observada frente ao WiiM; não anuncia identidade ou funções do WiiM. Com a opção desligada, as configurações das duas zonas ficam como na RC4. Com `kitchen`, a Piscina mantém a configuração anterior; áudio PCM, volume, LinkPlay, ARC/CEC, cenas e pareamento não são alterados pelo código. A atualização reinicia o App e interrompe sessões AirPlay em curso. Voltar a `off` e reiniciar reverte o ensaio. Não remove/repareia acessórios Apple automaticamente.

## 1.4.17-rc.4 — observação Remote Control Only

**Pré-release para atualização manual.** Acrescenta marcadores sanitizados para `SETUP` Remote Control Only, conexão do canal de eventos e ACK do `updateInfo` stock. Não encaminha Now Playing ao hub nem afirma que o cartão Casa foi corrigido.

## 1.4.17-rc.3 — leitura real do pipe de metadados

**Pré-release para atualização manual.** Corrige o enquadramento do pipe de metadados conforme o código fixado do Shairport Sync: os bytes Base64 e `</data></item>` chegam sem uma quebra de linha entre eles. A leitura anterior descartava silenciosamente esses itens, embora testes sintéticos com quebra extra passassem. A nova leitura usa comprimento declarado, limita memória e descarta itens grandes em blocos. A sonda opt-in acrescenta contagens de itens e de volume, sem guardar faixa, capa ou conteúdo do plist. O caminho de áudio PCM, saída LinkPlay, volume por hook/D-Bus, ARC, cenas e identidade Apple não muda. **Esta RC não corrige nem declara corrigido o cartão do app Casa; requer novo teste físico.**

## 1.4.17-rc.2 — proteção do token do stream nos logs

**Pré-release para atualização manual.** Desativa o log de acesso HTTP do Uvicorn nos dois pontos de entrada do App, pois o endereço do stream AirPlay contém um token de sessão que antes aparecia nos logs locais do HAOS. Os eventos operacionais internos permanecem ativos. A sonda MediaRemote segue opt-in e a interface nativa de reprodução do app Casa continua pendente de comprovação; esta versão não a declara corrigida. Não copiar logs antigos que contenham URLs de stream.

## 1.4.17-rc.1 — diagnóstico MediaRemote (pré-release, instalação manual)

**Requer atenção:** esta versão de ensaio não corrige, por si só, “Controles não disponíveis” no app Casa. A atualização reinicia o App e interrompe sessões AirPlay ativas. Faça backup e instale manualmente; a versão está em `breaking_versions` para impedir atualização automática. O recurso de observação fica desligado por padrão.

- Adiciona uma sonda opt-in de eventos MediaRemote recebidos de cada emissor AirPlay, com contagens e nomes de campos, sem armazenar faixas, capas, áudio ou dados de pareamento.
- Mantém intactos os destinos AirPlay, a saída LinkPlay, o sincronismo de volume, ARC/CEC e as cenas; erro de metadado não interrompe a ponte de volume.
- Publica a imagem RC sem mover a tag `latest`. O retorno conservador é restaurar o backup local pré-MediaRemote ou instalar uma nova versão estável após validar a migração; não reparear acessórios Apple durante o ensaio.

## 1.4.16 — estabilização do volume com duas zonas AirPlay

- Serializa os comandos de volume por zona e descarta posições ultrapassadas durante um arraste rápido do slider no iPhone, sem bloquear a outra zona.
- Reconhece respostas atrasadas do LinkPlay para todas as posições recentes e evita devolvê-las ao iPhone como se fossem alterações do AudioCast; mudanças externas voltam a ser espelhadas após estabilização.
- Mantém gancho, metadados e leitura D-Bus como caminhos de entrada, mas impede que fallbacks atrasados concorram imediatamente com o gancho nativo.
- Corrige os horários do diagnóstico de volume e acrescenta indicadores de comandos pendentes/estabilização. Teste físico nas duas zonas continua obrigatório.

## 1.4.15 — orientação Apple Casa no painel

- adiciona ao painel de áudio a distinção entre os receivers `Cozinha Room`/`Piscina Room` do HomeKit Bridge e os destinos AirPlay 2 `TecnoHead Cozinha`/`TecnoHead Piscina`;
- documenta o fluxo de adoção pelo app Casa e a regra de não misturar seleção dupla AirPlay com agrupamento LinkPlay;
- mantém o controle físico, a prioridade HDMI ARC e o volume seguro sem alterar a configuração do Home Assistant.

## 1.4.14 — fallback de leitura do volume AirPlay

- Lê a propriedade `AirplayVolume` do D-Bus privado do Shairport Sync durante uma sessão ativa.
- Encaminha mudanças do slider do iPhone ao `media_player` LinkPlay mesmo quando o gancho ou o evento `ssnc/pvol` não chega naquele instante.
- Mantém o PCM em ganho pleno, o teto de volume por zona e a proteção anti-eco da v1.4.13.

## 1.4.13 — estabilização do retorno de volume AirPlay

- Evita o laço de realimentação que fazia o slider AirPlay oscilar quando o LinkPlay arredondava o valor retornado pelo amplificador.
- Aplica tolerância de dois pontos e janela curta de eco nos caminhos iPhone → LinkPlay e LinkPlay → iPhone.
- Deduplica eventos físicos repetidos e expõe os últimos sentidos de sincronização no diagnóstico.

## 1.4.12 — sincronização bidirecional de volume AirPlay

- Encaminha alterações externas do volume LinkPlay/AudioCast para a sessão AirPlay 2 ativa pelo `SetAirplayVolume` nativo do Shairport Sync.
- Isola o D-Bus de controle por endpoint para que Cozinha e Piscina não compartilhem o mesmo nome de serviço.
- Suprime ecos do próprio encaminhamento e só sincroniza enquanto a zona tem uma sessão AirPlay ativa.

## 1.4.11 — gancho nativo de volume AirPlay

- Usa `run_this_when_volume_is_set` do Shairport Sync para encaminhar cada alteração do slider AirPlay por socket Unix privado ao App.
- Mantém o caminho `ssnc/pvol` como fallback e o PCM em ganho pleno, fazendo o `media_player` LinkPlay controlar o volume audível.
- Expõe no diagnóstico a origem e a atividade da ponte de volume, sem registrar payloads ou dados privados.

## 1.4.10 — leitor de metadados AirPlay resiliente

- Aumenta o limite do leitor FIFO de metadados para aceitar itens grandes antes do próximo evento `ssnc/pvol`.
- Evita que uma mensagem longa encerre a ponte de volume e deixe o player LinkPlay preso no último valor.
- Mantém o PCM em ganho pleno e o encaminhamento de volume pela API do Home Assistant.

## 1.4.9 — volume AirPlay encaminhado ao LinkPlay

- Mantém o PCM AirPlay em ganho pleno e encaminha o evento `ssnc/pvol` para `media_player.volume_set` da zona correspondente via Home Assistant.
- Usa uma FIFO de metadados exclusiva por endpoint, evitando colisão entre Cozinha e Piscina.
- Mantém o teto de volume configurado por zona e não altera a política HDMI ARC.

## 1.4.8 — volume AirPlay ativo

- Corrige o volume dos destinos AirPlay 2: o Shairport Sync deixa de ignorar o volume enviado pelo iPhone e aplica a atenuação no PCM antes da ponte HTTP para o LinkPlay.
- Mantém o volume físico de cada `media_player` como controle separado pelo painel TecnoHead/Home Assistant.

## 1.4.7 — AirPlay explícito com ARC observado

- Remove o bloqueio que recusava AirPlay na Piscina quando a última fonte observada era HDMI/ARC.
- Mantém a troca automática de fonte da TV/CEC sob responsabilidade do amplificador, sem o App disputar a fonte.
- Ao parar, preserva a proteção da TV: se o player já retornou a ARC, o App não envia `media_stop`.
- Atualiza o editor e a documentação para refletir a política operacional real.

## 1.4.6 — política D-Bus do responder mDNS

- Permite no barramento D-Bus privado do App as respostas e sinais necessários entre Avahi e Shairport Sync.
- Mantém um único responder mDNS interno, sem alterar o Avahi global do HAOS.
- Não altera LinkPlay, HDMI ARC, HomeKit Bridge ou cenas existentes.

## 1.4.5 — responder mDNS compartilhado para AirPlay 2

- Verifica se o HAOS oferece Avahi no D-Bus antes de iniciar os receptores.
- Quando o host não oferece Avahi, inicia um único D-Bus/Avahi interno do App para as duas instâncias, sem iniciar dois respondentes nem alterar o serviço global do HAOS.
- Propaga o barramento selecionado aos processos Shairport Sync e expõe diagnóstico sanitizado do modo mDNS e dos processos auxiliares.

## 1.4.4 — diagnóstico de anúncio AirPlay 2

- Vincula cada receptor Shairport Sync ao endereço LAN resolvido em tempo de execução e explicita o registro mDNS AirPlay 2.
- Detecta quando o processo Shairport Sync encerra após iniciar, em vez de manter um falso estado “Visível no AirPlay”.
- Mantém uma cauda sanitizada do log do endpoint para diagnosticar Avahi/D-Bus sem expor IPs ou credenciais.

## 1.4.3 — porta dedicada para host network

- Move o Ingress e o stream local para a porta 18199, evitando o conflito observado na atualização para rede do host.
- Mantém a ponte AirPlay 2, as duas identidades, proteção HDMI ARC, LinkPlay e todas as funções v1.2/v1.3.

## 1.4.2 — compatibilidade do build AirPlay 2

- Remove a dependência opcional `libsoxr-dev`, ausente no Alpine 3.23, e usa a interpolação básica embutida do Shairport Sync.
- Mantém AirPlay 2, NQPTP, PCM→LinkPlay, proteção ARC e o restante do App sem alteração funcional.

## 1.4.1 — correção de pacote Alpine

- Corrige o nome do pacote `libplist-util` usado para compilar o suporte AirPlay 2 no Alpine.
- Mantém a implementação e os commits upstream fixados da v1.4.0.

## 1.4.0 — AirPlay 2 virtual instalável

- Empacota Shairport Sync upstream com AirPlay 2 real e NQPTP em revisões fixadas.
- Adiciona duas identidades independentes, Cozinha e Piscina, com portas RAOP distintas, NQPTP compartilhado e mDNS do host.
- Converte PCM recebido para stream local e solicita reprodução ao LinkPlay através de `media_player.play_media` do Home Assistant.
- Protege HDMI ARC da Piscina por padrão e bloqueia tomada silenciosa da fonte da TV.
- Mantém o HomeKit Bridge existente separado dos destinos AirPlay; homologação física no iPhone continua obrigatória.
- Adiciona rota de stream temporária, diagnósticos por endpoint e testes unitários de ponte/ARC.

## 1.3.2 — service calls via WebSocket

- Corrige `401 Unauthorized` no controle de volume do LinkPlay usando a API WebSocket autenticada do Home Assistant para chamadas de serviço.
- Mantém chamadas únicas, sem fallback REST que pudesse duplicar comandos físicos IR.
- Adiciona teste automatizado da estrutura `call_service` com `target` e `service_data`.

## 1.3.1 — alinhamento do intervalo IR

- Restaura o default do desligamento do projetor para duas chamadas independentes com espera de 5 s após o retorno da primeira, conforme o handoff v1.3.
- Mantém valores personalizados persistidos; o perfil Cinema instalado foi alinhado para 5,0 s sem transmitir IR.

## 1.3.0 — áudio multiroom protegido

- Adiciona zonas Cozinha/Piscina ao mesmo App, com filtro estrito por área e cadastro do `media_player` canônico.
- Adiciona volume limitado, mudo, fontes anunciadas, diagnóstico e agrupamento explícito via serviços `media_player` do Home Assistant.
- Preserva a prioridade HDMI ARC da Piscina e impede automaticamente a ponte AirPlay quando não existe destino físico LinkPlay comprovado.
- Adiciona MQTT Discovery de estado e controles de áudio quando as capabilities reais existem.
- Migra o schema local v1.2 para v1.3 sem perder perfis Cinema, IR, clima, luzes e MQTT.
- Registra o bloqueio real atual: não foi encontrada integração LinkPlay nem entidade do amplificador novo da Piscina; AirPlay 2 e Apple Casa permanecem não homologados.
- Adiciona documentação e matriz B01–B45 sanitizadas.

## 1.2.11

- Corrige a manutenção do modo lógico em cenas parcialmente degradadas, permitindo que o temporizador de iluminação execute mesmo quando a aleta não puder ser confirmada.
- Mantém switches fora da classificação de iluminação protegidos e adiciona regressão automatizada para as três luzes descobertas da área.
- Ajusta a sequência do projetor para duas chamadas OFF independentes com intervalo configurável padrão de 4 s após o retorno da primeira chamada.

## 1.2.10

- Validação segura da entidade `remote` por área sem emitir IR.
- Cenas continuam as etapas independentes quando receiver, Apple TV ou climatização estão indisponíveis, registrando a degradação.
- MQTT Discovery informa a área sugerida do dispositivo.

## 1.2.3 — correção do ambiente do App

- Executa o entrypoint pelo `with-contenv` do Home Assistant para disponibilizar `SUPERVISOR_TOKEN` ao processo.

## 1.2.2 — correção do empacotamento HAOS

- Organiza o App em diretório próprio de repositório Home Assistant.
- Corrige o contexto do Docker e a validação de metadata para instalação pelo catálogo de Apps.

## 1.2.1 — correção de MQTT

- Corrige a criação do cliente MQTT seguro usando `tls_context` da API atual do `aiomqtt`.
- Mantém a arquitetura IR da 1.2.0 e os defaults ON1/OFF2/5s.

## 1.2.0 — inicial

- Arquitetura corrigida para selecionar entidade `remote` do Home Assistant por área.
- Transporte `remote.send_command` com presets Base64 e sequência OFF independente 2× com 5 s.
- Persistência privada, migração de schema, restauração de presets e validação de formatos.
- Motor multiambiente para Cinema, TV, OFF e evento de TV física.
- Descoberta efetiva por área, clima, luzes classificadas e MQTT Discovery.
- UI TecnoHead em português brasileiro e documentação de implantação.
## 1.2.8

- Corrige a persistência do editor de ambientes durante a atualização periódica do painel: alterações em andamento não são sobrescritas pelo polling de status.
## 1.2.9

- Alinha a versão exibida no painel, no runtime, nos metadados MQTT e no pacote do App.
