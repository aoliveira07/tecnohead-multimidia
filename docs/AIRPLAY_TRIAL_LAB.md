# Laboratório local de ensaios AirPlay/Casa

## Receptor de laboratório independente (20/10/2026)

O App de produção **TecnoHead Multimídia** foi parado no HAOS e a opção
**Iniciar no arranque** foi desligada. Nada foi desinstalado ou apagado; a
configuração e a identidade dos acessórios antigos foram preservadas. O App
separado [`tecnohead_airplay_lab/`](../tecnohead_airplay_lab/) contém um único
receptor descartável, com nome/ID próprios e porta 7100. Seu PCM é drenado
para descarte; não existe integração com HA Core, MQTT, cenas nem LinkPlay.

No laboratório, B0/M1/M2/M3 variam apenas o pedido de metadados clássicos e o
relay MediaRemote já presente no binário RC9. Nenhum perfil copia a máscara de
WiiM/Denon, anuncia MFi, altera o modelo para Apple/comercial ou falsifica
pareamento. A adoção desse novo receptor no app Casa pode ser refeita entre
ensaios sem mexer nos antigos, como autorizado pelo usuário. A conexão RC
legítima e o resultado visual ainda precisam ser medidos fisicamente; não
há declaração de sucesso do cartão neste ponto.

Uma branch de repositório do HAOS pode ser instalada separadamente da loja
estável usando `#branch`, conforme a documentação oficial do Supervisor.
Depois da instalação, mudar o perfil na aba Configuração do Lab e reiniciar
**somente o Lab**. Examinar os contadores saneados em Registo e o mesmo cartão
no iPhone. Ao terminar, parar o Lab; ele usa `boot: manual`. Para restaurar o
App original, habilitar seu próprio início automático e pressionar Iniciar.

Estado observado em 20/10/2026: o commit `36bf0ee` foi publicado somente na
branch `codex/airplay-lab`, sem merge ou release estável. O repositório dessa
branch foi adicionado separadamente à loja HAOS; o Supervisor instalou o App
`TecnoHead AirPlay Lab` v0.1.0 e mostrou **Em funcionamento**, `boot` desligado.
A aba Configuração confirmou perfil B0 e o log saneado mostrou `lab_ready`,
porta 7100 e saída `discarded`. Antes do ensaio com o iPhone, os contadores
permaneciam sem PCM, Now Playing ou RC. Isso **não comprova** descoberta pelo
iPhone, adoção Casa ou controles nativos; esses resultados dependem do teste
físico. O App TecnoHead Multimídia original permaneceu **Parado**, com início
automático desligado; suas configurações não foram removidas.
O Kanban oficial Smart House continua sem conexão de escrita identificada nesta
sessão; este registro versionado é provisório e não substitui a atualização do
Kanban quando houver acesso autorizado.

Primeira observação física do perfil B0: o usuário encontrou **TecnoHead
AirPlay Lab** no seletor AirPlay, adicionou o novo receptor ao app Casa e viu
“Controles não disponíveis” no seu cartão. Os contadores consultados em
seguida ainda registravam `pcm_bytes_discarded=0`, sem Now Playing nem conexão
RC observada. Portanto, esta observação comprova descoberta e adoção, mas
**não** avalia a interface durante reprodução; o ensaio com Apple Music ainda
é necessário.

Durante a sessão de Apple Music no perfil B0, os contadores finais saneados
registraram 476.328.008 bytes de PCM descartado, 24 eventos
`updateMRNowPlayingInfo` e 11 `updateMRSupportedCommands`. O registro assinalou
presença de título, artista, álbum, capa, duração e posição (sem gravar seus
valores). Houve `RC_SETUP_OK`, `RC_EVENT_CONNECTED` e `RC_UPDATE_INFO_ACK`,
uma vez cada. O usuário confirmou que o AirPlay permaneceu conectado e o
cartão do **mesmo Lab** no Casa continuou “Controles não disponíveis”. O perfil
B0 **não** encaminha Now Playing ao RC; a conexão/ACK por si só não habilita a
interface. O parser encerrou com 9 itens inválidos; sua causa não foi
classificada e não deve ser confundida com falha da sessão inteira.

Em seguida, o perfil M1 (relay RC ligado, metadados clássicos ainda desligados)
foi salvo e **somente o Lab** reiniciado. O novo log confirmou `lab_ready` em
M1. Após readopção somente do Lab, o usuário confirmou que o AirPlay conectou,
mas o cartão Casa continuou “Controles não disponíveis”. A sessão M1 recebeu
6 Now Playing, 5 SupportedCommands e cerca de 59,8 MB de PCM. O `GET /info`
somente de leitura durante a sessão mostrou `flags=0x20404`, portanto o bit
de acesso Casa estava legitimamente ativo. Sete conexões RC foram registradas,
mas **nenhum marcador de envio de Now Playing/Commands** apareceu. Isso torna
M1 inconclusivo quanto à aceitação da Apple: não há prova de que esses dados
tenham sido efetivamente entregues ao hub. O relay foi devolvido a B0.

Na preparação de v0.1.1, um erro de configuração do perfil combinado M3 foi
corrigido: `get_plist_metadata=no` fica restrito a M2. M3 agora solicita os
metadados clássicos **sem desligar** os eventos plist que o relay precisa.
Contadores de tamanho máximo das duas classes de eventos foram acrescentados
sem registrar payload, e o encerramento do Lab não deve classificar um stop
normal como falha. O App Lab v0.1.1 foi instalado e executou M3. Depois de
readotar **somente o Lab**, o usuário reproduziu Apple Music nele e informou
que o cartão Casa continuava **“Controles não disponíveis”**. Os contadores
finais saneados de M3 mostraram 29.333.632 bytes de PCM descartado, 3 eventos
Now Playing, 4 SupportedCommands, os campos título/artista/álbum/capa/duração/
posição, maior plist Now Playing de 237.231 bytes e maior SupportedCommands de
7.775 bytes — ambos abaixo dos limites do patch. Houve 2 SETUP RC, 2 conexões
de event port e 2 respostas válidas a `updateInfo`; `GET /info` durante a
reprodução mostrou `flags=0x20404`. **Não houve marcador de envio/ACK para
Now Playing ou SupportedCommands.** Os contadores de itens clássicos ficaram
em zero apesar de o perfil os solicitar; a arte estava dentro do plist. Assim,
M3 falhou visualmente, mas ainda não demonstra rejeição de metadados enviados
pela Apple: o próximo passo é instrumentar qual gate de captura ou envio impediu
o relay, preservando apenas contadores e sem registrar payloads. O perfil voltou
a B0, confirmado por `lab_ready`; o App de produção permanece parado.

O commit experimental `631c8c6` adicionou instrumentação limitada a marcadores
de captura, propriedade da sessão, máscara de elegibilidade RC, snapshot e
resposta do event port, sem conteúdo de mídia ou identificadores de rede.
O Lab v0.1.2 usa o mesmo Shairport fixado da RC9, recompilado **somente na
imagem descartável** com um patch incremental; a imagem de produção não foi
recriada nem instalada. A CI passou nos testes e no build amd64/arm64. O
Supervisor atualizou apenas o Lab para v0.1.2, com backup da v0.1.1 solicitado.
M1 foi iniciado e `lab_ready` confirmado para um novo ensaio, mas **não houve
sessão do iPhone nem nova conexão RC** na janela observada; portanto não há
resultado físico da instrumentação. Por segurança, o Lab voltou a B0 e o log
confirmou `lab_ready` com relay desligado. Reativar M1 apenas quando o usuário
estiver pronto para readotar o Lab e executar uma faixa curta.

No ensaio seguinte, o usuário removeu e readicionou **somente o Lab** e tocou
Apple Music por aproximadamente um minuto em M1. O AirPlay conectou, mas o
próprio cartão do Lab no Casa continuou **“Controles não disponíveis”**. A
instrumentação contou duas conexões RC (`SETUP`, event port e ACK de
`updateInfo`), uma transição da máscara de gate para `31` (todos os cinco
predicados verdadeiros naquele instante), dois Now Playing e quatro
SupportedCommands no receptor. O plist de Now Playing continha título,
artista, álbum, capa, duração e posição; não foi salvo conteúdo de mídia.
Quatro registros iniciais falharam no teste de propriedade da sessão
(`RECORD_NOT_OWNER`), mas os registros seguintes de Now Playing e Commands
foram **armazenados**. Não houve marcador `SNAPSHOT_READY`, tentativa de
envio ou ACK MediaRemote no RC. Portanto, este ensaio localiza uma lacuna entre
snapshot armazenado e loop de encaminhamento; **não comprova que a Apple
recebeu e rejeitou os dados**. A hipótese imediata é verificar a sobreposição
temporal entre conexão RC elegível e sessão de áudio, inclusive vida útil das
conexões, sem alterar identidade/anúncio. Após o teste, M1 voltou a B0 e
`lab_ready` confirmou o rollback. A produção continuou parada.

Para isolar essa corrida, a versão de ensaio v0.1.3 acrescenta ao **Lab apenas**
três marcadores sem payload: limpeza da conexão RC, pulso de vida do loop a
cada cinco segundos com máscara de elegibilidade e limpeza de snapshot. A
sonda continua off em B0. Os testes automatizados verificam que o parser só
publica esses marcadores fixos e máscaras de 0 a 31, sem texto de faixa ou
peer. Este patch diagnóstico não corrige o cartão Casa por si só; requer
compilação, atualização isolada e novo teste físico antes de qualquer
conclusão sobre o protocolo.

O commit `08d8da0` passou nos testes locais do Lab (13), nos testes do App
principal (54 passaram, 1 ignorado), Ruff e em todos os jobs da CI, inclusive
builds amd64/arm64 do Lab e do App principal (run `39479829498`). O Supervisor
atualizou **somente o Lab** para v0.1.3,
solicitando backup da v0.1.2, e confirmou a nova versão em funcionamento.
M1 foi iniciado e `lab_ready` confirmado; entretanto, não houve nova sessão
AirPlay nem readopção durante a janela observada (`pcm_bytes_discarded=0`,
sem novos marcadores RC). Logo **a v0.1.3 não tem resultado físico**. M1 voltou
a B0, com `lab_ready` confirmado. Nenhum App de produção foi atualizado ou
reiniciado por este ensaio.

Resposta tardia do teste no iPhone, correlacionada com o log **após** esse
rollback: o usuário confirmou AirPlay conectado e o cartão Casa ainda sem
controles. Esta sessão ocorreu em **v0.1.3/B0**, não em M1; portanto não pode
homologar o relay da v0.1.3. O log B0 registrou duas conexões RC com ACK de
`updateInfo`; ambas emitiram `EVENT_CLEANUP` **antes** dos primeiros contadores
de PCM e metadados da música. Depois, a sonda contou três Now Playing, quatro
SupportedCommands e campos de título/arte/posição, mas nenhuma nova conexão
RC durante a janela visível. Como B0 desliga o relay, a ausência de envio MR
nesse perfil é esperada. A ordem observada sustenta uma hipótese de falta de
sobreposição entre canal RC e sessão de áudio, ainda sem provar por que o
controlador encerrou a conexão ou se outro canal é usado por receptores
comerciais. Não solicitar nova readopção só para repetir esse baseline.

Auditoria do código fixado: `EVENT_CLEANUP` é emitido quando a thread de eventos
é cancelada durante a limpeza da conexão RTSP, não identifica a causa do
encerramento. O Lab v0.1.4 adiciona apenas marcadores saneados para TEARDOWN
sem streams, fechamento do canal pelo peer, erro de leitura/escrita, shutdown
solicitado e limpeza da thread RTSP. Não altera anúncio, identidade, áudio,
relay nem portas. Antes de concluir que há rejeição pela Apple, um próximo
ensaio deverá correlacionar esses marcadores com a chegada dos metadados e,
se necessário, comparar com um receptor comercial autorizado. Até esse teste,
a causa exata da curta vida do canal RC permanece indeterminada.

Build e instalação v0.1.4: commit `ae02891` na branch isolada; testes locais
do Lab 13/13, Ruff e aplicação integral da pilha de patches passaram. A CI
`39482937480` concluiu com sucesso, inclusive as imagens amd64/arm64 do Lab.
O Supervisor atualizou **somente o Lab** de 0.1.3 para 0.1.4, com backup da
versão anterior, e confirmou “Em funcionamento”. A configuração foi então
alterada de B0 para M1; o log confirmou `lab_ready` em M1, com relay ativo.
O App principal permaneceu fora do escopo da atualização.

Resultado físico **v0.1.4/M1**: após readopção somente do Lab, o usuário
confirmou que o AirPlay conectou, mas o próprio cartão Casa continuou
“Controles não disponíveis”. O log sanitizado registrou duas conexões RC,
duas respostas de `updateInfo` e `GATE_MASK_31` em uma delas. Ambas passaram
por `TECNOHEAD_RC_RTSP_TEARDOWN_CLOSE` e limpeza da thread/event port **antes**
dos primeiros registros de áudio e Now Playing da faixa. Em seguida, o Lab
recebeu cinco `updateMRNowPlayingInfo` e cinco
`updateMRSupportedCommands` (campos de título, artista, álbum, capa,
duração e posição); quatro snapshots de faixa e dois de comandos foram
armazenados pelo relay. Não houve `SNAPSHOT_READY`, tentativa de envio
MediaRemote nem ACK desses snapshots, porque nenhuma conexão RC permaneceu
ativa nessa fase. O marcador de TEARDOWN comprova que o handler RTSP recebeu
esse método para o canal RC; os logs não identificam qual controlador o
enviou nem por que a sessão foi encerrada.

Conclusão limitada: M1 não testou a aceitação de Now Playing pelo hub/Casa.
O resultado visual é negativo, mas não demonstra um bloqueio de classificação
da Apple. Próximo ensaio proposto, **ainda não executado**: começar a sessão
AirPlay no Lab antes da adoção no Casa, para observar se uma nova conexão RC
se sobrepõe aos snapshots já disponíveis; caso o áudio seja interrompido pela
adoção, registrar isso sem atribuir falsamente o resultado à UI. Em paralelo,
comparar a duração/negociação RC de um receptor comercial autorizado, somente
se houver um ponto de captura de rede que realmente observe esse tráfego.
Não forçar a conexão após TEARDOWN nem tratar `updateInfo` ACK como ACK de
faixa. Após coletar os
contadores finais (`pcm_bytes_discarded=44341952`), M1 foi devolvido a B0;
o Supervisor confirmou Lab 0.1.4 em funcionamento e `lab_ready B0`.

### Ensaio de sobreposição v0.1.4/M1 — áudio antes da adoção

O usuário removeu **somente o Lab** do Casa e iniciou Apple Music no Lab antes
de readicioná-lo. O AirPlay permaneceu conectado durante a adoção; o usuário
abriu o mesmo cartão e confirmou **“Controles não disponíveis”**. Antes da
readopção, o Lab já tinha recebido PCM e armazenado snapshots de
Now Playing e SupportedCommands, com campos de título/arte/posição. Seis
conexões RC anteriores terminaram por RTSP TEARDOWN sem snapshots disponíveis.
Na sétima conexão RC, já com mídia ativa, ocorreram `SETUP`, event port,
`updateInfo` ACK e `GATE_MASK_31`. O Lab enviou **primeiro** SupportedCommands
e **depois** Now Playing pelo event port dessa conexão. Para cada envio,
`ap2_event_port_send_message()` leu uma resposta RTSP **2xx** cifrada;
registrou-se um `TECNOHEAD_RC_MEDIAREMOTE_ACK_COMMANDS` e um
`TECNOHEAD_RC_MEDIAREMOTE_ACK_NOW_PLAYING`. O peer em seguida enviou
`TEARDOWN`. Nenhum nome de faixa, capa, payload, endereço ou chave foi
registrado/publicado. O marcador `sender_playback_updates` ficou em zero
nesta sessão.

Este é o primeiro ensaio local que **comprova envio e resposta RTSP 2xx** para
os dois snapshots no canal RC. Não comprova que o peer era o HomePod/hub,
que interpretou semanticamente os plists, nem que o Casa aceitou a capacidade
do acessório. O resultado visual negativo impede D16–D19; não estabelece
sozinho `BLOQUEADO_POR_PLATAFORMA`. D16/D17 das zonas reais não foram
retestados aqui; sem botões no Lab, D19 também não teve ação física.
A pergunta seguinte é se o emissor da
resposta RC é a central da Casa e se esse canal/framing é o esperado para
Now Playing, comparando com fonte primária e um receptor comercial sem
falsificar identidade. O Lab foi reiniciado com a opção B0 salva; `lab_ready
B0` confirmou relay desligado. A interface de configuração mostrou B0
transitoriamente antes de terminar de carregar M1, por isso o primeiro
reinício voltou em M1; a verificação pelo log impediu deixar esse estado
experimental ativo.

## Planejador offline para Windows

O programa [`tools/airplay_trial_lab.py`](../tools/airplay_trial_lab.py) roda no Windows com Python 3.12 e Tkinter (biblioteca padrão). Iniciar no diretório do repositório com `python tools/airplay_trial_lab.py`. Para uso sem janela: `python tools/airplay_trial_lab.py --compare` ou `python tools/airplay_trial_lab.py --scenario M3 --zone pool`.

Ele **não altera o HAOS**, não emula um receptor AirPlay, não pede token e não envia música, anúncios ou dados da rede. Mostra as diferenças históricas entre `features` do TecnoHead, WiiM e Denon; gera apenas planos com três opções já existentes na RC9, para **uma zona por vez**; e registra observações do iPhone/Casa em JSON local sem nome da faixa, capa, IP ou identidade do dispositivo. Esses planos devem ser aplicados manualmente na interface autenticada do Supervisor por um operador, com backup e rollback `off` após a janela curta. A opção `apple_mediaremote_experimental` preexistente não é alterada pelo plano.

| Cenário | Máscara do anúncio | Metadados clássicos | Relay RC | Pergunta |
| --- | --- | --- | --- | --- |
| B0 | Nativa | Não | Não | Qual é o baseline atual no mesmo cartão? |
| M1 | Nativa | Não | Sim | Now Playing/SupportedCommands entregues bastam? |
| M2 | Nativa, com bits clássicos gerados pelo Shairport | Sim | Não | O formato solicitado ao emissor altera a UI? |
| M3 | Nativa, com bits clássicos gerados pelo Shairport | Sim | Sim | A combinação muda a UI? Na RC5 não se observaram eventos enriquecidos nesse modo. |

O aplicativo separa **descoberta**, **ícone**, **Now Playing recebido**, **bit 10/HK Access Control**, **conexão RC**, **ACK no RC**, **capa/faixa no Casa** e **botões no Casa**. Ícone ou ACK não equivalem a controles nativos. Som audível não é critério deste ciclo, mas uma sessão AirPlay ativa ainda é necessária para produzir metadados reais; se falhar a negociação, a ausência de capa é inconclusiva para o gate da UI. Comandos só podem ser marcados funcionais após toque no Casa e reação da origem; o campo “botões ativos” sozinho não dá D19.

Na POC RC9, o envio ao RC requer `Enable_HK_Access_Control` legítimo, conexão RC estabelecida e sessão de áudio correspondente. O teste físico na Piscina teve som, mas o usuário ainda viu “Controles não disponíveis”; **não foi capturado ACK de Now Playing/Commands**. Após o rollback, a leitura mDNS somente de campos permitidos mostrou `flags=0x4` nas duas instâncias TecnoHead, versus `0x404` no WiiM, e a opção RC estava `off`. O estado `0x4` após reinício **não prova** qual era o valor durante o ensaio, mas evidencia que ativar a flag por si só não garante o gate de HK Access. Não chamar o ensaio RC9 de prova de que a Apple rejeitou metadados efetivamente entregues.

A interseção WiiM/Denon adicionaria, entre outros, o **bit 26 (MFi)**. Na RC7, a máscara conjunta levou a `POST /auth-setup`, falha de conexão e nenhum stream. Sem implementação/autorização MFi, anunciar esse bit, o bit 51, modelo Apple ou identidade de fabricante alheio seria uma capacidade falsa; o laboratório **não oferece** esses perfis nem máscaras arbitrárias. O ícone pode depender de classificação/modelo além de `features`; o caso RC7 não isolou causalmente um único bit. O próximo desenvolvimento técnico legítimo é instrumentar a cadeia de classificação e identificar uma capacidade realmente implementável, ou um modelo TecnoHead verdadeiro, antes de qualquer novo anúncio ao iPhone. Não remover/reparear acessórios sem autorização específica.

Para repetir ensaios rapidamente no futuro, uma API interna do próprio App HAOS poderia aplicar perfis versionados na zona de teste e revertê-los automaticamente após prazo curto. **Reiniciar Shairport perde o bit 10 e a lista de controladores da implementação atual**; para comparar relay sem readopção a cada rodada seria preciso atualização de configuração em processo que preserve uma sessão legitimamente negociada, ou primeiro corrigir a persistência dos pareamentos. Esta interface Windows **não** faz isso: construir tal controle exige autenticação, limites de sessão, rollback e teste de não interferência com ARC/CEC. Nunca rodar múltiplos anúncios mutantes com a mesma identidade em paralelo, pois o cache/pareamento da Apple confundiria a atribuição do resultado.

### Ensaio v0.1.5 — classificação sem credencial alheia

Hipótese do usuário: o ícone diferente pode indicar que a classificação do
destino TecnoHead impede a UI de reprodução no Casa, mesmo quando o Lab recebe
Now Playing e obtém RTSP 2xx na conexão RC. O [mapeamento reverso de
`features`](https://emanuelecozzi.net/docs/airplay2/features/) atribui
`ThirdPartySpeaker` à condição `bit 26 || bit 51`, ambos relacionados a MFi;
não é uma especificação pública da Apple nem prova de que esse bit habilite o
cartão. A cópia da máscara WiiM/Denon na RC7 provocou `POST /auth-setup` e
falha de conexão. Portanto, esta rodada **não** afirma possuir MFi nem simula
certificados, fabricante comercial, chave, serial, pareamento ou HomePod.

O Lab 0.1.5 adiciona a opção `advertisement`, independente do perfil B0/M1:

| Valor | Alteração isolável no próprio Lab |
| --- | --- |
| `stock` | Anúncio original Shairport; controle. |
| `tecnohead_model` | `model=TecnoHead AirPlay Lab`, mantendo `features` originais. |
| `classic_bits` | Adiciona somente os bits 15–17, que o receptor sabe ler, mantendo o bit 50 e o modelo original. |
| `tecnohead_model_classic_bits` | Combina as duas mudanças, ainda sem MFi. |

O mesmo `config.airplay_features` alimenta o TXT mDNS, `fex` e `GET /info`; o
modelo próprio alimenta TXT e `GET /info`. Nada altera o ID persistente, a
saída de áudio descartada, Cozinha/Piscina, ou o código do relay. As variantes
de bits clássicos **não prometem** que o iPhone entregue metadados clássicos e
plist simultaneamente; bit 50 pode prevalecer. Para distinguir classificação
de funcionalidade, anotar separadamente (1) visibilidade e ícone no seletor,
(2) conexão AirPlay e chegada de metadados, (3) RC/ACK, (4) capa/botões no
mesmo cartão Casa. Igualdade de ícone, se ocorrer, não homologa D16–D19.

Ordem após build e atualização **somente do Lab**, sempre com uma instância e
uma identidade: confirmar `B0/stock`; testar `M1/tecnohead_model` e depois
`M1/tecnohead_model_classic_bits`, com readopção **somente do Lab** quando
necessária pelo estado volátil do Shairport. Se o primeiro já mudar o ícone,
isolar `M1/classic_bits` antes de atribuir causa. Parar se AirPlay falhar;
voltar a `B0/stock` e confirmar `lab_ready` no log. Não promover a produção ou
uma release estável sem teste físico positivo. O resultado de campo da variante
combinada está registrado abaixo.

Resultado de campo v0.1.5 (20/10/2026): o Supervisor atualizou **somente o
Lab** para 0.1.5, com backup da versão anterior, e confirmou `lab_ready` no
perfil `M1` com anúncio `tecnohead_model_classic_bits`. O App principal
permaneceu parado. O iPhone conectou ao Lab e enviou Now Playing e comandos
suportados; o log saneado marcou presença de título, artista, álbum, capa,
duração e posição. O ícone no seletor continuou o alto-falante genérico,
diferente de WiiM/Denon. O cartão do próprio Lab no Casa mostrou “Controles
não disponíveis”. Antes da readopção, o canal RC tinha gate `15`, sem o bit
de acesso Casa, e **não** houve envio MediaRemote; esta observação isolada
testa o anúncio, não o relay.

Com a música ainda direcionada ao Lab, o usuário removeu **somente** esse
acessório do Casa; o AirPlay permaneceu conectado. Ao readicioná-lo, o gate
RC chegou a `31`, snapshots de SupportedCommands e Now Playing estavam
disponíveis, e o peer retornou RTSP **2xx** para ambos os envios. Ainda assim,
após abrir novamente o mesmo cartão, o usuário confirmou que os controles
continuaram indisponíveis. O teste combinado **não** habilitou o ícone nem a
UI. Os ACKs comprovam transporte/resposta, não identidade do peer, aceitação
semântica do payload ou bloqueio geral da Apple. Os bits MFi 26/51 não foram
anunciados; nenhum modelo/certificado comercial foi simulado. Esta conclusão
se restringe ao Lab e a esta combinação. Não houve teste físico das zonas
reais nesta rodada.

Ao encerrar o ensaio, o Supervisor confirmou `lab_stopped` do processo M1,
seguido de `lab_ready` no perfil `B0` com anúncio `stock` e relay desligado.
O Lab foi então **parado** na aba Info. Nenhuma release estável ou alteração
do App principal foi publicada nesta etapa; o acessório Lab pode aparecer
temporariamente indisponível no Casa enquanto o App de ensaio estiver parado.

### Ensaio de captura pelo hotspot Windows — comparador WiiM

Em 20/10/2026, o usuário conectou **iPhone e WiiM Amp** ao hotspot Wi-Fi
temporário da estação Windows. O próprio WiiM continuou visível no AirPlay;
o usuário confirmou som, capa e controles funcionais no seu cartão Casa,
incluindo a ação de pausa/retomada solicitada. Isso o valida como controle
positivo **nesse arranjo de rede**, não demonstra que todo o fluxo passa pela
pilha de captura do Windows.

O adaptador USB Realtek RTL8188FTV suporta Wi-Fi Direct GO, mas reporta
`Network monitor mode: unsupported`. Uma coleta local com PktMon, filtro
exclusivo para o par iPhone–WiiM, `--comp nics`, truncamento em 128 bytes,
limite circular de 8 MiB e encerramento automático após 90 s gerou 3.689
eventos sem perda indicada. O texto abreviado expôs principalmente UDP
319/320 (sincronização PTP) e duas aparições de mDNS; **não expôs TCP/RTSP**.
Como o ponto de captura pode não ver encaminhamento entre clientes do hotspot,
isso **não comprova ausência de RTSP/MediaRemote na rede**. A captura bruta
permanece somente em diretório temporário local, fora do repositório; este
registro não contém IP, MAC, SSID, áudio, faixa ou payload de usuário.

O Lab foi iniciado apenas em `B0/stock` e confirmou `lab_ready`; no iPhone
ainda no hotspot, o usuário informou que ele **não apareceu** no seletor
AirPlay. Lab/HAOS permaneceram na rede doméstica original, e a falta de
descoberta é compatível com a separação entre redes, mas a causa exata não foi
isolada. **Não houve sessão nem captura comparável do Lab** nesse hotspot.
O Lab foi parado novamente, verificado na aba Info; o App principal e as
zonas Cozinha/Piscina não foram alterados. Próximo ponto de captura útil:
AP UniFi ou espelhamento de porta TP-Link no caminho da rede original, após
confirmar topologia/modelos. Não interpretar este ensaio como D16–D19 do Lab.

### Preparação do espelhamento físico — comparação WiiM/Lab

Em 20/10/2026, o usuário identificou o TL-SG1016PE e confirmou a topologia:
UniFi na porta 1, WiiM na porta 2, HAOS na porta 10 e estação de captura na
porta 15. iPhone e WiiM voltaram à rede UniFi original. O switch mostrou
`Port Mirror=Enable`, destino `Port 15` e somente `Port 1` com ingress/egress
habilitados; as demais portas-fonte continuam desabilitadas. Por decisão
explícita do usuário, **manter esse espelhamento após o ensaio**, sem rollback
automático. A estação mantém a Ethernet como rota de gerenciamento e captura;
o Wi-Fi ficou com endereço APIPA, sem rota IPv4 doméstica. A configuração no
switch por si só não comprova
que a placa de rede capture quadros unicast de terceiros: isso exige teste
com Npcap/Wireshark e uma sessão real.

O instalador oficial Wireshark 4.6.9 x64 foi baixado localmente, teve hash
SHA-256 e assinatura Authenticode conferidos. O usuário concluiu o assistente
Npcap 1.88; `dumpcap -D` lista `Ethernet 2`, e `tshark -v` confirma 4.6.9.
Uma captura de visibilidade de 12 s na Ethernet, limitada a ARP/mDNS e ao
comparador, recebeu 133 quadros sem perda, todos com origem/destino MAC
distintos da placa Ethernet local: 108 ARP e 25 mDNS. Isso confirma o espelho
para broadcast/multicast, **não ainda para a sessão unicast do iPhone**. O
endereço do WiiM mudou após voltar do hotspot; a primeira sonda direcionada
ao endereço antigo não é interpretável. As sondas seguintes com índice `3`
também foram inválidas: adaptadores virtuais do Windows mudaram a numeração
de `dumpcap -D`, e o índice passou a indicar outra interface. A captura foi
fixada pelo identificador NPF da Ethernet, não por número. Com ela, uma sonda
ICMP de 8 s recebeu 38 quadros sem perda, dos quais 32 trafegavam entre
terceiros, comprovando que o espelho entrega também unicast. Até este ponto,
não houve captura comparável de uma
sessão AirPlay WiiM/Lab nem nova conclusão sobre MediaRemote. Próximo passo:
captura curta do comparador WiiM com sessão
Apple Music e controles funcionais no próprio cartão Casa; captura equivalente
do Lab no mesmo iPhone/rede e perfil conhecido; comparar mDNS, RTSP, conexão
Remote Control Only, portas e sequência de eventos. Guardar PCAPs apenas em
área privada local e publicar somente agregados sanitizados. O Lab permanece
parado; nenhuma mudança de `features`, identidade ou App de produção ocorreu.

### Comparação física Wireshark: WiiM funcional versus Lab B0/stock

Na mesma rede UniFi e com o mesmo iPhone, o usuário confirmou Apple Music,
som e pausa/retomada **no próprio cartão Casa do WiiM**. Em seguida, com
`TecnoHead AirPlay Lab` v0.1.5 em `B0/stock`, informou novamente
**“Controles não disponíveis”** no cartão do próprio Lab. Este último descarta
PCM por projeto. O App de produção não foi iniciado nem modificado.

Para observar as duas direções dos fluxos cabeados, o TL-SG1016PE ficou com
espelhamento habilitado das portas 1 (UniFi), 2 (WiiM) e 10 (HAOS), ingress e
egress, para a porta 15 (estação Windows). A tabela do switch confirmou as
três fontes habilitadas; **o espelhamento foi mantido ativo a pedido do
usuário**. `dumpcap`/`tshark` do Wireshark 4.6.9 usaram o identificador NPF
estável da interface Ethernet, não seu índice variável. As capturas completas
estão somente no diretório privado local `TecnoHeadMediaRemoteCaptures`, fora
do repositório:

| Sessão | Captura | Duração | Quadros | Observação física |
|---|---|---:|---:|---|
| WiiM | `wiim-port2-session-2026-10-20.pcapng` | 120 s | 10.776 | Casa exibiu controles; pausa/retomada funcionou |
| Lab | `lab-port10-session-2026-10-20.pcapng` | 150 s | 28.989 | Casa continuou sem controles |

A captura WiiM terminou com 0 perdas reportadas pela interface. A captura
Lab foi encerrada manualmente após o resultado visual; seu arquivo é legível,
mas não há estatística confiável de perdas reportadas nesse encerramento. As
fontes espelhadas podem duplicar quadros, e o filtro Lab incluiu tráfego de
fundo do HAOS; **contagens brutas não são comparação de desempenho**. O mesmo
MAC de origem do controlador aparece nas sessões AirPlay dos dois receptores,
sem ser divulgado neste relatório.

| Indicador observado | WiiM | Lab B0/stock |
|---|---|---|
| DNS-SD `_airplay._tcp` | A e AAAA | A, sem AAAA na janela |
| Família da sessão de controle e do fluxo TCP de mídia | IPv6 | IPv4 |
| Porta anunciada de controle | 7000 | 7100 |
| `features` anunciado | `0x445F8A00,0x1C340` | `0x401C4A00,0x5C340` |
| `flags` anunciado | `0x4` | `0x4` |
| Modelo próprio anunciado | `WiiM Amp` | `ShairportSync` |

O Wireshark identificou no início de ambas as sessões `GET /info` e
`POST /pair-setup`, mas **não decodificou o conteúdo protegido após o
pareamento**. Logo, estes PCAPs não demonstram se o home hub recebeu
`updateMRNowPlayingInfo`, quais capacidades ele aceitou ou por que habilitou
a UI do WiiM. O Lab B0 não faz relay RC por projeto; seus logs saneados,
contudo, registraram recepção de Now Playing e SupportedCommands da origem,
com presença de título, artista, álbum, capa, duração e posição. A ausência
de botões no Casa não é ausência de metadados no backend.

A diferença IPv4/IPv6 é **hipótese de ensaio, não causa comprovada**. Ela pode
ser isolada em uma variante reversível e exclusivamente do Lab que mantenha
nome, identidade, `features`, `flags` e perfil de metadata iguais a B0, mas
permita anúncio/escuta IPv6 legítimos. Primeiro confirmar por DNS-SD que a
variante publica AAAA e por captura que o mesmo iPhone escolhe IPv6; só então
comparar o cartão Casa. Não repetir a máscara comercial: o ensaio RC7 já
provocou falha de conexão e incluiu capacidade MFi não implementada. Não
inferir necessidade de IPv6, MFi ou classificação Apple a partir desta única
comparação. O Lab foi parado após a captura, verificado no Supervisor; a
configuração ficou em `B0/stock`.

### Variante experimental v0.1.6 — IPv6 confirmado, cartão ainda vazio

A inspeção do código mostrou dois bloqueios explícitos de IPv6 **somente no
Lab** v0.1.5: `address` liga o listener Shairport a IPv4, e o Avahi privado
usa `use-ipv6=no`/`publish-aaaa-on-ipv4=no`. O [arquivo de configuração
oficial do Shairport Sync](https://github.com/mikebrady/shairport-sync/blob/master/scripts/shairport-sync.conf)
documenta que omitir `address` permite escuta nos endereços locais; o
[manual do Avahi](https://manpages.debian.org/unstable/avahi-daemon/avahi-daemon.conf.5.en.html)
define as opções de anúncio IPv6/AAAA. A própria captura mostrou tráfego
IPv6 no host HAOS, mas isso não prova que a instância Lab consiga usá-lo.

Foi preparada para publicação isolada na branch experimental, sem alteração
da imagem ou do App de produção, a opção `network_mode=ipv4_only|dual_stack`
para o App Lab.
O padrão `ipv4_only` reproduz a configuração v0.1.5; `dual_stack` omite o
vínculo Shairport a um IP único e habilita IPv6 e AAAA no Avahi privado. O
mesmo nome, ID persistente, porta 7100, perfil B0/stock, `features`, `flags`,
metadata, saída descartada e ausência de relay RC permanecem. Testes locais:
37 testes do Lab e 4 do utilitário de ensaio passaram; Ruff e
`git diff --check` sem erros.

Antes de considerar essa hipótese, instalar apenas uma pré-release do Lab
com backup/rollback, confirmar `AAAA` para o próprio Lab e conexão IPv6
efetiva no PCAP, e só então pedir observação do cartão Casa com Apple Music.
Se IPv6 não for anunciado ou a conexão falhar, retornar a `ipv4_only` sem
inferir qualquer conclusão sobre classificação Apple. Nenhum App de produção
deve receber esta mudança experimental.

Resultado físico (20/10/2026): o commit `07889b1` foi publicado somente na
branch `codex/airplay-lab`, com [pré-release experimental de código-fonte
`lab-v0.1.6`](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/lab-v0.1.6).
Todos os jobs da [CI `39521826826`](https://github.com/aoliveira07/tecnohead-multimidia/actions/runs/39521826826)
passaram, incluindo o build amd64/arm64 do Lab. O Supervisor atualizou
**somente o Lab** de 0.1.5 para 0.1.6, com a opção de guardar backup da
versão 0.1.5 habilitada. O App principal permaneceu parado e não recebeu
imagem, atualização ou release. Em `B0/stock/dual_stack`, o log do Lab marcou
`lab_ready`, mantendo relay RC desligado.

Com espelhamento ainda ativo das portas 1/2/10 para a 15, uma captura
filtrada em mDNS e TCP/7100 registrou 927 quadros em 112 s. Ela permanece
somente no diretório privado local, com SHA-256
`FE1236970DD7CAB2D3E428C41544EAFB929FED591B8CC3137A69A0A48EC3A129`;
não há PCAP, IP, MAC, faixa, arte ou áudio anexado à release. O DNS-SD do
Lab publicou AAAA (8 respostas capturadas); houve um SYN IPv6 do controlador
para a porta 7100 exatamente no endereço AAAA anunciado e 514 quadros
IPv6 nessa porta, sem quadros IPv4 de controle na janela. O usuário confirmou
que o AirPlay conectou, mas o cartão do **mesmo Lab** no app Casa continuou
“Controles não disponíveis”. Contadores finais do Lab: 2 Now Playing,
4 SupportedCommands, campos de álbum/artista/capa/duração/posição/título
presentes; nenhum relay RC era esperado no perfil B0.

Conclusão restrita: **a ausência de IPv6, isoladamente, não explica a tela
vazia nesta sessão**. O teste não identifica o critério Apple, não valida
framing MediaRemote após pareamento e não refuta a necessidade de outros
mecanismos. O Lab foi parado e a opção `ipv4_only` restaurada e verificada
após recarregar a interface; `B0/stock`, arranque automático, watchdog e
atualização automática continuam desativados. O espelhamento do switch foi
mantido ativo, conforme pedido do usuário. Cozinha/Piscina, WiiM e Denon não
foram alterados nem retestados nesta rodada.

### Ensaio combinado v0.1.6 — IPv6, anúncio próprio e relay RC

Depois do ensaio isolado acima, a pedido do usuário o mesmo Lab 0.1.6 foi
reativado em `M1/tecnohead_model_classic_bits/dual_stack`. **Este é o estado
mais recente: o Lab permanece em execução nesse perfil experimental**; o
parágrafo anterior descreve apenas a reversão intermediária de B0. Arranque
automático, watchdog e atualização automática seguem desligados. O App
principal continua parado, sem modificação de Cozinha/Piscina. O espelhamento
das portas 1/2/10 para a 15 continua ativo, por solicitação do usuário; não
há captura em andamento.

O anúncio observado usou modelo próprio `TecnoHead AirPlay Lab` e
`features=0x401FCA00,0x5C340`, contra `0x401C4A00,0x5C340` em B0/stock.
Foram acrescentados somente os bits 15–17 de metadados que o receptor
processa; bits 26/51 associados à classe de speaker de terceiro/MFi não
foram anunciados. O Lab publicou AAAA e a captura registrou 671 quadros
IPv6 em TCP/7100, zero IPv4 nessa porta, durante a primeira janela combinada.
O usuário confirmou AirPlay conectado e música direcionada ao Lab, mas o
cartão do próprio Lab no Casa permaneceu sem controles.

Com a faixa ainda tocando, o usuário removeu e readicionou **somente o Lab**.
O AirPlay permaneceu conectado, porém o cartão continuou “Controles não
disponíveis”. Os logs sanitizados desse segundo ensaio registraram 6
`updateMRNowPlayingInfo`, 5 `updateMRSupportedCommands`, presença dos campos
álbum/artista/capa/duração/posição/título, dois SETUP RC, dois event ports,
um gate RC `31`, um snapshot de comandos, um de Now Playing e uma resposta
RTSP 2xx para cada envio. As duas conexões RC receberam TEARDOWN. A captura
da readopção registrou 897 quadros IPv6 em TCP/7100 e zero IPv4. Essas
respostas comprovam transporte RTSP, **não** que a central interpretou os
payloads ou habilitou a interface.

Os PCAPs brutos permanecem somente no armazenamento privado da estação,
sem publicação. SHA-256 da primeira janela combinada:
`254B1A9E8BCB935D9C1BF406C360AA1381120AD0121B984D8BFED2C9F645FDE5`
(2169 quadros/120 s). SHA-256 da readopção:
`BC2DA4A150810ACBD9841CE363E3AA3B0EF2034157BCDBAFBB99DBA877292B46`
(1566 quadros/93 s). Filtro das capturas: mDNS e TCP/7100. Nenhum endereço,
MAC, chave, faixa, capa ou payload foi incorporado ao repositório.

Conclusão: **IPv6 + modelo próprio + bits clássicos legítimos + relay RC +
readopção durante reprodução não bastaram** neste Lab. A diferença do ícone
em relação a WiiM/Denon continua sendo pista de classificação, não causa
demonstrada. No anúncio comercial, os únicos bits presentes no primeiro
bloco e ausentes deste Lab combinado são 22 (não documentado no upstream)
e 26 (categoria `ThirdPartySpeaker` em pesquisa de protocolo, associada ao
ecossistema MFi); o Lab tem também bits próprios diferentes. Não ativar
22/26/51 nem copiar modelo, identidade ou certificado comercial por tentativa
cega: a máscara comercial completa já causou falha de conexão na RC7.
O código Shairport fixado publica `model`, mas não `manufacturer` nem
`serialNumber` no TXT atual; esses campos **próprios e verdadeiros** são uma
hipótese futura separável, não uma capacidade Home comprovada. Ainda não há
prova suficiente para declarar bloqueio universal da Apple ou D16–D19
aprovados nas zonas reais.

### Ensaio proposto v0.1.7 — campos TXT independentes

O Lab ganhou uma opção `txt_variant` para variar somente os campos do
anúncio `_airplay._tcp` e da resposta `GET /info`, mantendo independentes
`profile`, `advertisement` e `network_mode`. As alternativas são `stock`
(controle), `own_manufacturer`, `own_manufacturer_serial`,
`required_sender_zero` (`rsf=0x0`) e `without_fex`. O fabricante e o serial
são próprios do Lab; nenhuma variante usa identidade comercial, certificado
ou bit MFi. O serial é estável enquanto o ID local do Lab persistir.

Hipótese: um desses campos pode influenciar a classificação do acessório
sem romper a sessão. Isto **não foi demonstrado**. A ordem do teste será:
confirmar conexão em `stock`, mudar uma única variante, confirmar conexão
AirPlay, observar ícone e cartão Casa com a mesma fonte musical e voltar a
`stock` se a conexão falhar. Ícone semelhante, metadados no backend ou ACK
RTSP não contam como D16–D19: é necessária capa/faixa visível e ação real
dos botões no **mesmo acessório**. A versão 0.1.7 foi compilada e instalada
apenas no Lab; esta nota não declara aprovação no Casa.

Certificado autoassinado é tecnicamente possível como identidade própria,
mas não substitui uma credencial MFi. A [documentação de segurança da
Apple](https://support.apple.com/guide/security/verifying-accessories-sec70a4f377d/web)
descreve certificado fornecido pela Apple e autenticação por componente
dedicado; o [programa MFi](https://mfi.apple.com/en/how-it-works) inclui
AirPlay audio, componentes e certificação. Não está demonstrado que a falta
de MFi seja *a* causa deste cartão vazio; por isso o Lab não simulará esse
status nem usará certificado de outro dispositivo.

### Execução física v0.1.7 — variantes iniciais

A pré-release `lab-v0.1.7` passou pela CI (49 testes Python, lint e builds
amd64/arm64) e foi instalada **somente no AirPlay Lab**, com backup da versão
anterior. O App TecnoHead Multimídia de produção permaneceu parado. O Lab
conservou `M1/tecnohead_model_classic_bits/dual_stack`; o TXT `stock` após a
atualização conectou no AirPlay, mas o cartão Casa continuou sem controles.

Mudando **somente** `txt_variant=own_manufacturer`, o log confirmou `lab_ready`
na nova opção. O usuário confirmou conexão AirPlay, ícone inalterado e
“Controles não disponíveis” no próprio cartão. Durante a sessão, os contadores
do Lab registraram metadados e comandos da fonte. Isto demonstra recepção no
Lab, **não** entrega ao Casa nem interpretação pelo hub.

Mudando **somente** para `own_manufacturer_serial`, o log confirmou `lab_ready`
na nova opção. O usuário voltou a confirmar conexão AirPlay, ícone inalterado
e Casa sem controles. Na variante seguinte, `required_sender_zero`, o log
também confirmou `lab_ready` e o usuário confirmou conexão normal, ícone
inalterado e Casa sem controles. Em `without_fex`, o log confirmou `lab_ready`
e o usuário novamente confirmou conexão normal, ícone inalterado e Casa sem
controles. Nenhuma das quatro variações isoladas passou D16–D19.

Ao final, somente `txt_variant` voltou a `stock`; a interface confirmou o
Lab 0.1.7 em execução e o log confirmou
`M1/tecnohead_model_classic_bits/dual_stack/stock`. Nenhum acessório real ou
App de produção foi modificado durante esta matriz. Esses resultados não
provam que uma credencial Apple seja necessária para a interface: apenas
descartam esses campos TXT isolados nas condições testadas. O próximo passo
de engenharia é delimitar com evidência a classificação/capacidades aceitas
pelo Casa, sem imitar identidade ou credenciais comerciais.

### Auditoria da negociação real dos endpoints — capturas privadas de 20/10/2026

As capturas já existentes do WiiM funcional e do Lab B0 foram relidas sem
exportar áudio, arte, endereços, identificadores ou payloads. Em ambos, o
mesmo iPhone fez `GET /info` (requisição de 227 bytes) seguido das duas
etapas `POST /pair-setup` (288 e 738 bytes); as três respostas foram RTSP
`200`. O Lab repetiu o último `POST` com o mesmo número de sequência TCP,
o que não constitui uma terceira etapa distinta. Isto comprova que a
descoberta e o início do pareamento de áudio funcionaram nos dois casos;
não comprova a negociação necessária para habilitar a interface do Casa.

O `GET /info` **daquelas sessões físicas** trouxe `statusFlags=0x4` nos dois
receptores. Logo, a presença do bit `0x400` nessa resposta específica não
separou o WiiM funcional do Lab vazio. A estrutura da resposta, porém, foi
distinta: WiiM incluiu `sourceVersion`, `manufacturer`, `sdk`, `OSInfo`,
`PTPInfo` e informações de firmware, e não incluiu `playbackCapabilities`;
Lab não incluiu aqueles campos e trouxe
`playbackCapabilities.supportsUIForAudioOnlyContent=false`. No ensaio
posterior `M1/tecnohead_model_classic_bits/dual_stack`, a resposta do Lab
continuou com esse campo `false` e sem os campos superiores citados,
apesar de `features` ter mudado. Trata-se de **diferenças observadas, não
da causa comprovada** do ícone ou do cartão.

No [Shairport Sync fixado em `cf6998d`](https://github.com/mikebrady/shairport-sync/blob/cf6998d/rtsp.c),
`generateInfoPlist()` parte de um
[modelo estático](https://github.com/mikebrady/shairport-sync/blob/cf6998d/plists/get_info_response.xml)
e sobrepõe identidade, `features` e `statusFlags`. Portanto as variações
de TXT já testadas não isolaram o efeito desse bloco estático de `/info`.
Seu significado para o cartão Casa precisa ser verificado antes de
qualquer alteração; não definir `true` sem implementar a capacidade real.

A [discussão #2262](https://github.com/mikebrady/shairport-sync/discussions/2262)
comprovou outro pedaço do protocolo: comandos **do receptor para o iPhone
emissor** pela porta de eventos da sessão de áudio/PTP, não pelo canal
`remote_control_stream`. O código fixado já contém o envio
`sendMediaRemoteCommand` em
[`remote/remote.c`](https://github.com/mikebrady/shairport-sync/blob/cf6998d/remote/remote.c),
e o release 5.6 o anuncia como Remote Control para AirPlay 2. Isso não
explica por si só **como o app Casa cria os botões, chega ao endpoint e
entrega um comando recebido**. O relay experimental RC do Lab também não
habilitou o cartão. Após o pareamento, a captura de rede não decodifica
o conteúdo cifrado: ACK, conexão TCP ou presença de metadados no backend
não devem ser registrados como controles nativos aprovados.

Próxima investigação restrita ao mesmo endpoint: mapear por sessão e
papel (emissor versus controlador Casa/hub) as solicitações RC recebidas
e a resposta `/info`, sem conteúdo pessoal; comparar o anúncio e a
resposta de capacidades do WiiM/Denon com o Lab; isolar **um** campo
honesto por variante somente no Lab, com rollback, antes de pedir novo
teste visual. Não há alteração de firmware, produção ou publicação nesta
auditoria.
