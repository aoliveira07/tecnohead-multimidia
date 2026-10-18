# Changelog

## 1.2.11

- Corrige a manutenção do modo lógico em cenas parcialmente degradadas, permitindo que o temporizador de iluminação execute mesmo quando a aleta não puder ser confirmada.
- Mantém switches fora da classificação de iluminação protegidos e adiciona regressão automatizada para as três luzes descobertas da área.
- Ajusta a sequência do projetor para duas chamadas OFF independentes com intervalo configurável padrão de 4 s após o retorno da primeira chamada.

## 1.2.10

- Validação segura da entidade `remote` por área sem emitir IR.
- Cenas continuam as etapas independentes quando receiver, Apple TV ou climatização estão indisponíveis, registrando a degradação.
- MQTT Discovery informa a área sugerida do dispositivo.

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
## 1.2.9

- Alinha a versão exibida no painel, no runtime, nos metadados MQTT e no pacote do App.
