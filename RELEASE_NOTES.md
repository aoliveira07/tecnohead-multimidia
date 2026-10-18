# Release notes

## v1.3.0 — módulo Áudio Multiroom

Esta release preserva Cinema/TV/IR/clima/luzes/MQTT da v1.2 e adiciona o painel de áudio para zonas por área. Volume, mudo, fontes e agrupamento só usam entidades `media_player` reais do Home Assistant; não há cliente LinkPlay proprietário e HDMI ARC da Piscina não é alterado automaticamente.

O HAOS real consultado em 18/10/2026 não apresentou integração LinkPlay nem o `media_player` do amplificador novo da Piscina. Consequentemente, a ponte AirPlay 2 virtual não foi iniciada, nenhum destino Apple foi anunciado e nenhum teste físico de áudio foi alegado. O desbloqueio requer o modelo/entidade do amplificador atual e, depois, iPhone para a homologação G2–G5.

Testes automatizados desta alteração: `15 passed`, Ruff e sintaxe JavaScript passaram. A instalação/atualização e os testes físicos permanecem uma etapa posterior ao commit/release.

## v1.2.11

Correção operacional observada no comissionamento: uma cena Cinema com degradação opcional (por exemplo, posição de aleta não confirmada) agora permanece logicamente ativa e executa o temporizador cancelável de iluminação. O intervalo padrão entre as duas chamadas independentes de desligamento IR foi ajustado para 4,0 s, mantendo a validação por entidade `remote` do Home Assistant e sem `num_repeats`.

O teste físico do projetor, das luzes, do telão e das cenas continua dependendo da observação manual; a API aceita pela integração não é tratada como confirmação física.

## v1.2.10

## v1.2.10

Revisão operacional para comissionamento: validação do emissor sem transmissão, degradação controlada de equipamentos opcionais e área sugerida no MQTT Discovery. Nenhuma chamada física é realizada na instalação durante a atualização.

Esta release corrige a entrada do contêiner para carregar o `SUPERVISOR_TOKEN` pelo ambiente do Home Assistant. Ela mantém as correções de empacotamento e MQTT das versões anteriores. O BroadLink existente continua sendo responsabilidade da integração do Home Assistant; o App não fala diretamente com o equipamento.

Antes de marcar a instalação como homologada, o instalador deve executar o checklist físico de [TEST_PLAN.md](docs/TEST_PLAN.md), registrar a versão instalada e anexar capturas reais. Sem acesso ao HAOS e aos equipamentos, a release deve ser tratada como instalável e parcialmente testada.
## v1.2.8

Correção operacional do editor Ingress: o polling de diagnóstico não sobrescreve mais um cadastro de área enquanto ele está sendo preenchido.
## v1.2.9

Alinha a versão exibida no painel e nos metadados internos com a versão instalada pelo catálogo HAOS.
