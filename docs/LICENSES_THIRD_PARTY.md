# Licenças de terceiros

O módulo usa as dependências Python declaradas em `pyproject.toml` e `requirements.txt`, além dos pacotes Alpine necessários para o App. A imagem v1.4.5 inclui e fixa:

- Shairport Sync `cf6998daa1876c5a8f97128a960c8afc0e731841`, com os avisos de licença distribuídos pelo upstream.
- NQPTP `ab8fb67483411640fd7f1e193889482f2421c37c`, GPL-2.0-or-later conforme o arquivo `LICENSE` upstream.
- Avahi e D-Bus dos pacotes Alpine 3.23 para o responder mDNS compartilhado; os textos de licença vêm dos próprios pacotes da distribuição.
- FFmpeg e bibliotecas de codec/transporte exigidas pela imagem base e pelo build do Shairport Sync.

As fontes e avisos devem permanecer acessíveis no release junto com o SBOM gerado pelo workflow quando disponível. O App não redistribui credenciais, dados do cliente ou arquivos de configuração do HA.

Referências: [Shairport Sync LICENSES](https://github.com/mikebrady/shairport-sync/tree/master/LICENSES), [NQPTP LICENSE](https://github.com/mikebrady/nqptp/blob/master/LICENSE), [Avahi](https://www.avahi.org/) e [D-Bus](https://www.freedesktop.org/wiki/Software/dbus/).

