# Changelog

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
