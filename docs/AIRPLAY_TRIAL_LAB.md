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
