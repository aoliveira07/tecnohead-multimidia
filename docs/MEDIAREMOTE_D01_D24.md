# Homologação MediaRemote D01–D24 — v1.3.2

Atualização: 19/10/2026. `PASSOU` exige o critério inteiro e evidência; teste sintético ou inspeção de código não equivale a teste de iPhone/Casa. Evidências privadas enviadas pelo usuário **não são copiadas ao repositório**. Branch de ensaio: `experiment/mediaremote-now-playing`; código da sonda: [commit `7d889d5`](https://github.com/aoliveira07/tecnohead-multimidia/commit/7d889d55e1835146064bf4bf2f5ad8dbcd456f4d); rollback de código: tag `v1.4.16` (`7c391d665ca9889debf800d33d25e536215ccbe5`). O HAOS confirmou App **v1.4.16 instalado e em execução**, Shairport `cf6998d` AirPlay 2/`smi11`, NQPTP `1.2.9`/`smi11`, Core/Supervisor `2026.10.2` e HAOS `18.3`. No último commit do PR, os jobs de teste, configuração e build multi-arquitetura passaram na [CI](https://github.com/aoliveira07/tecnohead-multimidia/actions/runs/39266461471).

| ID | Estado | Evidência disponível / falta exata |
| --- | --- | --- |
| D01 | PASSOU | Inventário do repositório/tag/build e versão runtime feito pelo painel HAOS autenticado e Ingress; dois endpoints, um NQPTP, Avahi e D-Bus por zona identificados. Nenhum IP/ID privado publicado. |
| D02 | PASSOU | Captura privada anterior da Cozinha e capturas da Piscina às 19:18 de 19/10/2026: Apple Music mostra reprodução roteada para TecnoHead Piscina, enquanto o cartão do **mesmo destino** no Casa mostra “Controles não disponíveis”. A instalação consultada era v1.4.16. A captura comprova rota/reprodução no iPhone, não audibilidade física nem entrega de metadados ao hub. Imagens mantidas somente na conversa. |
| D03 | BLOQUEADO | Branch e tag `v1.4.16` preservados; backup manual local criptografado **“TecnoHead Multimídia pré-MediaRemote 2026-10-19”** concluído (22,94 MB). Tela de detalhes lista App v1.4.16 e configurações HA restauráveis; a restauração **não foi executada** para não interromper a casa, logo ausência de perda após restore segue não comprovada. |
| D04 | PASSOU | Runtime instalado confirmou Shairport `cf6998d` com AirPlay 2/`smi11`, D-Bus/MPRIS/metadados e NQPTP `1.2.9`/`smi11`; o código pinado é posterior à tag 5.6. Comandos reais ainda pertencem a D09–D11. |
| D05 | NÃO TESTADO | Atualização não indicada: runtime já está em Shairport posterior a 5.6 e NQPTP 1.2.9, ambos `smi11`. Não alterar versões sem necessidade e backup. |
| D06 | NÃO TESTADO | Requer Apple Music no iPhone, Cozinha selecionada e leitura sanitizada de Now Playing no App/DBus. |
| D07 | NÃO TESTADO | Requer repetir na Piscina e verificar isolamento de metadados. |
| D08 | NÃO TESTADO | Teste unitário usou plist sintético com arte de 194 kB e o pipe ignora item >2 MiB sem perder volume; falta capa real e teste de memória/crash no Shairport. |
| D09 | NÃO TESTADO | Sonda unitária extrai códigos habilitados de `updateMRSupportedCommands`; falta `CommandInformation` da origem real. |
| D10 | NÃO TESTADO | Requer play/pause/próxima no iPhone emissor via canal AirPlay 2 da Cozinha e observar resposta. |
| D11 | NÃO TESTADO | Mesmo procedimento para Piscina. |
| D12 | NÃO TESTADO | Requer log RTSP sanitizado da conexão `Remote Control Only` na instalação. |
| D13 | NÃO TESTADO | Requer associação observada entre conexão RC, áudio e zona, sem IDs/pairings publicados. |
| D14 | NÃO TESTADO | Nenhum patch RC foi enviado. A #2182 documenta ACK **de build modificado de terceiros**; não é prova deste App nem da UI. POC só após D01–D13 e rollback físico. |
| D15 | NÃO TESTADO | Há hipótese comunitária de gate `isAddedToHomeKit`/`isRemoteControllable`; falta observação passiva no iPhone/hub do cliente. |
| D16 | FALHOU | Baseline anterior: captura privada mostra o acessório AirPlay TecnoHead Cozinha com “Controles não disponíveis”. Ainda sem reteste após a sonda (que não tenta corrigir UI). |
| D17 | FALHOU | **Baseline v1.4.16:** captura privada do próprio acessório TecnoHead Piscina no Casa mostra “Controles não disponíveis” apesar de Apple Music reproduzindo para esse destino. Ainda não houve reteste com POC; nenhum botão habilitado para toque. |
| D18 | FALHOU | **Baseline v1.4.16:** o Apple Music mostra capa/faixa/estado, mas o cartão Piscina no Casa permanece vazio. Cozinha tinha a mesma tela vazia em captura anterior. Ainda sem reteste após correção. |
| D19 | FALHOU | **Baseline v1.4.16:** play/pause e volume estão desabilitados no cartão Casa da Piscina; não é possível demonstrar resposta física por esse caminho. Ainda sem reteste após correção. |
| D20 | NÃO TESTADO | Usuário relatou agrupamento/volumes funcionando antes. Regressão pós-alteração ainda não executada com iPhone. |
| D21 | NÃO TESTADO | ARC/CEC e TV Piscina→Cozinha relatados antes; regressão pós-alteração ainda não executada. |
| D22 | NÃO TESTADO | Faltam reconexão, troca, pausa e reinício App/HAOS reais. |
| D23 | NÃO TESTADO | Falta matriz física Apple Music/Spotify via AirPlay por zona, incluindo comandos indisponíveis da origem. |
| D24 | BLOQUEADO | Branch/documentação/testes locais preparados em [PR rascunho #1](https://github.com/aoliveira07/tecnohead-multimidia/pull/1). Sem release/deploy desta sonda experimental, sem prova D16–D19 e sem API autorizada do Kanban. Não marcar como homologado. |

## Provas automatizadas locais (não são D16–D19)

`python -m pytest -q` em `tecnohead_multimidia`: **45 passed, 1 skipped**. Os testes novos verificam parser de `copl`, ausência de conteúdo privado no diagnóstico, opção HAOS desligada por padrão, isolamento da sonda pela flag e continuidade de `pvol` após metadado volumoso ou falha da sonda. Não houve conexão do teste com iPhone, hub, HAOS ou amplificador físico.

## Sequência segura quando o acesso estiver disponível

1. D01/D02 estão documentados, e o backup de D03 existe; preservar o pareamento. Não remover/reparear acessórios como primeiro passo.
2. Preparar uma forma de instalar a imagem de ensaio **sem substituir a tag `latest` nem a instalação estável**. Só então habilitar a sonda, um destino por vez, e verificar D04, D06–D13. O relatório `sender_mediaremote_probe` não contém faixa/capa e não atesta a tela Casa.
3. Caso os metadados/canais justifiquem POC, revisar patch limitado em Shairport para buffer e retransmissão RC em branch, flag off por padrão. `RTSP 200 OK` satisfaz no máximo D14.
4. Comparar visualmente Casa com o baseline, executar D16–D23 e regressões de ARC/volume. Só então considerar release, atualização HAOS e D24.

Kanban: registro pendente por falta de API oficial autorizada; não houve escrita em PostgreSQL. A conexão de Trello encontrada no catálogo não é o Kanban Smart House e não foi usada.
