# Now Playing nativo no app Casa — arquitetura e limite atual

O destino `TecnoHead Cozinha` ou `TecnoHead Piscina` é o **próprio** acessório AirPlay 2 adotado no app Casa. Seu áudio passa por Shairport Sync, PCM e o `media_player` LinkPlay físico. O HomeKit Bridge é uma superfície distinta; este projeto não adiciona outro Receiver ou `media_player` para contornar o cartão “Controles não disponíveis”.

Shairport Sync 5.6 pode receber metadados e enviar comandos ao iPhone de origem. Isso comprova capacidade de controle no **backend** quando testada; não obriga o app Casa a apresentar capa, faixa, play/pause e volume no cartão do acessório. A [issue upstream #2182](https://github.com/mikebrady/shairport-sync/issues/2182) reproduz a mesma tela e descreve um ensaio com entrega/ACK de Now Playing sem liberação do cartão. O relato sugere classificação Apple como obstáculo, mas não é prova física da instalação TecnoHead nem documentação pública de API Apple.

Nesta etapa, a arquitetura de produção permanece igual à v1.4.16 publicada: sem mudança de identidade, pairing, HomeKit Bridge, ARC/CEC, LinkPlay ou volume. A sonda opcional do branch `experiment/mediaremote-now-playing` é somente para diagnóstico de `ssnc/copl` por zona. Ela fica desativada por padrão e não preenche o cartão Casa.

Critério de conclusão: D16–D19 somente PASSAM com captura real do **mesmo** acessório Cozinha e Piscina no iPhone, metadados e controles visíveis, toque em play/pause/volume e resposta física observada. Até lá, o estado da correção da tela é **NÃO TESTADO após a mudança**; a captura anterior da Cozinha mostra a falha de baseline. Não criar fallback sem decisão do usuário.

Consulte [APPLE_MEDIAREMOTE_RESEARCH.md](APPLE_MEDIAREMOTE_RESEARCH.md) para evidências/hipóteses e [MEDIAREMOTE_D01_D24.md](MEDIAREMOTE_D01_D24.md) para o checklist de homologação.
