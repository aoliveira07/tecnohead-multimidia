# IR via integração do Home Assistant

## Transporte

O único transporte do App é o serviço do Home Assistant:

```yaml
action: remote.send_command
target:
  entity_id: remote.ir_cinema
data:
  command: "b64:<preset-do-perfil>"
```

Na chamada REST interna do App, `entity_id` é enviado no corpo do serviço; isso é a representação REST do target. Antes de cada chamada, o App refaz a validação do registro de área, domínio e disponibilidade.

O App usa o proxy do Core fornecido pelo Supervisor e seu token de App. Não conhece endereço do cliente, não abre protocolo LAN, não instala biblioteca de marca e não modifica `.storage`.

## Presets e sequência

Os presets genéricos ON/OFF autorizados ficam no código limpo e são copiados para o perfil quando necessário. O valor é salvo sem prefixo e recebe `b64:` apenas no envio. A validação rejeita prefixo duplo e Base64 inválido.

- ON: uma chamada independente.
- OFF: chamada independente 1 → retorno do HA → espera monotônica de 5,0 s → chamada independente 2.
- `num_repeats` não é usado como substituto.
- Erro antes da primeira chamada não gera retry. Erro/queda durante a espera gera `UNCERTAIN` e não envia terceiro comando.

O log registra entidade, tipo e retorno da chamada, nunca o payload bruto. O estado físico do projetor não é inferido como confirmado.

## Troca de emissor

Integre primeiro o novo emissor no Home Assistant e associe a entidade `remote` à área. Depois selecione-a no App; cenas e temporizações permanecem iguais. O formato do código pertence ao perfil:

- BroadLink: Base64 com prefixo HA `b64:`.
- iTach ou equivalente: normalmente Pronto Hex; não se deve enviar Base64 BroadLink como se fosse Pronto.
- Integração que expõe comando aprendido: comando nomeado, e opcionalmente `device` quando exigido pelo HA.

Não existe conversão automática presumida. Se não houver conversão tecnicamente válida e testada, forneça o formato compatível ao perfil e preserve o preset original.

Referências: [remote.send_command](https://www.home-assistant.io/actions/remote.send_command/), [Broadlink](https://www.home-assistant.io/integrations/broadlink/) e [iTach](https://www.home-assistant.io/integrations/itach/).
