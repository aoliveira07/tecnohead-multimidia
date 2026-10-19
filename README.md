# TecnoHead Multimídia

App para Home Assistant OS que transforma áreas cadastradas no HA em ambientes multimídia com cenas Cinema, TV e Desligar. A interface é em português brasileiro, responsiva, aparece na sidebar por Ingress e usa um motor próprio por área — sem criar automações YAML intermediárias.

## Estado da entrega 1.4.16

O módulo v1.2 permanece no mesmo App, com Ingress, MQTT Discovery, cenas e IR pela entidade do Home Assistant. O áudio multiroom usa os players LinkPlay reais `media_player.cozinha_room` e `media_player.piscina_room`, descobertos por área. A v1.4 acrescenta a implementação do receptor AirPlay 2 virtual: duas instâncias Shairport Sync upstream fixadas, NQPTP compartilhado, mDNS do host e ponte PCM→stream local encaminhada ao LinkPlay por `media_player.play_media`.

O operador confirmou áudio AirPlay nas zonas Cozinha e Piscina e a seleção simultânea pelo iPhone; nesse último teste o volume oscilou por retorno atrasado do LinkPlay. A v1.4.16 corrige o ciclo de realimentação no código, mas o reteste físico ainda é necessário. Em capturas privadas, `TecnoHead Cozinha` foi adicionado ao app Casa como acessório ShairportSync, mas o cartão Casa exibiu “Controles não disponíveis”. O pareamento da Piscina no Casa, o compartilhamento da TV por LinkPlay e a regressão física integral ainda não estão homologados. Os receivers `Cozinha Room` e `Piscina Room` no Casa são acessórios separados do HomeKit Bridge do HA. Veja [HOMOLOGATION.md](HOMOLOGATION.md), [AUDIO_DISCOVERY_REPORT.md](docs/AUDIO_DISCOVERY_REPORT.md) e [AUDIO_TEST_PLAN.md](docs/AUDIO_TEST_PLAN.md) para resultados e pendências.

Desde a v1.4.5, o App consulta o Avahi do host antes de publicar. Se o HAOS não oferecer Avahi no D-Bus, uma única instância interna compartilhada de D-Bus/Avahi é usada pelas duas zonas, sem iniciar dois respondentes e sem alterar o serviço global. A porta 18199 continua sendo usada pelo Ingress/stream; o estado mDNS e o diagnóstico ficam visíveis no painel.

## Arquitetura de segurança

- O App chama o proxy oficial do Home Assistant Core com `SUPERVISOR_TOKEN` e `homeassistant_api`.
- O emissor IR é apenas uma entidade `remote` da mesma área. Não há IP/MAC, protocolo LAN, autenticação própria, `python-broadlink` ou driver BroadLink neste projeto.
- O projetor usa `remote.send_command` com os presets próprios do App. BroadLink Base64 vira `b64:<payload>` somente no limite do transporte.
- Desligamento atual: primeira chamada HA → espera monotônica de 5,0 s após o retorno → segunda chamada HA. Não usa `num_repeats` como substituto e não reinicia o ciclo em timeout.
- O retorno da API confirma processamento pelo HA, não a resposta física do projetor. A UI e os diagnósticos deixam essa limitação explícita.
- O áudio segue a mesma regra: o retorno do serviço `media_player` não prova som audível. LinkPlay, ARC, AirPlay 2 e Casa só são marcados como homologados após evidência física.
- A configuração do cliente vive no volume privado `/data`; diagnósticos exportados redigem os códigos IR.

## Instalação no HAOS

1. Abra **Settings → Apps → App Store → Repositories**.
2. Adicione `https://github.com/aoliveira07/tecnohead-multimidia`.
3. Instale **TecnoHead Multimídia**, inicie-o e abra o painel **TecnoHead Multimídia** na sidebar.
4. Execute a descoberta e habilite somente as áreas que deseja comissionar.
5. No editor, selecione entidades oferecidas apenas pela área atual. A entidade `remote.ir_cinema` será sugerida quando realmente estiver associada à área Cinema no HA.
6. Salve o perfil e valide primeiro ações sem IR; use os botões de teste IR somente com confirmação local e o projetor em condição segura.

Para áudio, siga [AUDIO_MULTIROOM.md](docs/AUDIO_MULTIROOM.md) e [AIRPLAY2_BRIDGE.md](docs/AIRPLAY2_BRIDGE.md). Ative cada identidade AirPlay somente depois de confirmar os players físicos. A Piscina mantém o comportamento ARC do amplificador: a TV pode assumir a fonte ao ligar, enquanto uma seleção AirPlay explícita é encaminhada pelo App sem um bloqueio adicional.

Para clientes novos, siga [INSTALL.md](INSTALL.md) e [MANUAL_IMPLANTACAO_CLIENTE.md](docs/MANUAL_IMPLANTACAO_CLIENTE.md).

## Desenvolvimento

```powershell
cd tecnohead_multimidia
python -m pip install -r requirements.txt pytest pytest-asyncio ruff
python -m pytest -q
ruff check app tests
```

O build da imagem é feito pelo GitHub Actions para `amd64` e `aarch64`. O workstation usado para esta entrega não possui Docker; por isso, o build local da imagem não foi alegado como executado. A pipeline [CI](.github/workflows/ci.yml) executa testes, lint, auditoria de dependências, validação do metadata e build multi-arquitetura sem publicação. Tags `vX.Y.Z` publicam a imagem no GHCR e uma release.

## Documentação

- [Manual de implantação](docs/MANUAL_IMPLANTACAO_CLIENTE.md)
- [Configuração por ambiente](docs/CONFIGURATION.md)
- [IR via Home Assistant](docs/IR_HOME_ASSISTANT.md)
- [MQTT, HomeKit e Alexa](docs/MQTT_HOMEKIT_ALEXA.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Plano e checklist de testes](docs/TEST_PLAN.md)
- [Áudio Multiroom](docs/AUDIO_MULTIROOM.md)
- [Descoberta real de áudio](docs/AUDIO_DISCOVERY_REPORT.md)
- [Ponte AirPlay 2](docs/AIRPLAY2_BRIDGE.md)
- [Adaptador LinkPlay](docs/LINKPLAY_ADAPTER.md)
- [Apple Casa / HomeKit / AirPlay](docs/APPLE_HOME.md)
- [Plano B01–B45](docs/AUDIO_TEST_PLAN.md)
- [Relatório de homologação](HOMOLOGATION.md)
- [Changelog](CHANGELOG.md)

## Referências oficiais

- [Home Assistant Apps — configuração](https://developers.home-assistant.io/docs/apps/configuration/)
- [Apps — comunicação com Home Assistant](https://developers.home-assistant.io/docs/apps/communication/)
- [remote.send_command](https://www.home-assistant.io/actions/remote.send_command/)
- [Broadlink no Home Assistant](https://www.home-assistant.io/integrations/broadlink/)
- [iTach no Home Assistant](https://www.home-assistant.io/integrations/itach/)
- [MQTT Discovery](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery)
- [HomeKit Bridge](https://www.home-assistant.io/integrations/homekit/)
