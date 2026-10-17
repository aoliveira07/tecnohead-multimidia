# Troubleshooting

## Nenhuma área ou entidade aparece

Confirme que o App está online no HA, execute **Atualizar descoberta** e verifique se o dispositivo/entidade tem área no registro do HA. O App não infere área pelo nome.

## `remote.ir_cinema` não aparece

Confira o estado atual da entidade `remote`, se ela não está desabilitada e se a área efetiva é Cinema. O backup antigo não é fonte de verdade. Reassocie a entidade/dispositivo no HA e atualize a descoberta. Não informe IP/MAC ao App.

## IR aceito, mas o projetor não respondeu

O retorno do HA não é feedback físico. Confira a entidade selecionada, a integração existente e o apontamento do emissor. Não dispare repetidamente. Use o teste explícito uma vez e, se o formato for outro emissor, forneça um preset compatível (por exemplo, Pronto Hex para iTach).

## Estado `UNCERTAIN`

Isso significa que a sequência física não pôde ser inferida com segurança, geralmente por indisponibilidade durante OFF→5s→OFF. O App não envia um terceiro OFF. Verifique o projetor localmente e faça uma nova ação explícita.

## Receiver não muda a fonte

Leia a `source_list` atual do Denon e use o rótulo exato. O App não presume que Apple TV seja o nome da fonte.

## Aleta não fica alta

O LG precisa anunciar uma posição fixa nas capacidades do clima. `swing_mode` automático não prova posição alta. Se não houver capacidade válida, a etapa fica documentada como não confirmada.

## Luz da pipoqueira não aparece

Somente uma entidade `light` da área entra automaticamente. Um `switch` só entra depois da classificação explícita no editor. Nunca marque o switch da máquina, aquecimento ou tomada como luz.

## MQTT não conecta

Confira se existe um broker configurado no HA e se o Supervisor informa o serviço MQTT. O App não grava credenciais no repositório. Após o broker voltar, aguarde o birth ou pressione atualizar.
