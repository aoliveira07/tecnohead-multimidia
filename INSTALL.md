# Instalação para um cliente novo

Este App não requer servidor externo, banco PostgreSQL, HACS, arquivo YAML de automação ou integração IR nova. O cliente precisa ter Home Assistant OS/Supervisor compatível, acesso de administrador e as integrações dos equipamentos já funcionando no Home Assistant.

## Pré-requisitos

- Home Assistant OS com arquitetura `amd64` ou `aarch64` e Core compatível com o `homeassistant` mínimo do `config.yaml`.
- Entidades dos equipamentos já visíveis no HA, associadas às áreas corretas.
- Para IR: uma entidade `remote` funcional integrada no HA; a instalação BroadLink existente deve permanecer no HA.
- MQTT e, se desejado, HomeKit Bridge/Alexa configurados no próprio HA.

## Instalação

1. Faça backup normal do Home Assistant.
2. Adicione a URL do repositório no App Store.
3. Instale e inicie o App.
4. Abra o Ingress e confirme que o cabeçalho mostra a versão instalada.
5. Execute **Atualizar descoberta**.
6. Selecione a área desejada e habilite seu perfil.
7. Mapeie TV, receiver, telão, clima, sensor opcional e Apple TV opcional. Só aparecem entidades cuja área efetiva vem do registro de entidades ou do dispositivo no HA.
8. Selecione o `remote` sugerido. Se uma entidade esperada estiver fora da área, corrija sua associação no HA com o procedimento normal do HA e atualize a descoberta; o App não altera registros de outras entidades automaticamente.
9. Confirme a fonte Cinema lendo `source_list` real do receiver. Não adivinhe o rótulo da entrada Apple TV.
10. Classifique somente switches que sejam comprovadamente iluminação. Luzes do domínio `light` são descobertas automaticamente.
11. Salve o perfil, teste o telão e as ações de receiver em volume baixo, depois execute os testes IR com confirmação.

## Reversão

Pare/desinstale o App pelo Supervisor. O volume privado do App pode ser restaurado pelo backup do próprio HA. A remoção do App não remove a integração BroadLink, automações existentes, entidades, MQTT broker ou outros Apps. Se uma atualização apresentar regressão, reinstale a tag/release anterior e restaure somente o volume do App quando necessário.
