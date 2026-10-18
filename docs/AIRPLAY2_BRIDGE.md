# Ponte AirPlay 2 virtual

## Estado desta versão

A ponte Shairport Sync/NQPTP não foi iniciada nem anunciada nesta instalação. O motivo é objetivo: não há destino físico LinkPlay canônico para receber o PCM e não há modelo/codec/firmware do amplificador novo da Piscina confirmados. Publicar nomes mDNS agora produziria uma falsa homologação.

## Arquitetura prevista, sob pré-condições

- Shairport Sync upstream com suporte AirPlay 2 real, revisão fixada e licença registrada.
- Uma identidade estável por zona: `TecnoHead Cozinha` e `TecnoHead Piscina`.
- Portas RAOP distintas, uma instância NQPTP compartilhada e um registrador mDNS compatível, sem iniciar um segundo Avahi global.
- Áudio PCM isolado por sessão, ponte local protegida e entrega ao player LinkPlay somente após comprovar URL, codec, buffering e parada.
- Persistência das identidades e pareamentos no volume privado do App; nenhum stream é retomado automaticamente após reinício.

Os requisitos de host networking, IPC, D-Bus/mDNS e portas só serão adicionados ao metadata do App depois de um destino físico confirmado e de uma verificação de conflito no HAOS. Não há sidecar, Compose manual ou alteração do serviço global do host nesta release.

## Critério de sucesso

O iPhone encontrar o nome não é suficiente. É necessário provar handshake AirPlay 2, receber PCM, entregar ao amplificador, ouvir som em cada zona, parar sem áudio fantasma e medir latência/sincronia. A ponte só pode avançar para a Piscina depois da prova na Cozinha.

Referências: [AIRPLAY2.md](https://github.com/mikebrady/shairport-sync/blob/master/AIRPLAY2.md), [múltiplas instâncias](https://github.com/mikebrady/shairport-sync/blob/master/ADVANCED%20TOPICS/RunningMultipleInstances.md) e [integração ao app Casa](https://github.com/mikebrady/shairport-sync/blob/master/ADDINGTOHOME.md).

