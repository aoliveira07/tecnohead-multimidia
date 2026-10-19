# Licenças de terceiros

O módulo usa as dependências Python declaradas em `pyproject.toml` e `requirements.txt`, além dos pacotes Alpine necessários para o App. A imagem de ensaio v1.4.17-rc.4 mantém as revisões fixadas:

- Shairport Sync `cf6998daa1876c5a8f97128a960c8afc0e731841`, com o [patch local de diagnóstico RC](../tecnohead_multimidia/patches/shairport-rc-diagnostics.patch). O patch só acrescenta marcadores constantes; não remove créditos ou cabeçalhos de fonte.
- NQPTP `ab8fb67483411640fd7f1e193889482f2421c37c`, GPL-2.0-or-later conforme o arquivo `LICENSE` upstream.
- Avahi e D-Bus dos pacotes Alpine 3.23 para o responder mDNS compartilhado; os textos de licença vêm dos próprios pacotes da distribuição.
- FFmpeg e bibliotecas de codec/transporte exigidas pela imagem base e pelo build do Shairport Sync.

O build RC4 copia `COPYING` e `LICENSES` do Shairport Sync, a licença de `tinyhttp` e a licença do NQPTP para `/usr/share/licenses/` dentro da imagem. O código e o patch usados no build permanecem rastreáveis pelo commit deste repositório. SBOM ainda não é gerado automaticamente pelo workflow; se produzido em release futuro, deverá ser publicado junto. O App não redistribui credenciais, dados do cliente ou arquivos de configuração do HA.

Referências: [Shairport Sync LICENSES](https://github.com/mikebrady/shairport-sync/tree/master/LICENSES), [NQPTP LICENSE](https://github.com/mikebrady/nqptp/blob/master/LICENSE), [Avahi](https://www.avahi.org/) e [D-Bus](https://www.freedesktop.org/wiki/Software/dbus/).

