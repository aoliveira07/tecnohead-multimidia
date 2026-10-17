# TecnoHead Multimídia

App para Home Assistant OS que transforma áreas cadastradas no HA em ambientes multimídia com cenas Cinema, TV e Desligar. A interface é em português brasileiro, responsiva, aparece na sidebar por Ingress e usa um motor próprio por área — sem criar automações YAML intermediárias.

## Estado da entrega 1.2.2

O código, a UI, a persistência, a descoberta por área, o transporte IR via `remote.send_command`, MQTT Discovery e a suíte simulada estão implementados. A homologação física e a instalação no HAOS do cliente permanecem pendentes até que esse ambiente seja disponibilizado ao operador; este repositório não afirma teste físico que não foi observado.

Os testes locais atuais são executados com um HA simulado e cobrem o intervalo OFF de 5 segundos, isolamento por área, cenas e evento de TV física. Veja [HOMOLOGATION.md](HOMOLOGATION.md) e [TEST_PLAN.md](docs/TEST_PLAN.md) para o status por critério.

## Arquitetura de segurança

- O App chama o proxy oficial do Home Assistant Core com `SUPERVISOR_TOKEN` e `homeassistant_api`.
- O emissor IR é apenas uma entidade `remote` da mesma área. Não há IP/MAC, protocolo LAN, autenticação própria, `python-broadlink` ou driver BroadLink neste projeto.
- O projetor usa `remote.send_command` com os presets próprios do App. BroadLink Base64 vira `b64:<payload>` somente no limite do transporte.
- Desligamento atual: primeira chamada HA → espera monotônica de 5,0 s após o retorno → segunda chamada HA. Não usa `num_repeats` como substituto e não reinicia o ciclo em timeout.
- O retorno da API confirma processamento pelo HA, não a resposta física do projetor. A UI e os diagnósticos deixam essa limitação explícita.
- A configuração do cliente vive no volume privado `/data`; diagnósticos exportados redigem os códigos IR.

## Instalação no HAOS

1. Abra **Settings → Apps → App Store → Repositories**.
2. Adicione `https://github.com/aoliveira07/tecnohead-multimidia`.
3. Instale **TecnoHead Multimídia**, inicie-o e abra o painel **TecnoHead Multimídia** na sidebar.
4. Execute a descoberta e habilite somente as áreas que deseja comissionar.
5. No editor, selecione entidades oferecidas apenas pela área atual. A entidade `remote.ir_cinema` será sugerida quando realmente estiver associada à área Cinema no HA.
6. Salve o perfil e valide primeiro ações sem IR; use os botões de teste IR somente com confirmação local e o projetor em condição segura.

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
