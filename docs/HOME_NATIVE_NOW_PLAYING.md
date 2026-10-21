# Now Playing nativo no app Casa — arquitetura e limite atual

O destino `TecnoHead Cozinha` ou `TecnoHead Piscina` é o **próprio** acessório AirPlay 2 adotado no app Casa. Seu áudio passa por Shairport Sync, PCM e o `media_player` LinkPlay físico. O HomeKit Bridge é uma superfície distinta; este projeto não adiciona outro Receiver ou `media_player` para contornar o cartão “Controles não disponíveis”.

Um WiiM Amp comercial na mesma casa **mostrou** faixa, capa e controles no próprio cartão Casa (captura privada do usuário). Portanto a impossibilidade genérica para todo receptor de terceiro não está demonstrada. O anúncio AirPlay do WiiM difere dos TecnoHead em `features` e em `flags`. A readopção controlada da Cozinha ativou legitimamente o bit de acesso Casa e trouxe conexões Remote Control Only, **mas a UI continuou sem controles**. Essa pista de negociação não é receita de copiar identidade nem correção homologada. Ver [comparação e ensaio físico](APPLE_MEDIAREMOTE_RESEARCH.md#comparador-positivo-wiim-amp-no-mesmo-ambiente).

A [RC7 ensaiou](APPLE_FEATURE_COMPARISON_TRIAL.md#resultado-de-campo--rc7) a interseção de `features` anunciada por WiiM e Denon **somente na Cozinha**. O iPhone não conseguiu estabelecer reprodução estável e mostrou “Não foi possível conectar”; o teste foi interrompido antes do cartão Casa. A opção voltou a `off`, o anúncio original retornou e o usuário confirmou som normal na Cozinha. Portanto essa máscara não pode ser adotada como definitiva e não demonstra controle nativo no Casa.

Shairport Sync 5.6 pode receber metadados e enviar comandos ao iPhone de origem. Isso comprova capacidade de controle no **backend** quando testada; não obriga o app Casa a apresentar capa, faixa, play/pause e volume no cartão do acessório. A [issue upstream #2182](https://github.com/mikebrady/shairport-sync/issues/2182) reproduz a mesma tela e descreve um ensaio com entrega/ACK de Now Playing sem liberação do cartão. O relato sugere classificação Apple como obstáculo, mas não é prova física da instalação TecnoHead nem documentação pública de API Apple.

A RC5 oferece apenas um ensaio reversível do formato de metadados solicitado ao iPhone em **uma** zona por vez (`apple_legacy_metadata_zone`, `off` por padrão). Não acrescenta entidade HomeKit, não muda modelo/identidade e não habilita controles Casa por declaração. O ensaio físico na Cozinha confirmou áudio audível, mas o mesmo cartão Casa continuou sem controles, inclusive após readopção controlada que ativou o bit de acesso Casa e negociou Remote Control Only. A opção foi devolvida a `off`; sessões Apple Music separadas tiveram som normal na Cozinha e na Piscina após o rollback. ARC/CEC e TV→Cozinha não foram retestados nessa etapa. A RC5 não foi transformada em solução estável.

Nesta etapa, o Supervisor identifica o App de ensaio instalado como `1.4.17-rc.7` no **mesmo** App; o cabeçalho interno ainda exibe `v1.4.17-rc.5` porque a constante de versão do código não foi atualizada na RC7. A opção de comparação RC7 está novamente `off`. Nenhum ensaio de cópia de `features` ficou ativo. A sonda opcional observa `ssnc/copl` por zona; fica desativada por padrão para outras instalações e foi ligada explicitamente no HAOS de ensaio. A primeira sessão Cozinha na RC2 mostrou fluxo PCM ativo, mas revelou que o parser descartava itens do pipe por esperar uma quebra de linha que o Shairport não escreve. A [RC3](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.3) corrigiu essa leitura. Em testes separados com Apple Music e Cozinha/Piscina, o usuário confirmou som audível em ambas; a sonda observou Now Playing, comandos suportados e campos de faixa/arte na zona correta, sem cruzamento. A [RC4](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.4) acrescentou somente marcadores de diagnóstico de conexão Remote Control Only no Shairport pinado. Nos retestes RC4 de **ambas** as zonas, o usuário confirmou som audível e **Casa sem controles**; chegaram eventos Now Playing por zona, mas nenhum marcador RC foi observado ao abrir os cartões. Após readopção RC4, o canal RC apareceu, sem mudar a UI. Na RC5, o usuário confirmou áudio da Cozinha; com metadados clássicos e nova readopção, houve `SETUP/event/updateInfo ACK = 2/2/2`, mas o Casa ainda exibiu **“Controles não disponíveis”**. O ensaio foi revertido a `off`, com ambas as zonas anunciadas novamente. A sonda não retransmite metadados ao hub e não é uma correção do Casa. O build `cf6998d` posterior a Shairport Sync 5.6 e NQPTP `1.2.9`/`smi11` permanecem os mesmos. O estado de acesso Casa **e a lista de controladores pareados** desse Shairport são voláteis, conforme auditoria do código: não persistem após reinício do processo. Isso prejudica a continuidade do pareamento, mas **não é causa suficiente** da tela vazia, pois a UI falhou também com estado Casa e RC recém-negociados. A identidade AirPlay não foi alterada. A RC2 e a RC3 impedem que o token do stream apareça em novos logs de acesso HTTP.

Critério de conclusão: D16–D19 somente PASSAM com captura real do **mesmo** acessório Cozinha e Piscina no iPhone, metadados e controles visíveis, toque em play/pause/volume e resposta física observada. A correção da tela **não está homologada**: há capturas basais da v1.4.16 e falhas relatadas pelo usuário nos retestes Cozinha/Piscina RC3, RC4 e Cozinha RC5, apesar de som audível. O HomePod consta como central **Conectado** e na mesma rede Wi‑Fi doméstica do iPhone; isso elimina a ausência de central ou rede de convidados diferente como explicações simples, mas não comprova alcance TCP ao App nem o gate de classificação Apple. A conexão RC observada foi associada à readopção e respondeu a `updateInfo` stock; não houve correlação comprovada com a sessão musical ou entrega de Now Playing ao hub. Não criar fallback sem decisão do usuário.

A RC8 adiciona apenas uma POC opt-in de encaminhamento de Now Playing/SupportedCommands da sessão de áudio ao event port de uma conexão Remote Control Only negociada no **mesmo processo receptor**. Ela não modifica PCM/LinkPlay, anúncio AirPlay, identidade ou HomeKit. Limite por payload e limpeza na troca de sessão evitam buffer fixo e metadados obsoletos. A opção `apple_mediaremote_forward_zone` inicia em `off`, aceita apenas `kitchen` e pode ser revertida a `off` pelo Supervisor. Os ACKs são telemetria de transporte, não de interface; os testes físicos Casa ainda são necessários. Uma vez que o Shairport corrente não autentica o peer RC contra uma lista persistente, não expor o conteúdo fora da LAN de ensaio e não promover a flag a padrão de produção. O estado de acesso Casa continua volátil após reiniciar o receptor.

A RC8 foi instalada no HAOS com backup RC7. Sem retorno do teste físico do iPhone, a flag foi devolvida a `off`; o App permaneceu em funcionamento e os dois destinos foram anunciados. Não há evidência nova de controles no Casa, nem readopção desta versão. Para uma futura prova física, reativar só `kitchen` por janela curta, confirmar áudio audível e obter autorização separada antes de remover/readicionar a Cozinha. Não habilitar Piscina ou declarar D16–D19 aprovados sem teste real.

A RC9 preparada após constatar `media_player.cozinha_room` indisponível permite o mesmo relay **somente** na Piscina quando `apple_mediaremote_forward_zone=pool`; a configuração inicial permanece `off`. Isso não muda prioridade HDMI ARC/CEC nem autoriza uso com TV ativa. A causa da indisponibilidade da Cozinha segue desconhecida. A conexão RC atual não é autenticada contra lista persistente; a opção só deve ser ligada temporariamente com consentimento informado. Sem prova física no cartão do próprio `TecnoHead Piscina`, a meta Casa continua pendente.

A RC9 foi publicada e instalada no HAOS após backup local RC8; o App e ambos os endpoints AirPlay voltaram online, e a Piscina física foi vista como pronta. O relay permaneceu `off`. Isso é apenas verificação de implantação, não homologação de D17–D19: não houve ainda áudio físico ou cartão Casa testados nesta variante. A Cozinha física continuou indisponível e requer diagnóstico separado.

Após essa instalação, houve ensaio consentido da RC9 **somente na Piscina**: áudio AirPlay recebido e som confirmado, porém o mesmo cartão do Casa ainda mostrou “Controles não disponíveis”. O relay foi revertido a `off` e o App voltou online com ambas as zonas anunciadas. Não foi observado ACK de metadados ao RC durante a janela; portanto o ensaio não comprova entrega de capa à central nem resolve a classificação do acessório. Sem botões no Casa, não houve teste de play/pause/volume nativos. O foco seguinte é distinguir anúncio/ícone, bit 10 de acesso Casa, conexão RC, entrega e UI; [o laboratório offline](AIRPLAY_TRIAL_LAB.md) registra esses checkpoints sem alterar o HAOS.

Consulte [APPLE_MEDIAREMOTE_RESEARCH.md](APPLE_MEDIAREMOTE_RESEARCH.md) para evidências/hipóteses e [MEDIAREMOTE_D01_D24.md](MEDIAREMOTE_D01_D24.md) para o checklist de homologação.

No ensaio isolado v0.1.4/M1, o Lab já recebia música quando foi readicionado
ao Casa. O mesmo processo Shairport encaminhou snapshots reais de
SupportedCommands e Now Playing ao event port Remote Control Only e recebeu
resposta RTSP 2xx para ambos, mas o cartão continuou “Controles não
disponíveis”. O 2xx confirma transporte naquele canal, **não** identificação
do peer como HomePod, interpretação semântica, nem habilitação da UI. O Lab
voltou a B0; a instalação funcional das zonas reais não recebeu essa mudança.

No ensaio seguinte, Lab v0.1.5/M1 com modelo **TecnoHead AirPlay Lab** e bits
clássicos 15–17 adicionais (sem MFi), o iPhone conectou e enviou metadados
com capa. O ícone permaneceu genérico. Após readopção somente do Lab com a
faixa já em reprodução, o gate RC ficou elegível e o peer respondeu RTSP 2xx
aos snapshots de comandos e Now Playing; mesmo assim, o próprio cartão Casa
continuou “Controles não disponíveis”. Assim, essa combinação legítima de
anúncio + transporte RC não resolve a interface. Não prova que o peer era a
central, que interpretou o payload ou que uma exigência fechada específica
da Apple seja a causa. O Lab voltou a `B0/stock` e foi parado **após esse
ensaio v0.1.5**; o App principal permaneceu parado, sem mudança nas zonas
reais. Não há novo Receiver/Bridge.

O teste posterior em Lab v0.1.6 isolou IPv6: publicação AAAA e sessão
efetivamente IPv6, mas o cartão Casa ainda vazio. A combinação subsequente
`M1/tecnohead_model_classic_bits/dual_stack` manteve o AirPlay conectado e
obteve gate RC e respostas RTSP 2xx a Now Playing e SupportedCommands após
readopção do próprio Lab com música tocando; a interface continuou sem
controles. Assim, nem IPv6 isolado nem a combinação legítima ensaiada
homologaram a tela. O estado atual do Lab é essa última combinação em
execução, por solicitação do usuário; produção permanece parada. O ícone
comercial de speaker ainda não foi reproduzido, e não há demonstração de
qual bit/campo habilita o cartão. Ver [resultado v0.1.6](AIRPLAY_TRIAL_LAB.md#ensaio-combinado-v016--ipv6-anúncio-próprio-e-relay-rc).
