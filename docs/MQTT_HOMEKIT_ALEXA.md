# MQTT Discovery, HomeKit Bridge e Alexa

## MQTT Discovery

Com `mqtt:want`, o App lê as credenciais do serviço MQTT pelo Supervisor. Se o broker não estiver disponível, a UI e o motor local continuam disponíveis e o diagnóstico mostra a degradação.

Para cada área habilitada são publicados, com `unique_id` estável e device context:

- switch de modo Cinema;
- switch de modo TV;
- switch mestre Multimídia;
- sensor de modo, fase e diagnóstico.

Os tópicos de comando não são retidos. Discovery e estados são retidos para que o HA possa reconstruir entidades, e o App republica Discovery quando recebe o birth `homeassistant/status=online`. Estados e disponibilidade têm LWT. Comandos antigos não são reexecutados após restart.

Cinema e TV são mutuamente exclusivos. Ligar um modo troca diretamente o estado lógico do outro; não passa por Desligar Multimídia. Desligar o modo ativo executa a cena OFF.

## HomeKit Bridge

O App não configura nem altera filtros do HomeKit Bridge. Quando o HomeKit Bridge da instalação expõe entidades MQTT, os switches podem aparecer conforme os filtros já definidos no HA. Verifique a entidade e execute um comando real durante a homologação.

## Alexa

O App não cria credenciais nem configura a integração Alexa. Se a instalação já expõe esses switches pelo HA/Alexa, valide frases e retorno de estado durante A16. Ausência da integração deve ser registrada como pendência, não como sucesso.
