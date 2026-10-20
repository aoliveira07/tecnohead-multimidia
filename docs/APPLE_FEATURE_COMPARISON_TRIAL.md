# Ensaio isolado: máscara AirPlay comum a WiiM e Denon

Status em 19/10/2026: **ensaiado e revertido; hipótese falhou no teste de conexão/áudio da Cozinha**. A opção experimental permanece `off`. Não há homologação do cartão Casa nem autorização técnica para tornar a máscara definitiva.

O usuário propôs testar em conjunto `features` e o bit de acesso ao Casa após observar cartões funcionais no WiiM Amp e no Denon AVR-S960H. A leitura DNS-SD sanitizada encontrou `features=0x445F8A00,0x1C340` nos dois receptores; o Denon anuncia também o bit 59 no segundo bloco (`0x801C340`), que **não** faz parte da interseção. O Shairport instalado anuncia `0x401C4A00,0x5C340`. Não há demonstração de que a máscara, sozinha ou com `flags`, seja a causa do cartão Casa.

O patch experimental altera somente o valor de `features` do processo Cozinha para a máscara comum `0x0001C340445F8A00` quando `apple_feature_comparison_zone: kitchen` for configurado. Esse valor é usado pelo Shairport tanto no DNS-SD quanto na resposta `GET /info`; `fex` é gerado a partir dele. A opção ativa metadados clássicos e capa para manter o formato solicitado ao iPhone coerente com a máscara. O nome, modelo `ShairportSync`, identidade AirPlay, porta, pairing, áudio PCM, volume LinkPlay, instância Piscina e HDMI ARC não são alterados. A opção padrão é `off` e qualquer valor diferente de `kitchen` falha fechado.

O bit `0x400` de `flags` **não é forçado** pelo patch: no upstream ele é definido por `POST /configure` com `Enable_HK_Access_Control`. No ensaio anterior a Cozinha chegou a `flags=0x404` com ACK Remote Control Only e continuou mostrando “Controles não disponíveis”. O Denon passou de `0x804` para `0xc04` após a adoção e mostrou cartão funcional. A combinação exata máscara comum + acesso Casa legítimo ainda não foi testada no TecnoHead.

## Riscos e limites

- A máscara remove os bits 14 e 50 do anúncio atual e acrescenta 15–17, 22 e 26. O upstream implementa os bits clássicos de metadados 15–17, mas a semântica/implementação dos bits 22 e 26 neste receptor não foi estabelecida; o emissor pode tentar um modo que ele não suporta. Por isso o código é **apenas POC**, nunca default ou definitivo sem áudio real, regressões e prova no Casa.
- O ensaio deve ocorrer apenas na Cozinha, em janela curta, com backup do App e versão anterior disponível. Piscina/ARC não entram no teste inicial.
- Não copiar `model`, `manufacturer`, serial, chave, certificado, HAP ou identidade de receptor comercial. Não criar segundo acessório.
- Se o iPhone descobrir o destino mas não sair som, ou se houver falha de conexão, desativar a opção e reiniciar o App antes de prosseguir.

## Sequência de campo exigida

1. Confirmar versão do App HAOS, opções atuais, áudio normal nas duas zonas, estado do cartão Cozinha e backup/restauração possível.
2. Instalar uma imagem experimental rastreável, com `apple_feature_comparison_zone: off`; conferir que os anúncios e áudio não mudaram.
3. Mudar somente para `kitchen`; reiniciar o App; conferir no mDNS Cozinha `0x445F8A00,0x1C340`, Piscina inalterada. Verificar AirPlay e som audível da Cozinha antes de abrir o Casa.
4. Verificar se `flags` da Cozinha contém `0x400`. Se não, consultar o usuário antes de remover/readicionar **somente** Cozinha ao Casa; não mexer em Piscina, WiiM ou Denon.
5. Apple Music somente em Cozinha: confirmar som, abrir o **mesmo acessório** no Casa e verificar capa/faixa/posição/controles. Se houver botões, testar pausa, próximo e volume fisicamente. Registrar screenshot privado e logs sanitizados.
6. Testar reconexão, mudança de faixa, volume, agrupamento AirPlay e regressão Piscina/ARC quando houver disponibilidade física. Se falhar, voltar a `off` e verificar áudio novamente.

Não marcar a variante como definitiva ou v1.3.2 resolvida até que os testes de Casa Cozinha/Piscina e regressões passem. A ausência de controle, mesmo com os bits coincidentes, será evidência contra essa hipótese e orientará a investigação do canal Remote Control Only/Now Playing ou classificação HAP legítima.

## Resultado de campo — RC7

- O App HAOS foi atualizado para `1.4.17-rc.7` (prerelease; `latest` estável não mudou) depois de backup manual local criptografado. A opção começou em `off` e foi ativada **somente na Cozinha**. O mDNS confirmou Cozinha `features=0x445F8A00,0x1C340` e Piscina inalterada em `0x401C4A00,0x5C340`. As duas anunciaram `flags=0x4`; portanto a combinação máscara + bit Casa `0x400` não chegou a ser testada.
- Ao escolher **somente TecnoHead Cozinha** no Apple Music, o usuário informou “Falha ou oscilação” e enviou captura privada do iPhone com “Não foi possível conectar”. O App não chegou a `streaming`; logs do Shairport mostraram tentativas repetidas `POST /auth-setup` não tratadas. Isto é uma regressão de negociação observada com essa máscara, não identifica qual bit isolado a provocou.
- Pelo critério de interrupção acima, **não** houve readopção no Casa, teste da interface nativa ou promoção da máscara a configuração definitiva. Piscina, WiiM, Denon e TV não foram alterados neste ensaio.
- `apple_feature_comparison_zone` foi devolvida a `off` na configuração do App e o App reiniciou. A UI confirmou ambas as zonas prontas/visíveis no AirPlay; consulta mDNS pós-rollback confirmou as duas com a máscara original `0x401C4A00,0x5C340` e `flags=0x4`. O usuário reproduziu novamente **som normal na Cozinha, sem erro ou oscilação**, após o rollback. O áudio da Piscina e o ARC/CEC não foram retestados após este último reinício; a Piscina não recebeu a máscara experimental.

Conclusão: copiar a interseção de `features` de dois receptores comerciais para um build Shairport que não implementa necessariamente todas as capacidades anunciadas **não é seguro nem suficiente**. O resultado não prova que o cartão Casa seja impossível, tampouco demonstra a hipótese da combinação com o bit Casa, pois o fluxo de áudio falhou antes desse checkpoint. Próximos ensaios devem começar por capacidades **implementadas**, em alterações menores e reversíveis, sem afirmar suporte por identidade ou bits desconhecidos.
