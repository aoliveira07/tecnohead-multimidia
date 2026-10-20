# Laboratório local de ensaios AirPlay/Casa

## Receptor de laboratório independente (20/10/2026)

O App de produção **TecnoHead Multimídia** foi parado no HAOS e a opção
**Iniciar no arranque** foi desligada. Nada foi desinstalado ou apagado; a
configuração e a identidade dos acessórios antigos foram preservadas. O App
separado [`tecnohead_airplay_lab/`](../tecnohead_airplay_lab/) contém um único
receptor descartável, com nome/ID próprios e porta 7100. Seu PCM é drenado
para descarte; não existe integração com HA Core, MQTT, cenas nem LinkPlay.

No laboratório, B0/M1/M2/M3 variam apenas o pedido de metadados clássicos e o
relay MediaRemote já presente no binário RC9. Nenhum perfil copia a máscara de
WiiM/Denon, anuncia MFi, altera o modelo para Apple/comercial ou falsifica
pareamento. A adoção desse novo receptor no app Casa pode ser refeita entre
ensaios sem mexer nos antigos, como autorizado pelo usuário. A conexão RC
legítima e o resultado visual ainda precisam ser medidos fisicamente; não
há declaração de sucesso do cartão neste ponto.

Uma branch de repositório do HAOS pode ser instalada separadamente da loja
estável usando `#branch`, conforme a documentação oficial do Supervisor.
Depois da instalação, mudar o perfil na aba Configuração do Lab e reiniciar
**somente o Lab**. Examinar os contadores saneados em Registo e o mesmo cartão
no iPhone. Ao terminar, parar o Lab; ele usa `boot: manual`. Para restaurar o
App original, habilitar seu próprio início automático e pressionar Iniciar.

Estado observado em 20/10/2026: o commit `36bf0ee` foi publicado somente na
branch `codex/airplay-lab`, sem merge ou release estável. O repositório dessa
branch foi adicionado separadamente à loja HAOS; o Supervisor instalou o App
`TecnoHead AirPlay Lab` v0.1.0 e mostrou **Em funcionamento**, `boot` desligado.
A aba Configuração confirmou perfil B0 e o log saneado mostrou `lab_ready`,
porta 7100 e saída `discarded`. Antes do ensaio com o iPhone, os contadores
permaneciam sem PCM, Now Playing ou RC. Isso **não comprova** descoberta pelo
iPhone, adoção Casa ou controles nativos; esses resultados dependem do teste
físico. O App TecnoHead Multimídia original permaneceu **Parado**, com início
automático desligado; suas configurações não foram removidas.
O Kanban oficial Smart House continua sem conexão de escrita identificada nesta
sessão; este registro versionado é provisório e não substitui a atualização do
Kanban quando houver acesso autorizado.

## Planejador offline para Windows

O programa [`tools/airplay_trial_lab.py`](../tools/airplay_trial_lab.py) roda no Windows com Python 3.12 e Tkinter (biblioteca padrão). Iniciar no diretório do repositório com `python tools/airplay_trial_lab.py`. Para uso sem janela: `python tools/airplay_trial_lab.py --compare` ou `python tools/airplay_trial_lab.py --scenario M3 --zone pool`.

Ele **não altera o HAOS**, não emula um receptor AirPlay, não pede token e não envia música, anúncios ou dados da rede. Mostra as diferenças históricas entre `features` do TecnoHead, WiiM e Denon; gera apenas planos com três opções já existentes na RC9, para **uma zona por vez**; e registra observações do iPhone/Casa em JSON local sem nome da faixa, capa, IP ou identidade do dispositivo. Esses planos devem ser aplicados manualmente na interface autenticada do Supervisor por um operador, com backup e rollback `off` após a janela curta. A opção `apple_mediaremote_experimental` preexistente não é alterada pelo plano.

| Cenário | Máscara do anúncio | Metadados clássicos | Relay RC | Pergunta |
| --- | --- | --- | --- | --- |
| B0 | Nativa | Não | Não | Qual é o baseline atual no mesmo cartão? |
| M1 | Nativa | Não | Sim | Now Playing/SupportedCommands entregues bastam? |
| M2 | Nativa, com bits clássicos gerados pelo Shairport | Sim | Não | O formato solicitado ao emissor altera a UI? |
| M3 | Nativa, com bits clássicos gerados pelo Shairport | Sim | Sim | A combinação muda a UI? Na RC5 não se observaram eventos enriquecidos nesse modo. |

O aplicativo separa **descoberta**, **ícone**, **Now Playing recebido**, **bit 10/HK Access Control**, **conexão RC**, **ACK no RC**, **capa/faixa no Casa** e **botões no Casa**. Ícone ou ACK não equivalem a controles nativos. Som audível não é critério deste ciclo, mas uma sessão AirPlay ativa ainda é necessária para produzir metadados reais; se falhar a negociação, a ausência de capa é inconclusiva para o gate da UI. Comandos só podem ser marcados funcionais após toque no Casa e reação da origem; o campo “botões ativos” sozinho não dá D19.

Na POC RC9, o envio ao RC requer `Enable_HK_Access_Control` legítimo, conexão RC estabelecida e sessão de áudio correspondente. O teste físico na Piscina teve som, mas o usuário ainda viu “Controles não disponíveis”; **não foi capturado ACK de Now Playing/Commands**. Após o rollback, a leitura mDNS somente de campos permitidos mostrou `flags=0x4` nas duas instâncias TecnoHead, versus `0x404` no WiiM, e a opção RC estava `off`. O estado `0x4` após reinício **não prova** qual era o valor durante o ensaio, mas evidencia que ativar a flag por si só não garante o gate de HK Access. Não chamar o ensaio RC9 de prova de que a Apple rejeitou metadados efetivamente entregues.

A interseção WiiM/Denon adicionaria, entre outros, o **bit 26 (MFi)**. Na RC7, a máscara conjunta levou a `POST /auth-setup`, falha de conexão e nenhum stream. Sem implementação/autorização MFi, anunciar esse bit, o bit 51, modelo Apple ou identidade de fabricante alheio seria uma capacidade falsa; o laboratório **não oferece** esses perfis nem máscaras arbitrárias. O ícone pode depender de classificação/modelo além de `features`; o caso RC7 não isolou causalmente um único bit. O próximo desenvolvimento técnico legítimo é instrumentar a cadeia de classificação e identificar uma capacidade realmente implementável, ou um modelo TecnoHead verdadeiro, antes de qualquer novo anúncio ao iPhone. Não remover/reparear acessórios sem autorização específica.

Para repetir ensaios rapidamente no futuro, uma API interna do próprio App HAOS poderia aplicar perfis versionados na zona de teste e revertê-los automaticamente após prazo curto. **Reiniciar Shairport perde o bit 10 e a lista de controladores da implementação atual**; para comparar relay sem readopção a cada rodada seria preciso atualização de configuração em processo que preserve uma sessão legitimamente negociada, ou primeiro corrigir a persistência dos pareamentos. Esta interface Windows **não** faz isso: construir tal controle exige autenticação, limites de sessão, rollback e teste de não interferência com ARC/CEC. Nunca rodar múltiplos anúncios mutantes com a mesma identidade em paralelo, pois o cache/pareamento da Apple confundiria a atribuição do resultado.
