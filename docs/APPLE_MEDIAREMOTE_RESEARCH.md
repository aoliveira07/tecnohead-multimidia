# Apple MediaRemote no próprio destino AirPlay 2 — pesquisa v1.3.2

Estado em 19/10/2026: **parcial, com RC4 diagnóstica instalada e retestada fisicamente; controles nativos do Casa ainda indisponíveis**. Este documento é a trilha de evidência do handoff v1.3.2. Não há segundo `media_player`, Receiver, tile HomeKit ou mudança de identidade Apple nesta investigação.

## Inventário e rollback

- Repositório: `https://github.com/aoliveira07/tecnohead-multimidia`.
- Base estável publicada: tag `v1.4.16`, commit `7c391d665ca9889debf800d33d25e536215ccbe5`. O commit de pesquisa anterior é `3eebe82caece7cf75f15f37b6b30f2aef25b46cc` em `main`.
- Ensaio iniciado no branch `experiment/mediaremote-now-playing`, incorporado pela [PR #1](https://github.com/aoliveira07/tecnohead-multimidia/pull/1). Imagens de diagnóstico: [RC1](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.1) (`9846f52`) e [RC2](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.2) (`67422d0`); esta última protege os logs de acesso ([PR #2](https://github.com/aoliveira07/tecnohead-multimidia/pull/2)). Retorno de código: tag `v1.4.16`; isso **não** substitui backup de `/data` e das identidades/pairings da instalação HAOS.
- A sessão autenticada do HAOS confirmou **App v1.4.16 em execução** no painel de Apps e no próprio Ingress. O diagnóstico do App mostra Shairport `cf6998d-AirPlay2-smi11-OpenSSL-Avahi-ALSA-stdout-pipe-metadata-dbus-mpris` e NQPTP `1.2.9`, `smi11`, ambos em execução, com endpoints Cozinha/Piscina publicados. Core e Supervisor: `2026.10.2`; HAOS: `18.3`. Essa verificação é de runtime, não de controles no Casa. Não copiar URL/IP/identidade do cliente ao repositório.
- Dockerfile do código-fonte fixa Shairport Sync `cf6998daa1876c5a8f97128a960c8afc0e731841`, 7 commits após a tag 5.6, sem arquivos C alterados nessa diferença; compila `--with-airplay-2 --with-dbus-interface --with-mpris-interface --with-metadata --with-metadata-pipe`. NQPTP fixa `ab8fb67483411640fd7f1e193889482f2421c37c`, o commit da tag 1.2.9. A compatibilidade `smi11` **foi confirmada nos binários em execução** pelo diagnóstico do App.
- Duas instâncias Shairport, D-Bus de sessão separado por zona, um NQPTP, Avahi e saída PCM→LinkPlay permanecem inalterados no branch. O leitor de metadados anterior só tratava `ssnc/pvol` para volume. O painel em execução confirmou um player canônico por zona, limite de volume 100% configurado em ambas e política HDMI ARC da Piscina. Os IDs específicos do cliente ficam fora do repositório. Nenhum comando físico foi enviado nesta inspeção.
- Baseline do iPhone em 19/10/2026, 19:18: Apple Music exibiu reprodução roteada para TecnoHead Piscina; no mesmo momento, o cartão do acessório TecnoHead Piscina no Casa mostrou “Controles não disponíveis”, sem faixa, capa ou controles ativos. Capturas privadas fornecidas pelo usuário permanecem na conversa, não no GitHub. Não houve confirmação de som audível nessa mensagem. A Cozinha já tinha captura anterior do mesmo sintoma. Isso conclui D02 e documenta falha basal de D17–D19 **na v1.4.16**, não prova bloqueio definitivo da plataforma nem resultado da POC.

## Evidência e classificação

| Nível | Observação | O que ela **não** prova |
| --- | --- | --- |
| Upstream implementado | [Release Shairport Sync 5.6](https://github.com/mikebrady/shairport-sync/releases/tag/5.6): comandos AirPlay 2 para o emissor, `NowPlayingInformation` e `CommandInformation` em D-Bus; `RemoteControl.Available` pode ser `false` apesar de comandos ativos. | Que o app Casa exponha controles no cartão do acessório. |
| Documentação Apple | A [Apple orienta selecionar vários destinos AirPlay 2 no iPhone](https://support.apple.com/en-ie/guide/iphone/iph315e0d58d/ios) e descreve [controle de mídia no app Casa para HomePod](https://support.apple.com/content/dam/edam/applecare/images/en_US/otherassets/accessibility/vpat_homepod.pdf). | Não há, nesses textos, promessa de cartão de mídia idêntico para todo receptor AirPlay 2 de terceiros. Esta última frase é inferência da diferença de escopo, não regra técnica publicada. |
| Código do App | O Shairport fixado já é posterior a 5.6; o pipe recebe `ssnc/copl`. A sonda opcional deste branch observa somente presença de campos/comandos do emissor, sem guardar seus valores. | Que o hub recebeu Now Playing, ou que a Apple habilitou a UI. |
| Experimento comunitário | [Issue #2182](https://github.com/mikebrady/shairport-sync/issues/2182): um build **modificado** encaminhou Now Playing/artwork por Remote Control Only; o hub respondeu, mas o cartão Casa continuou vazio. O autor corrigiu explicitamente a alegação inicial: o build stock não faz esse encaminhamento. | Resultado na instalação TecnoHead ou especificação oficial Apple. |
| Engenharia reversa, hipótese | A #2182 e um [pseudocódigo de MediaRemote](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/90aa0cfe59d9682b4265e1354c8b19ec3c7823ab/System/Library/PrivateFrameworks/MediaRemote.framework/MediaRemote/MRAVConcreteOutputDevice.mm) associam o cartão a `isAddedToHomeKit`/`isRemoteControllable` e classificação do dispositivo. Um ensaio de identificação como HomePod foi rejeitado pelo iPhone/hub. | Que não exista **nenhuma** implementação legítima para terceiros; a fonte não é API pública Apple. |
| Canal de comandos | A [discussão #2262](https://github.com/mikebrady/shairport-sync/discussions/2262) demonstrou `sendMediaRemoteCommand` na sessão de áudio/PTP; Remote Control Only usa outro mecanismo. | Que esses comandos possam ser enviados como plist ao canal RC ou acionados pelo Casa. |

## Código de diagnóstico da pré-release

O [commit experimental `7d889d5`](https://github.com/aoliveira07/tecnohead-multimidia/commit/7d889d55e1835146064bf4bf2f5ad8dbcd456f4d) adiciona `APPLE_MEDIAREMOTE_EXPERIMENTAL`, `false` por padrão. Um ajuste posterior disponibiliza a mesma flag na aba **Configuração** do App HAOS, validada como booleano pelo Supervisor e lida de `/data/options.json` no início do processo, conforme a [documentação oficial de opções de Apps](https://contributors.home-assistant.io/apps/guides/options/). A ativação no ensaio foi feita após backup e reinício acompanhado. Quando explicitamente habilitado, `MediaRemoteProbe` interpreta até 1 MiB de `ssnc/copl` por zona e publica **somente** contagens, existência de título/artista/álbum/capa/duração/posição, códigos de comandos habilitados e horários no diagnóstico do App. Nunca guarda título, artista, imagem, identificador ou plist bruto. O relatório rotula a origem como `sender_to_receiver_only` e o cartão Casa como `not_observed`.

O leitor do pipe agora ignora itens declarados acima de 2 MiB e continua a ler o próximo item; um teste sintético verifica que um `copl` excessivo não faz perder o `pvol` subsequente. Outro teste injeta uma falha interna na sonda e confirma que o `pvol` ainda é encaminhado, sem registrar o payload. Isto evita interpretar um teste de arte grande como falha no volume. Não há `include_cover_art=yes`, retransmissão RC, alteração de anúncios mDNS, comandos a fontes, modificação de pairing ou mudança na saída de áudio. A sonda **não** é a correção da interface do Casa.

O [Supervisor aceita `#branch` na URL de um repositório](https://contributors.home-assistant.io/apps/guides/repository/), porém deriva daí **outra identidade de App**. Por isso, o ensaio foi publicado no mesmo repositório como pré-release, sem segundo App: `config.yaml` exige instalação manual com `breaking_versions`, a opção da sonda permanece `false` por padrão para outras instalações e o workflow não move a tag `latest` em RCs. O registro confirmou `1.4.17-rc.2` separada, enquanto `1.4.16` continua com `latest`.

## Implantação controlada e limite da prova

Com autorização do usuário, o HAOS atualizou o App existente para `1.4.17-rc.1` e depois `1.4.17-rc.2`, mantendo backup automático da versão anterior nas duas atualizações, além do backup manual pré-MediaRemote. A atualização automática do App foi desligada temporariamente para o ensaio. A opção `apple_mediaremote_experimental` foi ativada no HAOS e persistiu na RC2. Após reinício, o painel mostrou a RC2 online, duas zonas configuradas, os dois endpoints anunciados e NQPTP `smi11` compartilhado. Na primeira sessão acompanhada, o usuário informou **“Tocando”** para Cozinha; a API mostrou endpoint `streaming`, PCM recebido e reprodução HTTP solicitada ao LinkPlay. Os contadores de Now Playing, comandos e estado ficaram em zero **por defeito posterior identificado no leitor do pipe**; esses zeros não indicam ausência de metadados do emissor. A Piscina permaneceu `advertising`. Nada disso prova negociação Remote Control Only.

### Falha de enquadramento encontrada na RC2

O código fixado de Shairport Sync, em `metadata/pipe.c`, escreve Base64 e `</data></item>` **sem quebra de linha entre eles**. O leitor RC2 consumia a linha inteira como Base64, procurava depois outra linha começando em `</data>` e descartava o item ao chegar ao EOF. Os testes sintéticos haviam incluído uma quebra que o upstream não produz. Como o volume real pode seguir pelo hook e D-Bus, a reprodução e seu volume não expunham esse defeito. A correção [PR #3](https://github.com/aoliveira07/tecnohead-multimidia/pull/3) lê o comprimento Base64 exato em blocos limitados, confere o fechamento e conta apenas tipos de itens, sem conteúdo privado. CI aprovou testes, configuração e build multi-arquitetura. A [RC3](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.3) foi instalada no **mesmo App HAOS**, com backup da RC2. O Supervisor confirmou RC3 em funcionamento, flag diagnóstica ligada e ambos endpoints anunciados. Antes da nova reprodução, a sonda contou um item inicial do pipe em cada zona. Isso só corrige **observabilidade**, não a UI Casa. Referências: [fonte upstream do pipe](https://github.com/mikebrady/shairport-sync/blob/cf6998daa1876c5a8f97128a960c8afc0e731841/metadata/pipe.c) e [encaminhamento `copl` no RTSP](https://github.com/mikebrady/shairport-sync/blob/cf6998daa1876c5a8f97128a960c8afc0e731841/rtsp.c).

Na reprodução seguinte pelo Apple Music, a Cozinha entrou em `streaming` e a sonda contou 26 itens de pipe, incluindo seis `ssnc/copl`: três `updateMRNowPlayingInfo` e três `updateMRSupportedCommands`. Foram observados somente os **nomes** dos campos título, artista, álbum, capa, duração e posição; nenhum valor, imagem ou payload foi guardado/publicado. `invalid_updates=0`, `oversized_updates=0`. A Piscina permaneceu `advertising`, sem `copl` ou campos da Cozinha. O usuário confirmou **som audível**, mas informou **“Casa sem controles”** ao abrir o próprio acessório Cozinha. Isto aprova D06 e reprova D16/D18/D19 no reteste RC3.

Depois, com a Cozinha parada e somente TecnoHead Piscina selecionado no Apple Music, o usuário também confirmou **som audível; Casa sem controles**. A API mostrou Piscina `streaming`, 26 itens de pipe, cinco `ssnc/copl`, dois `updateMRNowPlayingInfo`, três `updateMRSupportedCommands`, os mesmos seis tipos de campos e nenhum item inválido ou excessivo; Cozinha estava `advertising`, sem metadados cruzados. Isto aprova D07 e reprova D17 no reteste RC3. Ambos os ensaios confirmam o fluxo emissor→receptor, **não** conexão RC, comando de retorno à fonte, entrega ao hub ou bloqueio definitivo da Apple.

### POC de observação RC4 — instalada; ambas as zonas testadas fisicamente

A [RC4](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.4) acrescenta ao **mesmo build pinado** um patch mínimo de diagnóstico em Shairport Sync: após preparar resposta `200` para `SETUP` Remote Control Only, após conexão no event port e após ACK de `updateInfo`, ele emite apenas três marcadores constantes no nível de log já usado (`1`). Não aumenta verbosidade, não inclui IP, nome do iPhone, chave, conteúdo musical, porta nem identificador. A sonda do App conta esses marcadores **por processo/zona**, não os copia ao log geral e só mostra contagens quando `apple_mediaremote_experimental=true`. O `updateInfo` continua sendo o mesmo chamado upstream; não há retransmissão Now Playing, mudança de mDNS/pairing, volume ou áudio. O patch foi conferido com `git apply --check` contra `cf6998d`; os testes unitários, CI e builds multi-arquitetura passaram. A RC4 foi instalada no mesmo App HAOS, com backup da versão anterior solicitado no Supervisor; o App voltou a `Em funcionamento` e ambos os destinos anunciaram normalmente.

Teste RC4 Cozinha, Apple Music/iPhone: o usuário confirmou **som audível** e que o cartão do mesmo acessório no Casa continuou **sem controles**. A consulta sanitizada à API do App após a abertura do Casa mostrou Cozinha em `streaming`, duas atualizações `updateMRNowPlayingInfo`, três `updateMRSupportedCommands` e contadores `Remote Control Only` `SETUP/event/ACK = 0/0/0`. Piscina estava `advertising`.

Teste RC4 Piscina, após parar a Cozinha: o usuário confirmou novamente **som audível; Casa sem controles**. A API mostrou Piscina em `streaming`, dez atualizações `updateMRNowPlayingInfo`, três `updateMRSupportedCommands`, sem atualizações inválidas ou excessivas, e `SETUP/event/ACK = 0/0/0`. Cozinha estava `advertising`. Assim, em ambos os ensaios os metadados chegaram ao receptor e nenhum marco RC foi **observado** quando o mesmo acessório Casa foi aberto. O usuário conferiu no app Casa que o HomePod constava como central **Conectado** e na mesma rede Wi‑Fi doméstica usada pelo iPhone (sem divulgar SSID); isso afasta a ausência de central ou uma rede de convidados diferente como explicação simples. Ainda não prova alcance TCP específico entre central e App — isolamento de clientes e regras de rede continuam possíveis — nem expõe os tokens de classificação Apple. A tela nativa segue não corrigida; não foi implementado encaminhamento Now Playing sem uma conexão RC legítima. O resultado é **PARCIAL**, não `RESOLVIDO` nem prova definitiva de bloqueio por plataforma.

Interpretação: `SETUP` e ACK positivos comprovarão apenas negociação/transporte daquela conexão no processo da zona. Não associam, por si, o hub ao emissor nem fazem a Apple renderizar o cartão. Ausência de RC durante um ensaio não prova requisito fechado da Apple sem repetir condições de rede/hub. A [#2182](https://github.com/mikebrady/shairport-sync/issues/2182) já descreve ACK de Now Playing em build **modificado** sem controles no Casa; portanto até uma POC posterior de encaminhamento precisaria de prova visual D16–D19 antes de ser considerada correção.

### Comparador positivo: WiiM Amp no mesmo ambiente

Às 21:07 de 19/10/2026, o usuário enviou captura privada do **próprio acessório WiiM Amp** no app Casa mostrando capa, título/artista, posição, play/pause, anterior/próxima e volume. O usuário confirmou que os controles aparecem no próprio Casa, não só no seletor AirPlay. A captura comprova a apresentação visual; ações físicas individuais dos botões do WiiM não foram medidas neste ensaio. Esse comparador impede concluir categoricamente que **todo** receptor AirPlay 2 de terceiro é excluído dessa interface. O WiiM é equipamento comercial com firmware próprio; não se pode atribuir o resultado a um único bit do anúncio, nem presumir que Shairport Sync implemente as mesmas negociações.

Uma consulta **somente de leitura** ao mDNS na LAN doméstica, sem tráfego de mídia, pareamento ou alteração de dispositivo, observou anúncios `_airplay._tcp` dos três destinos. Foram extraídos apenas campos de capacidade sem IP, MAC, serial, chave pública, identificador de pareamento ou conteúdo musical:

| Destino | `features` anunciado | `flags` anunciado | `model` anunciado |
| --- | --- | --- | --- |
| TecnoHead Cozinha e Piscina | `0x401C4A00,0x5C340` | `0x4` | `ShairportSync` |
| WiiM Amp | `0x445F8A00,0x1C340` | `0xc04` | `WiiM Amp` |

As duas partes de `features` seguem a ordem baixa,alta usada no anúncio. O XOR marca diferenças nos bits **14, 15, 16, 17, 22, 26 e 50**; `flags` difere nos bits **10 e 11**. O [código Shairport fixado](https://github.com/mikebrady/shairport-sync/blob/cf6998daa1876c5a8f97128a960c8afc0e731841/shairport.c) documenta o bit 50 como pedido de metadados AirPlay 2 em plist, e o [tratamento de `POST /configure`](https://github.com/mikebrady/shairport-sync/blob/cf6998daa1876c5a8f97128a960c8afc0e731841/rtsp.c) marca o bit 10 quando recebe `Enable_HK_Access_Control`. O WiiM anuncia esse bit; os TecnoHead, embora adicionados ao Casa, **não o anunciavam no instante da consulta**. No código Shairport inspecionado, `enable_HK_Access_Control` é alterado no tratamento de `/configure` e não foi encontrado mecanismo de persistência desse booleano entre reinícios. É uma hipótese concreta de estado perdido ou de negociação diferente, **não** prova de causalidade: não há registro de `/configure` da adoção original e ainda não se observou a classificação interna do iPhone/hub. O bit 11 e os demais bits de `features` tampouco autorizam copiar capacidades de outro produto sem implementá-las.

Na amostra curta de mDNS, não houve resposta `_hap._tcp`; isso **não demonstra ausência definitiva** de HAP, certificação, pareamento ou outro canal proprietário do WiiM. A documentação do fabricante [inclui oficialmente o WiiM Amp como acessório Apple Home](https://faq.wiimhome.com/en/support/solutions/articles/72000548874-how-to-add-a-wiim-device-to-the-apple-home-app-as-an-accessory). O fato de ele aparecer também sob uma integração chamada Apple TV no Home Assistant não o transforma em Apple TV e não explica, por si, o cartão Casa.

### Readopção controlada da Cozinha: bit 10 e canal RC não bastam

Após o baseline, o usuário **autorizou expressamente** remover e readicionar somente `TecnoHead Cozinha` no app Casa. Piscina, WiiM, `Cozinha Room`, App HAOS e identidade AirPlay não foram alterados. Em 19/10/2026, aproximadamente 21:19–21:24 (America/Sao_Paulo):

1. Antes e após a remoção do acessório Casa, o anúncio `_airplay._tcp` da Cozinha permaneceu em `flags=0x4`; Piscina também `0x4`.
2. O usuário readicionou o **mesmo** TecnoHead Cozinha sem mudar ajustes globais. A captura mDNS somente de leitura passou a mostrar `flags=0x404` na Cozinha; Piscina permaneceu `0x4`. O log local do Shairport mostrou `POST /configure` nessa janela. Nenhum trecho de log, nome de telefone, IP, chave ou identificador foi publicado.
3. A sonda RC4 do processo Cozinha contou `SETUP/event/updateInfo ACK = 2/2/2` após a readopção, contra `0/0/0` no ensaio anterior. O ACK é do **`updateInfo` stock**, não de `updateMRNowPlayingInfo`/artwork. O último marcador RC antecedeu o ensaio musical e não mudou ao abrir o cartão durante a reprodução; não atribuir as duas conexões ao fluxo de áudio sem correlação de sessão. Piscina continuou `0/0/0`.
4. Em Apple Music via AirPlay 2 somente para Cozinha, o usuário confirmou **som audível; Casa sem controles**. A API sanitizada mostrou `streaming`, sete atualizações Now Playing, dez `updateMRSupportedCommands`, campos de título/artista/álbum/capa/duração/posição presentes e `invalid=0`, enquanto Piscina permaneceu `advertising`. Ao reproduzir, o anúncio chegou a `0x20404`, acrescentando apenas o bit de sessão ativa à Cozinha; o bit 10 continuou presente.

Conclusão restrita: o Shairport **negociou legitimamente** o bit 10 durante a readopção e aceitou conexões Remote Control Only, mas o cartão Casa do mesmo endpoint seguiu indisponível. Portanto, nem a ausência anterior do bit 10, nem a falta anterior de RC explicam **sozinhas** a falha. Não houve encaminhamento de Now Playing à conexão RC, teste de comandos Casa ou observação dos tokens internos de classificação Apple. O ensaio não prova bloqueio definitivo da plataforma, não autoriza anunciar capacidades do WiiM e não justifica remover/reparear a Piscina. Falta distinguir o papel do encaminhamento RC e das demais capacidades/negociações legítimas. Um eventual patch deve ser pequeno, reversível, limitado ao mesmo receptor e fisicamente homologado; não alterar produção estável a partir deste ACK.

### Próxima hipótese isolada: formato de metadados anunciado

O [código Shairport fixado](https://github.com/mikebrady/shairport-sync/blob/cf6998daa1876c5a8f97128a960c8afc0e731841/shairport.c) anuncia o bit 50 e solicita `updateMRNowPlayingInfo` binário por padrão. Quando `diagnostics.get_plist_metadata = "no"`, o próprio upstream anuncia os bits clássicos de texto/progresso/arte (15–17) e deixa de solicitar o plist enriquecido. O WiiM comparado anunciava esses bits clássicos, sem o bit 50; **correlação não é causalidade**. O [arquivo de configuração upstream](https://github.com/mikebrady/shairport-sync/blob/cf6998daa1876c5a8f97128a960c8afc0e731841/scripts/shairport-sync.conf) chama esse modo de compatibilidade de deprecated. Não copiamos bits arbitrários do WiiM.

A RC5 introduz uma opção HAOS **desligada por padrão** (`apple_legacy_metadata_zone = off | kitchen | pool`) que gera esse modo somente para uma zona, junto a `include_cover_art = yes` e sem cache local da arte. A outra zona e a identidade/pairing permanecem intactos. É uma POC de negociação *do próprio Shairport*, não um patch do protocolo RC. Sequência controlada: instalar RC5 no mesmo App com backup, manter `off` e conferir serviço; mudar para `kitchen`, reiniciar, confirmar mDNS e áudio/volume; testar o **mesmo** cartão Cozinha no Casa com Apple Music. Se ele continuar vazio, voltar a `off` e não declarar bloqueio geral da Apple. Nenhuma readopção adicional foi feita nesta etapa de código. A RC5 não deve virar estável sem regressão física; D16–D19 continuam FALHOU até prova visual e funcional contrária.

**Implantação em 19/10/2026, ~21:45 (America/Sao_Paulo):** a [RC5](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.5), commit de release `0c3159ff82c39c80ea263e5cf34d8571e6c8cdbf`, passou por testes locais (50 passaram, 1 ignorado), CI/testes/auditoria e build multi-arquitetura. Foi instalada **no mesmo App HAOS** com opção de backup da RC4 marcada; a UI confirmou `1.4.17-rc.5` e `Em funcionamento`. O Supervisor preservou `apple_mediaremote_experimental: true`. A nova opção não apareceu automaticamente nas opções existentes; foi adicionada pelo editor YAML do próprio App como `apple_legacy_metadata_zone: kitchen` e o Supervisor reiniciou o App. A UI voltou a mostrar ambas as zonas prontas e os dois destinos anunciados, sem erro de inicialização visível. Não houve reset de pareamento ou alteração da Piscina.

Consulta mDNS posterior ao reinício confirmou Cozinha `features=0x401FCA00,0x1C340`, Piscina **inalterada** em `0x401C4A00,0x5C340`. O `flags` da Cozinha voltou a `0x4` (o bit 10 da readopção não persistiu no processo Shairport após reinício); Piscina também `0x4`. No primeiro teste RC5, o usuário confirmou **som audível** pelo Apple Music na Cozinha e **“Ainda sem controles”** no cartão do próprio acessório Casa. A API do App mostrou Cozinha em `streaming`, quatro `updateMRSupportedCommands`, zero `updateMRNowPlayingInfo` (esperado neste modo clássico), zero erros de parsing e contadores RC `0/0/0`; Piscina continuou `advertising`. Esse resultado isolado ainda tinha o estado de acesso Casa reinicializado como variável concomitante.

O usuário autorizou expressamente uma segunda readopção **somente da Cozinha**, desta vez com o modo RC5 ativo. Após parar a música e remover o acessório, o anúncio ficou em `flags=0x4`; após readicionar o **mesmo** acessório, mudou legitimamente para `0x404`, sem trocar a identidade AirPlay. O processo contou `SETUP/event/updateInfo ACK = 2/2/2` na Cozinha, `0/0/0` na Piscina. No novo teste Apple Music, a Cozinha estava em `streaming` e anunciou `flags=0x20404` durante a sessão, com quatro SupportedCommands, zero NowPlaying enriquecido e zero erros; os três contadores RC permaneceram em `2/2/2` — a negociação foi observada na readopção, não novamente ao abrir o cartão. O usuário informou **“Controles não disponíveis”** no próprio Casa. A audibilidade foi confirmada no primeiro teste RC5, mas não foi respondida separadamente no segundo; `streaming` é evidência técnica de fluxo, não de som físico. Não houve nova captura RC5; o relato do usuário e os contadores sanitizados são as evidências deste reteste.

Conclusão restrita: **metadados clássicos + bit de acesso Casa + conexão RC com ACK de `updateInfo` não bastaram** para D16–D19. Isto não prova que todo receptor de terceiro seja bloqueado pela Apple, nem testa entrega de NowPlaying ao hub. Após o ensaio, `apple_legacy_metadata_zone` voltou a `"off"` pelo Supervisor e o App reiniciou; a UI confirmou `v1.4.17-rc.5` em funcionamento, ambas as zonas prontas e endpoints anunciados. O mDNS da Cozinha voltou a `features=0x401C4A00,0x5C340` e `flags=0x4`. Em sessões Apple Music separadas depois do rollback, o usuário confirmou **“Som, normal”** na Cozinha e **“Som normal”** na Piscina. Assim, o áudio físico das duas zonas voltou a funcionar, mas o **ARC/CEC com a TV e o compartilhamento TV→Cozinha não foram retestados** após esse reinício. O estado de acesso Casa **não persiste ao reiniciar Shairport** no código upstream atual; não alegar que o pareamento/RC ficou homologado após restart. Não removemos Piscina, WiiM ou qualquer outro acessório e não publicamos música, chave, IP ou imagem privada.

Não foi implantado o forwarder `updateMRNowPlayingInfo` ao canal RC neste branch: o build stock aceita RC e envia só `updateInfo`, e o [experimento da #2182](https://github.com/mikebrady/shairport-sync/issues/2182) obteve ACK de Now Playing em build **modificado** sem habilitar o cartão Casa. Além disso, o envio stock usa buffer fixo de 4096 bytes e ACK síncrono; retransmitir arte grande sem limite, política de concorrência e sessão RC ativa seria uma regressão de segurança/áudio. Um ACK futuro, por si, não cumpriria D16–D19.

**Ensaio RC7, ainda em 19/10/2026:** a [máscara de `features` comum a WiiM e Denon](APPLE_FEATURE_COMPARISON_TRIAL.md#resultado-de-campo--rc7) foi anunciada somente pela Cozinha. O iPhone mostrou falha de conexão, o usuário relatou oscilação e o Shairport não entrou em `streaming`, com repetição de `POST /auth-setup` não tratado nos logs. O teste parou antes de habilitar legitimamente o bit Casa `0x400` ou avaliar o cartão nativo. A opção foi revertida a `off`; mDNS original retornou nas duas zonas e o usuário confirmou som normal na Cozinha. Essa observação refuta a segurança da cópia integral da máscara neste build, não prova qual bit individual falha nem um bloqueio geral da Apple.

### Comparação somente de leitura do anúncio completo e `GET /info` — 20/10/2026

Foram lidas as 13 páginas do índice de [AirPlay 2 Internals](https://emanuelecozzi.net/docs/airplay2/), especialmente [descoberta](https://emanuelecozzi.net/docs/airplay2/discovery/), [features](https://emanuelecozzi.net/docs/airplay2/features/), [autenticação](https://emanuelecozzi.net/docs/airplay2/authentication/) e [RTSP](https://emanuelecozzi.net/docs/airplay2/rtsp/). Trata-se de engenharia reversa **não oficial, incompleta e datada**; suas condições de classificação são hipóteses verificáveis, não especificação da Apple para o cartão Casa.

Na rede da estação de trabalho, consultas DNS-SD de leitura descobriram WiiM e Denon, mas não as duas instâncias TecnoHead. A UI autenticada do App HAOS mostrou `v1.4.17-rc.5`, instâncias Cozinha/Piscina prontas e responder Avahi privado ativo; as portas RTSP 7000/7001 aceitaram conexão. A ausência nessa estação não demonstra que o anúncio TecnoHead sumiu da rede do iPhone: pode refletir o caminho de multicast entre a estação e o HAOS. O `GET /info` RTSP com `qualifier=txtAirPlay` respondeu `200 OK` nas duas instâncias e expôs o TXT que o próprio receptor entregaria a um emissor. A consulta também respondeu `200 OK` no WiiM e no Denon. Nenhuma configuração, adoção, sessão de mídia ou fonte foi alterada.

| Receptor | `features` | `flags` | Campos selecionados de `GET /info` |
| --- | --- | --- | --- |
| TecnoHead Cozinha/Piscina | `0x401C4A00,0x5C340` | `0x4` | `model=ShairportSync`; `sourceVersion`, `manufacturer` e `sdk` ausentes na resposta superior, embora `srcvers=366.0` esteja em `txtAirPlay`; `keepAliveSendStatsAsBody=false`; há `playbackCapabilities.supportsUIForAudioOnlyContent=false`. |
| WiiM Amp | `0x445F8A00,0x1C340` | `0x404` | `model=WiiM Amp`; `sourceVersion=366.0`, `manufacturer` e `sdk` presentes; `keepAliveSendStatsAsBody=true`; `playbackCapabilities` não apareceu. |
| Denon AVR-S960H | `0x445F8A00,0x801C340` | `0x404` | `model=Denon AVR-S960H`; `sourceVersion=366.0`, `manufacturer` e `sdk` presentes; `keepAliveSendStatsAsBody=true`; `playbackCapabilities` não apareceu. |

No `txtAirPlay`, as instâncias TecnoHead contêm `btaddr`, `fex`, `igl`, `pgid`, `psi` e `vv`, mas não `fv`, `manufacturer`, `rsf` ou `serialNumber`; o WiiM contém estes quatro últimos e não os primeiros. Ambos têm campos de identidade/pairing como `deviceid`, `pi` e `pk`, cujos **valores não foram extraídos para este relatório**. Os anúncios `_raop._tcp` de WiiM e Denon repetem as máscaras em `ft` e o estado em `sf`; a estação não observou `_raop` das instâncias TecnoHead, de modo que sua consistência mDNS/RAOP continua pendente. Não concluir causalidade do cartão Casa a partir de diferenças de presença de campos.

Segundo a tabela de [features](https://emanuelecozzi.net/docs/airplay2/features/), a condição inferida `ThirdPartySpeaker = bit 26 || bit 51` é falsa para a máscara TecnoHead e verdadeira nos dois receptores comerciais pelo bit 26. Essa é uma hipótese concreta para a classificação/ícone, **não** evidência de que habilite a UI. A página de [autenticação](https://emanuelecozzi.net/docs/airplay2/authentication/) associa o bit 26 a MFi e ao `POST /auth-setup`, coerente com a regressão RC7; como vários bits mudaram juntos, a atribuição causal isolada ainda não foi demonstrada. Não anunciar bit 26 ou 51, mudar modelo/identidade nem adicionar campos comerciais sem implementar legitimamente o protocolo correspondente. O significado de `supportsUIForAudioOnlyContent=false` neste contexto também é desconhecido; sua ausência no WiiM/Denon não prova que suprimi-lo habilitaria o cartão.

Ensaio físico comparativo concluído para WiiM versus Cozinha: com Apple Music enviado **somente ao WiiM**, o usuário confirmou som, título/capa e controles no próprio cartão Casa, inclusive pausa com efeito físico (**“Tudo funciona”**). De volta ao iPhone e enviando a mesma faixa **somente a TecnoHead Cozinha**, confirmou **“Som normal, controle não disponível”** no mesmo cartão Casa. Portanto a falha visual persiste com reprodução real e um comparador funcional no mesmo iPhone; não se observou a causa. Esta comparação não incluiu Piscina, Denon nem ensaio de tráfego simultâneo. Isolar somente mecanismos implementáveis no Shairport, com rollback, antes de nova alteração do App. Não é necessário readoção inicial do Casa nem Wireshark para esta comparação.

### Auditoria dirigida do canal Remote Control Only — 20/10/2026

O fonte upstream fixado em `cf6998d` foi inspecionado junto ao único patch instalado (`shairport-rc-diagnostics.patch`). Em `rtsp.c`, `handle_command()` encaminha os plists `POST /command` da sessão emissora ao pipe `ssnc/copl` e, quando compilado, ao metadata hub. Não chama a conexão Remote Control Only. Em `ap2_event_receiver.c`, o event port aceita a conexão RC e chama `ap2_event_send_update_info()` uma vez; o único comando de saída nesse caminho é `updateInfo`. Os três marcadores do patch TecnoHead apenas contam `SETUP`, conexão e ACK desse `updateInfo`. **Não há código nesse build que encaminhe `updateMRNowPlayingInfo` ou `updateMRSupportedCommands` do emissor ao event port RC.** A auditoria estabelece ausência de encaminhamento no software instalado, não prova se a central Apple exigiria esses eventos para habilitar a interface. A [correção explícita do autor na #2182](https://github.com/mikebrady/shairport-sync/issues/2182) distingue seu build modificado do stock e relata ACK de artwork sem cartão Casa funcional.

Consulta sanitizada do App em repouso: Cozinha `SETUP/event/ACK=0/0/0`; Piscina `1/1/1` após uma interação anterior, sem correlação com sessão de áudio. Os contadores de Now Playing são zerados quando a sessão termina; por isso uma medição temporal válida requer lê-los **durante** a próxima reprodução, não depois. Nenhum payload, endereço, chave ou faixa foi exportado. Não houve alteração de anúncio, pareamento, imagem ou configuração no HAOS nesta auditoria.

**Teste ao vivo na Cozinha:** o usuário iniciou Apple Music somente em TecnoHead Cozinha e confirmou som normal. Durante `streaming`, a API sanitizada contou **2** `updateMRNowPlayingInfo` com presença de título, artista, álbum, capa, duração e posição, e **4** `updateMRSupportedCommands`; zero erros de parsing e zero atualizações excessivas. Piscina ficou `advertising`, sem esses eventos. Após o usuário abrir o próprio cartão Casa e confirmar **“Sim, sem controles”**, a Cozinha permaneceu `streaming` com `SETUP/event/updateInfo ACK = 0/0/0`. A Piscina manteve seus contadores RC anteriores `1/1/1`, sem mudança neste ensaio. Assim, **nenhuma conexão RC concluída foi observada na Cozinha durante esse teste**, além de o build não possuir encaminhamento Now Playing. A sonda não identifica o peer de uma conexão anterior nem vê a decisão interna de classificação Apple: ausência de RC concluída não prova, isoladamente, bloqueio da plataforma ou causa única do cartão.

### Estado Casa e pareamentos após reinício — auditoria dirigida, 20/10/2026

Nova leitura **somente de código e estado público do receptor** no Shairport fixado (`cf6998d`) confirmou duas variáveis voláteis. Em `rtsp.c`, `POST /configure` recebe `Enable_HK_Access_Control`, altera `config.enable_HK_Access_Control` e o bit 10 de `config.airplay_statusflags`, e republica o anúncio; em `shairport.c`, a inicialização do bit 10 permanece comentada. A lista de controladores do fluxo `pair-add`/`pair-remove`/`pair-list` é uma lista encadeada global em memória (`struct pairings *pairings`); não há leitura/escrita de arquivo nesses callbacks. A chave pública do próprio receptor é derivada da identidade AirPlay, mas isso **não** preserva a lista de controladores autorizados. Portanto o processo perde o estado recebido da Apple e essa lista ao reiniciar. Não testamos aqui a reação exata do iPhone/hub a uma verificação de par após o reinício; uma sessão transitória ainda pode seguir outro caminho.

Após o reinício já realizado no ensaio anterior, `GET /info` respondeu `200 OK` nas portas das duas zonas e informou `flags=0x4` em ambas, concordando com a perda observada do bit 10. Isso é um defeito de persistência/continuidade **separado** do defeito-alvo do cartão: nas readopções RC4/RC5, o bit 10 legítimo ficou ativo (`0x404`), houve `SETUP/event/updateInfo ACK=2/2/2` e o usuário ainda viu “Controles não disponíveis”. Não forçar `0x400` sem `/configure` real, não inventar pareamentos e não pedir nova readopção apenas para mascarar a perda após restart.

O Supervisor mostra o App instalado como **`1.4.17-rc.7` em funcionamento**, enquanto o cabeçalho do Ingress diz **`v1.4.17-rc.5`**. O repositório explica a divergência: `config.yaml` declara RC7, mas `app/__init__.py` e o fallback de `app/settings.py` ainda dizem RC5. O cabeçalho não é prova de que o binário instalado voltou à RC5; identificar o build por mais de um sinal antes de qualquer próximo ensaio. O painel de logs do Supervisor, nessa inspeção, exibiu linhas de inicialização do App às 06:07, mas **não** trouxe eventos RTSP `/configure`/`pair-add` ou RC dessa janela; sua ausência ali não demonstra que esses eventos não ocorreram. A sonda por processo continua sendo a fonte dos contadores RC usados acima. Nenhum log bruto, chave, IP, arte ou faixa foi exportado.

Uma amostra passiva de mDNS da estação Windows viu anúncios AirPlay do WiiM e Denon e 18 serviços `_hap._tcp`, sem associação confiável de `_hap` a esses dois comparadores nessa amostra; as instâncias TecnoHead não foram descobertas pela mesma estação, embora ambas respondessem `GET /info`. A visibilidade multicast parcial impede inferir presença/ausência de HAP em qualquer dos receptores. O comparador comercial funcional no Casa permanece evidência visual/funcional, **não** especificação dos bytes necessários.

**Correção de rumo após revisão do código:** a persistência descrita como próxima experiência acima não foi implementada. `handle_pair_verify()` chama `pair_verify_new()` com callback de busca de controladores `NULL`, que na biblioteca seleciona verificação transitória, não autenticação contra a lista de `pair-add`. Persistir essa lista ou manter o bit 10 sem consertar e testar o fluxo de autenticação seria uma falsa garantia de segurança. A RC8 investiga somente o encaminhamento de Now Playing pelo canal RC, em uma zona e com flag desligada por padrão. A persistência continua hipótese separada, sem deployment.

### POC RC8 — encaminhamento limitado no mesmo receptor (antes do ensaio físico)

O patch `shairport-rc-now-playing-forward.patch` mantém em memória por processo somente o último `updateMRNowPlayingInfo` (até 512 KiB) e `updateMRSupportedCommands` (até 64 KiB) da sessão de áudio PTP que detém o player. Limpa os snapshots na troca/parada de sessão. Se a opção `apple_mediaremote_forward_zone=kitchen` for ativada, uma conexão RC já estabelecida e cifrada, com `Enable_HK_Access_Control` recebido legitimamente, recebe os dois eventos no seu próprio event port. A Piscina permanece desativada. O envio usa buffer proporcional limitado; registra apenas contagem de ACKs RTSP, sem faixa, capa, endereços ou payloads. `200 OK` aqui não é evidência de que o Casa habilitou botões.

O gate `config.enable_HK_Access_Control` é volátil e pode exigir nova readopção controlada da **Cozinha** após reinício; isso só será feito com autorização específica do usuário e preservando Piscina/WiiM/Denon. O `pair-verify` transitório do upstream não fornece uma prova de identidade persistente do peer RC: por isso a opção é exclusivamente de laboratório, desligada por padrão e deve ser mantida pelo menor tempo necessário na LAN autorizada. Não anunciar ou persistir classificação Apple falsa. O fluxo de comandos recebidos do Casa não foi implementado, pois a [discussão #2262](https://github.com/mikebrady/shairport-sync/discussions/2262) distingue os canais. Sem D16–D19 físicos, RC8 é **POC**, não solução homologada.

Em 20/10/2026, a [RC8](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.8) foi compilada para amd64/arm64, publicada como pré-release e instalada no **mesmo** App HAOS após backup local da RC7. Supervisor e Ingress confirmaram versão RC8 em funcionamento, NQPTP smi11 e duas zonas anunciadas. A flag foi ligada apenas na Cozinha para ensaio, mas não chegou resposta do teste físico no iPhone nessa janela; não houve readopção, ACK MR verificado ou evidência nova da UI Casa. Por segurança, a flag foi devolvida a `off` e ambas as zonas voltaram a anunciar após reinício. A instalação da POC é confirmada; **o objetivo visual continua não testado nesta versão**. A prova de áudio, volume, Casa e ARC/CEC terá de ser acompanhada em outra janela.

### Preparação RC9 — teste alternativo na Piscina

Ao retomar o teste, o Ingress RC8 exibiu `media_player.cozinha_room` **indisponível** mesmo após redescoberta, enquanto `media_player.piscina_room` estava **pronto** e ambos os endpoints AirPlay anunciados. A causa da indisponibilidade da Cozinha não foi identificada; não atribuí-la à rede sem diagnóstico. A RC8 seleciona exclusivamente a Cozinha para o relay, portanto tocar na Piscina com RC8 não exercita a POC. A RC9 altera somente a seleção opt-in para aceitar **uma** zona conhecida (`kitchen` ou `pool`), com `off` padrão; `both` e valores malformados falham fechados. O processo não selecionado recebe `TECNOHEAD_RC_NOW_PLAYING=0`. A Piscina deve ser ensaiada sem TV em uso para não confundir ARC/CEC com o fluxo AirPlay. Esta preparação não atesta áudio físico, ACK de Now Playing nem mudança do cartão Casa; esses resultados dependem da janela de teste no iPhone e de consentimento para a exposição temporária de metadados na LAN.

A [PR #15](https://github.com/aoliveira07/tecnohead-multimidia/pull/15) passou teste, validação de App e build amd64/arm64; a [pré-release RC9](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.9) publicou a imagem sem mover `latest`. Antes do update HAOS, foi confirmado um backup manual local **“TecnoHead Multimídia RC8 antes de RC9 Piscina”** com o App RC8 e as definições mínimas de restauração; a atualização também foi solicitada com cópia da versão anterior. O Supervisor confirmou `1.4.17-rc.9` instalada e em funcionamento, e o Ingress confirmou RC9 online, NQPTP smi11, Piscina pronta e os dois destinos AirPlay visíveis. A entidade física da Cozinha permaneceu indisponível. A opção de relay foi verificada em `off` após a instalação; **nenhum teste físico, ACK RC ou alteração de UI Casa foi atribuído à RC9 até esse ponto**. A ativação na Piscina aguarda consentimento informado e TV livre; não readotar acessórios sem autorização separada.

No teste físico posterior, o usuário autorizou por janela curta `apple_mediaremote_forward_zone=pool` com TV livre. O App reiniciou, recebeu AirPlay 2 na Piscina e encaminhou o stream ao LinkPlay; o usuário confirmou som, mas o próprio acessório no Casa permaneceu sem controles. A opção foi desligada e o App reiniciado; ambas as instâncias voltaram a anunciar. **Não medimos ACK de Now Playing/SupportedCommands nessa janela** e não houve readopção da Piscina. Logo, a falha visual não demonstra que o Casa recebeu e rejeitou o payload da RC9. Após o rollback, mDNS somente de leitura mostrou TecnoHead `features=0x401C4A00,0x5C340`, `flags=0x4`, `model=ShairportSync` em ambas as zonas, enquanto o WiiM manteve `features=0x445F8A00,0x1C340`, `flags=0x404`, `model=WiiM Amp`. O bit 10 do TecnoHead é volátil após reinício; seu estado **durante** a janela não foi capturado. A hipótese combinada de classificação/ícone com relay permanece não demonstrada. Ver [laboratório local](AIRPLAY_TRIAL_LAB.md) para variantes limitadas e checkpoints.

Na RC1, a inspeção local dos logs do HAOS revelou que o log de acesso HTTP do Uvicorn exibia a URL do stream com token de sessão. O valor não foi copiado ou publicado. A RC2 desliga esse log nos dois entrypoints, mantendo eventos operacionais; após abrir o painel RC2, não apareceram novas linhas de acesso desde o início do processo. Logs anteriores podem permanecer no histórico local e **não devem ser exportados sem sanitização**. Ainda falta provar esse ponto com uma nova sessão real de áudio.

### Evidência nova do AirPlay Lab v0.1.4 — metadados enviados, cartão vazio

Em 20/10/2026, no receptor descartável independente (não nas zonas reais),
o usuário iniciou Apple Music **antes** de readotar o Lab no Casa. Já havia
snapshots de `updateMRSupportedCommands` e `updateMRNowPlayingInfo` com campos
de título, capa e posição quando a conexão Remote Control Only foi aberta.
O Lab enviou ambos como `POST /command` no event port RC; os dois tiveram
resposta RTSP **2xx**, seguida de `TEARDOWN` do peer. O iPhone permaneceu
conectado por AirPlay, mas o próprio cartão continuou “Controles não
disponíveis”. O [código Shairport pinado](https://github.com/mikebrady/shairport-sync/blob/cf6998d/ap2_event_receiver.c)
verifica o status RTSP antes de retornar valor positivo, portanto esses
marcadores não significam apenas escrita local. O relay foi desligado de novo
(`lab_ready B0`). Nenhum dado de mídia ou identificador de rede foi publicado.

**Interpretação limitada:** o teste confirma transporte e resposta do peer,
não aceitação semântica pela Apple Home. A instrumentação atual não identifica
se o peer RC era o HomePod/hub ou outro controlador. A
[discussão #2262](https://github.com/mikebrady/shairport-sync/discussions/2262)
alerta que o canal de sessão PTP e o RC-only não têm o mesmo protocolo para
todos os comandos; não inferir do 2xx que o framing desses updates produz
controle nativo. A [issue #2182](https://github.com/mikebrady/shairport-sync/issues/2182)
relata um experimento comunitário parecido e sugere gate de classificação,
mas a observação positiva de WiiM e Denon no Casa deste usuário impede
generalizar o bloqueio a todo receptor de terceiros. Ainda falta comparar
uma implementação comercial legítima e determinar quais capacidades ela
realmente oferece, sem copiar modelo, certificado ou identidade.

### AirPlay Lab v0.1.5 — modelo próprio + bits clássicos + relay RC

O ensaio isolado `M1/tecnohead_model_classic_bits` manteve o AirPlay conectado
e recebeu Now Playing com capa e comandos suportados. O anúncio com modelo
**próprio** e bits 15–17 não alterou o ícone genérico do Lab nem o cartão
“Controles não disponíveis”. Após readopção somente do Lab, com a faixa já
direcionada a ele, o gate RC passou a `31` e houve uma resposta RTSP **2xx**
para SupportedCommands e uma para Now Playing. O usuário reabriu o cartão e
confirmou que ele permaneceu sem controles. Assim, não se pode atribuir esta
falha apenas à falta dos metadados no receptor ou à ausência de transporte
RC neste ensaio; tampouco se pode afirmar que o peer interpretou os plists
ou que uma exigência Apple específica foi demonstrada. Ver a sequência
sanitizada em [AIRPLAY_TRIAL_LAB.md](AIRPLAY_TRIAL_LAB.md). Nenhuma alteração
de anúncio foi aplicada às zonas de produção.

## Sequência de campo ainda necessária

1. O backup manual criptografado **“TecnoHead Multimídia pré-MediaRemote 2026-10-19”** foi criado no armazenamento **Este sistema**, 22,94 MB, com App v1.4.16 e configurações HA como itens restauráveis. Backups da atualização RC1/RC2 também foram solicitados. Nenhuma restauração foi feita, para não interromper o sistema. Preservar o pareamento Apple; não repará-lo como primeira tentativa.
2. Reproduzir Apple Music em uma zona por vez. Comparar D-Bus `NowPlayingInformation` e `CommandInformation`, `ssnc/copl`, comandos reais play/pause/skip, estado e áudio. Não deduzir suporte de `Available=false`.
3. Instrumentar apenas logs sanitizados de `RTSP SETUP Remote Control Only`, origem/hub e ACK. Correlacionar cada conexão com sua zona/sessão; não capturar chaves, áudio, capa ou endereços identificáveis.
4. Só se os dados do emissor existirem e houver conexão RC legítima, avaliar POC de encaminhamento no **mesmo** endpoint. O `ap2_event_port_post_command()` stock usa buffer fixo de 4096 bytes: corrigir limite/alocação e testar payload grande antes de qualquer retransmissão. Um `200 OK` do hub é apenas D14, não D16–D19.
5. Testar visualmente no iPhone real, por zona. Se o Casa continuar vazio apesar da entrega, documentar classificação/capacidades observadas e consultar o usuário antes de qualquer alternativa. Jamais anunciar HomePod/Apple TV ou criar segundo acessório.

## Estado de acesso/governança

Houve acesso autenticado ao HAOS via navegador para inventário, backup, atualização e diagnóstico sanitizado; o usuário forneceu capturas reais do iPhone/Casa. A primeira sessão de Cozinha foi acompanhada até o estado `streaming`, mas a falha de parser impede usar os zeros da RC2 como evidência de ausência de metadados do emissor. A busca por conexão oficial do Kanban Smart House não encontrou o serviço; Trello e ClickHouse não são substitutos autorizados. Checklist e bloqueios permanecem em [MEDIAREMOTE_D01_D24.md](MEDIAREMOTE_D01_D24.md) até que a API oficial esteja disponível. Nenhuma escrita em PostgreSQL foi feita.

### Lab v0.1.6 — diferença de ícone ainda não localizada

O ensaio de IPv6 isolado confirmou anúncio AAAA e sessão de controle IPv6,
sem habilitar o cartão Casa. A combinação seguinte conservou IPv6 e somou
modelo próprio, bits 15–17 de metadados implementados e relay RC. Mesmo após
readopção durante a música, houve snapshots e respostas RTSP 2xx para
SupportedCommands e Now Playing, mas o usuário confirmou “Casa sem
controles”. A máscara do Lab combinado foi
`0x401FCA00,0x5C340`; a observada no WiiM foi
`0x445F8A00,0x1C340`. Os bits 22 (sem semântica implementada) e 26
(`ThirdPartySpeaker` em [pesquisa de protocolo](https://emanuelecozzi.net/docs/airplay2/features/))
são diferenças, **não** uma receita de classificação: habilitar bit
desconhecido ou associado a perfil comercial/MFi sem suporte real poderia
quebrar AirPlay ou representar capacidade inexistente. A RC7, com máscara
comercial, já falhou antes do cartão.

O [mapeamento de descoberta](https://emanuelecozzi.net/docs/airplay2/discovery/)
mostra que `features` são apenas um dos campos TXT; `model`, `manufacturer`,
`serialNumber` e `flags` também existem. Na captura local, WiiM anunciou
`manufacturer` e `serialNumber` próprios; o Shairport fixado só publica
`model` entre esses campos de identificação. `isGroupLeader=0` no WiiM e
`igl=0` no Lab não diferenciam um líder ativo nesse ensaio. Não foi
demonstrado que acrescentar fabricante/série **próprios** altere o ícone
ou a UI; seria um próximo teste isolado de anúncio, sem falsificar
identidade ou afirmar MFi. A [issue upstream #2182](https://github.com/mikebrady/shairport-sync/issues/2182)
contém hipótese comunitária de classificação Apple, mas o WiiM e o Denon
funcionando no Casa nesta residência impedem tratá-la como bloqueio geral
comprovado. Estado: PARCIAL; D16–D19 não homologados. O App principal segue
parado; o Lab v0.1.6 foi mantido em M1/anúncio próprio/IPv6 a pedido do
usuário.

### Lab v0.1.10 — comando ao emissor comprovado, Casa ainda vazio

Em 21/10/2026, um ensaio no Lab descartável separou explicitamente os
dois fluxos que a [discussão upstream #2262](https://github.com/mikebrady/shairport-sync/discussions/2262)
descreve: `sendMediaRemoteCommand` saiu pelo event channel da sessão
**áudio/PTP**, enquanto o relay de Now Playing anterior usava a conexão
**Remote Control Only**. O Lab recebeu PCM e metadados do Apple Music;
uma pausa e um play únicos registraram categoria PTP e POST aceito.
O usuário confirmou que o iPhone pausou e retomou **sem toque manual**.
O mesmo cartão Lab no app Casa, durante a reprodução, continuou com
“Controles não disponíveis”. Portanto, falta de mecanismo outbound
play/pause **não explica sozinha** o cartão vazio; o ensaio não prova que
o Casa tenha solicitado ou recebido comandos, nem que a classificação
Apple esteja bloqueada. O caminho de investigação restante é comparar
negociação/assinatura efetiva do acessório e mensagens **originadas pelo
Casa/hub**, com o WiiM/Denon positivos, sem copiar identidades ou
certificados. Detalhes e limites no [relatório do Lab](AIRPLAY_TRIAL_LAB.md#resultado-físico-lab-0110--comandos-na-sessão-de-áudioptp).
