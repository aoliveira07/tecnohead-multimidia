# Relatório de homologação — TecnoHead Multimídia 1.2.1

## Escopo observado nesta entrega

- Implementação local do App e sua UI Ingress.
- Transporte IR exclusivamente pela API/serviço do Home Assistant.
- Presets ON/OFF genéricos autorizados, persistência e restauração.
- Filtro estrito por área e validação antes de cada ação física.
- Motor de cenas por área, proteção de TV, clima e desligamento de luzes.
- MQTT Discovery opcional e documentação de HomeKit/Alexa.
- 10 testes automatizados locais: PASSOU.

## Não observado

O repositório GitHub e a release instalável foram publicados. Ainda não houve sessão autorizada do HAOS do cliente, broker real ou acesso aos equipamentos físicos. Portanto, esta versão não é classificada como `instalado` ou `homologado`; o status correto é `publicado / instalável / parcialmente testado / implantação bloqueada por acesso de ambiente`.

## Bloqueios objetivos

1. URL/credencial de acesso ao HAOS autorizado, ou uma sessão de Ingress disponibilizada.
2. Janela segura para observar projetor, telão, Denon, TV, LG, luzes, MQTT e assistentes de voz.

## Evidências locais

- `python -m pytest -q`: 10 passed.
- `ruff check app tests`: passou.
- `python -m compileall -q app tests`: passou.
- O payload de OFF foi verificado em teste simulado como duas chamadas `remote.send_command` independentes, sem `num_repeats`, com 5,0 s após o retorno da primeira.

## Próxima atualização obrigatória

Após o acesso, executar [TEST_PLAN.md](docs/TEST_PLAN.md), anexar capturas reais, registrar versão instalada, SHA, tag/release, entidades mapeadas e pendências. Se qualquer teste físico falhar, corrigir, versionar e repetir a janela de testes antes de mudar o status para homologado.
