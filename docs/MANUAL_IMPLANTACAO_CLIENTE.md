# Manual de implantação TecnoHead Multimídia

## 1. Levantamento somente leitura

Registrar antes de qualquer comando físico:

- versão do HAOS/Core, arquitetura e versão do App;
- áreas cadastradas e o nome exato da área do ambiente;
- entidades dos domínios `media_player`, `switch`/`cover`, `climate`, `light`, `sensor` e `remote` de cada área;
- fontes e capacidades anunciadas pelo receiver;
- `hvac_modes`, `fan_modes`, `swing_modes`, temperatura atual e estado do clima;
- disponibilidade de MQTT, HomeKit Bridge e Alexa.

Não copiar `.storage`, tokens, backups ou identificadores pessoais para o repositório.

## 2. Comissionamento de Cinema

1. Associe os dispositivos à área correta no HA.
2. Habilite a área e selecione as entidades.
3. Escolha a entidade `remote` da mesma área; quando `remote.ir_cinema` estiver válido, ela aparece como sugestão.
4. Confirme a fonte real do Denon para Apple TV e um volume inicial baixo. Os volumes armazenados são níveis HA `0.0–1.0`.
5. Confirme a capacidade do telão. Para o Cinema atual, `switch.tela` ligado abre/desce e desligado fecha/recolhe.
6. Configure aleta somente se o clima anunciar uma posição fixa válida. `swing` automático não é tratado como aleta alta fixa.
7. Salve e execute A02–A05 do [plano de testes](TEST_PLAN.md).

## 3. Testes físicos controlados

Execute uma única tentativa por etapa, respeitando o tempo de resfriamento do fabricante:

1. Teste de entidade/estado sem IR.
2. Teste IR ON explicitamente confirmado; observe o projetor.
3. Teste IR OFF explicitamente confirmado; observe o projetor e confira duas chamadas no diagnóstico, com 5,0 s entre o retorno da primeira e o início da segunda.
4. Verifique telão, TV, receiver, clima, aleta e luzes separadamente.
5. Execute Cinema completo, TV explícita, Desligar e TV física em Cinema inativo/ativo.
6. Teste MQTT e, quando presentes, HomeKit/Alexa.

Se houver timeout depois da primeira chamada OFF, o App fica `UNCERTAIN` e não faz uma terceira chamada. Não repita cegamente; faça uma verificação física segura e inicie uma nova ação explícita.

## 4. Evidências

Guardar no relatório da instalação somente capturas de tela sem tokens/IPs/códigos, timestamps, entidade selecionada, versão, commit/tag e resultado. Não incluir o backup do cliente. O diretório `docs/screenshots/` do código contém apenas instruções até que capturas reais do HAOS sejam coletadas.
