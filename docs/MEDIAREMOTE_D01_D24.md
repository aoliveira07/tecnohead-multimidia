# Homologação MediaRemote D01–D24 — v1.3.2

Atualização: 19/10/2026. `PASSOU` exige o critério inteiro e evidência; teste sintético ou inspeção de código não equivale a teste de iPhone/Casa. Evidências privadas enviadas pelo usuário **não são copiadas ao repositório**. Baseline estável: tag `v1.4.16` (`7c391d665ca9889debf800d33d25e536215ccbe5`). O HAOS confirmou App **v1.4.17-rc.3 instalado e em execução** com backup solicitado da RC2, Shairport `cf6998d` AirPlay 2/`smi11`, NQPTP `1.2.9`/`smi11`, Core/Supervisor `2026.10.2` e HAOS `18.3`. [RC3 publicada](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.3); `latest` segue na v1.4.16.

| ID | Estado | Evidência disponível / falta exata |
| --- | --- | --- |
| D01 | PASSOU | Inventário do repositório/tag/build e versão runtime feito pelo painel HAOS autenticado e Ingress; dois endpoints, um NQPTP, Avahi e D-Bus por zona identificados. Nenhum IP/ID privado publicado. |
| D02 | PASSOU | Captura privada anterior da Cozinha e capturas da Piscina às 19:18 de 19/10/2026: Apple Music mostra reprodução roteada para TecnoHead Piscina, enquanto o cartão do **mesmo destino** no Casa mostra “Controles não disponíveis”. A instalação consultada era v1.4.16. A captura comprova rota/reprodução no iPhone, não audibilidade física nem entrega de metadados ao hub. Imagens mantidas somente na conversa. |
| D03 | BLOQUEADO | Branch e tag `v1.4.16` preservados; backup manual local criptografado **“TecnoHead Multimídia pré-MediaRemote 2026-10-19”** concluído (22,94 MB). HAOS também solicitou backup da versão anterior nas atualizações RC1/RC2/RC3. A restauração **não foi executada** para não interromper a casa, logo ausência de perda após restore segue não comprovada. |
| D04 | PASSOU | Runtime instalado confirmou Shairport `cf6998d` com AirPlay 2/`smi11`, D-Bus/MPRIS/metadados e NQPTP `1.2.9`/`smi11`; o código pinado é posterior à tag 5.6. Comandos reais ainda pertencem a D09–D11. |
| D05 | NÃO TESTADO | Atualização não indicada: runtime já está em Shairport posterior a 5.6 e NQPTP 1.2.9, ambos `smi11`. Não alterar versões sem necessidade e backup. |
| D06 | PASSOU | No ensaio RC3 com Apple Music no iPhone e somente TecnoHead Cozinha, o usuário confirmou **som audível**. A instância Cozinha ficou em `streaming` e recebeu 3 `updateMRNowPlayingInfo` com presença de título, artista, álbum, capa, duração e posição; nenhum valor privado foi retido. Isto comprova chegada de metadados e reprodução física, **não** a UI do Casa ou controle de retorno. Leitura D-Bus separada continua pendente em D09. |
| D07 | PASSOU | No ensaio RC3 com Apple Music no iPhone e somente TecnoHead Piscina, o usuário confirmou **som audível**. A instância Piscina ficou em `streaming`, recebeu 2 `updateMRNowPlayingInfo` e 3 `updateMRSupportedCommands`, com presença de título/artista/álbum/capa/duração/posição, `invalid=0`, `oversized=0`. Cozinha ficou `advertising`, sem itens nem metadados cruzados. Conteúdo privado não foi retido. Isto não comprova controles no Casa. |
| D08 | NÃO TESTADO | Cozinha recebeu campo `artwork` real em 3 Now Playing, sem erro/truncamento detectado pela sonda (`invalid=0`, `oversized=0`). Falta validação de capa efetiva, tamanho real, memória e troca de faixas. Teste unitário usou plist sintético com arte de 194 kB e item >2 MiB seguido de volume. |
| D09 | NÃO TESTADO | Cozinha recebeu 3 `updateMRSupportedCommands` reais no pipe, com códigos habilitados. Falta conferir `CommandInformation` D-Bus e resposta efetiva da origem antes de declarar suporte funcional. |
| D10 | NÃO TESTADO | Requer play/pause/próxima no iPhone emissor via canal AirPlay 2 da Cozinha e observar resposta. |
| D11 | NÃO TESTADO | Mesmo procedimento para Piscina. |
| D12 | NÃO TESTADO | Requer log RTSP sanitizado da conexão `Remote Control Only` na instalação. |
| D13 | NÃO TESTADO | Requer associação observada entre conexão RC, áudio e zona, sem IDs/pairings publicados. |
| D14 | NÃO TESTADO | Nenhum patch RC foi enviado. A #2182 documenta ACK **de build modificado de terceiros**; não é prova deste App nem da UI. POC só após D01–D13 e rollback físico. |
| D15 | NÃO TESTADO | Há hipótese comunitária de gate `isAddedToHomeKit`/`isRemoteControllable`; falta observação passiva no iPhone/hub do cliente. |
| D16 | FALHOU | Reteste físico na **RC3**: Apple Music em TecnoHead Cozinha, som audível, 3 atualizações Now Playing recebidas, mas o usuário informou **“Casa sem controles”** no mesmo acessório. A sonda não encaminha metadados ao hub nem corrige a UI. |
| D17 | FALHOU | Reteste físico **RC3**: Apple Music em TecnoHead Piscina, som audível e 2 atualizações Now Playing recebidas, mas o usuário informou **“Casa sem controles”** no mesmo acessório. A captura v1.4.16 documenta o baseline visual; falta captura nova RC3. |
| D18 | FALHOU | Nos retestes RC3 de Cozinha e Piscina, campos de faixa/arte chegaram às respectivas instâncias e o usuário ouviu som, mas relatou que os cartões no Casa seguem sem controles; título/arte/estado não ficaram utilizáveis naquela tela. |
| D19 | FALHOU | Nos retestes RC3 de Cozinha e Piscina, o cartão Casa permaneceu sem controles, impedindo qualquer toque de play/pause ou volume por essa interface. Isto não questiona o volume pelo seletor AirPlay/painel, testado anteriormente. |
| D20 | NÃO TESTADO | Usuário relatou agrupamento/volumes funcionando antes. Regressão pós-alteração ainda não executada com iPhone. |
| D21 | NÃO TESTADO | ARC/CEC e TV Piscina→Cozinha relatados antes; regressão pós-alteração ainda não executada. |
| D22 | NÃO TESTADO | Faltam reconexão, troca, pausa e reinício App/HAOS reais. |
| D23 | NÃO TESTADO | Há ensaio parcial de Apple Music nas duas zonas RC3, separadamente (som audível, metadados recebidos), mas ainda falta Spotify via AirPlay e suporte real de comandos por origem. |
| D24 | BLOQUEADO | [RC3](https://github.com/aoliveira07/tecnohead-multimidia/releases/tag/v1.4.17-rc.3) publicada e instalada manualmente no App existente, com flag de diagnóstico habilitada; CI aprovou testes, configuração e build multi-arquitetura. D16–D19 não passaram; não há homologação de controles nativos Casa nem API autorizada do Kanban. |

## Provas automatizadas locais (não são D16–D19)

`python -m pytest -q` em `tecnohead_multimidia`: **46 passed, 1 skipped** na RC3; Ruff passou. Os testes novos reproduzem o enquadramento real do pipe (`Base64</data></item>` sem quebra), além de `copl`, privacidade, flag desligada por padrão, continuidade de `pvol` após item volumoso ou falha da sonda. Os testes automatizados não substituem iPhone, hub, HAOS ou amplificador físico.

## Sequência segura quando o acesso estiver disponível

1. D01/D02 estão documentados, e o backup de D03 existe; preservar o pareamento. Não remover/reparear acessórios como primeiro passo.
2. RC3 já foi instalada manualmente no **mesmo App**, sem substituir `latest`; a opção de sonda permaneceu habilitada no HAOS de ensaio. Cozinha e Piscina passaram D06/D07 com som audível; D16–D19 falharam no reteste físico. Próximo: observar `Remote Control Only` e capacidades do mesmo endpoint sem tocar no ARC/CEC. O relatório `sender_mediaremote_probe` não contém faixa/capa e não atesta a tela Casa.
3. Caso os metadados/canais justifiquem POC, revisar patch limitado em Shairport para buffer e retransmissão RC em branch, flag off por padrão. `RTSP 200 OK` satisfaz no máximo D14.
4. Comparar visualmente Casa com o baseline, executar D16–D23 e regressões de ARC/volume. Só então considerar release, atualização HAOS e D24.

Kanban: registro pendente por falta de API oficial autorizada; não houve escrita em PostgreSQL. A conexão de Trello encontrada no catálogo não é o Kanban Smart House e não foi usada.
