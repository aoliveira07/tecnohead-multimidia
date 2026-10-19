# AirPlay 2 build pinned to upstream revisions. The runtime remains a single
# Home Assistant App; no host-side Docker Compose or sidecar is required.
FROM alpine:3.23.4 AS nqptp-build

ARG NQPTP_COMMIT=ab8fb67483411640fd7f1e193889482f2421c37c

RUN apk add --no-cache \
      autoconf \
      automake \
      build-base \
      git \
      libtool \
      linux-headers \
      musl-dev \
      pkgconf

RUN git clone --filter=blob:none https://github.com/mikebrady/nqptp.git /src/nqptp \
    && cd /src/nqptp \
    && git fetch --depth 1 origin "${NQPTP_COMMIT}" \
    && git checkout --detach "${NQPTP_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${NQPTP_COMMIT}"

RUN cd /src/nqptp \
    && autoreconf -fi \
    && ./configure --prefix=/usr \
    && make -j"$(getconf _NPROCESSORS_ONLN)" \
    && rm -rf /tmp/nqptp-install \
    && make DESTDIR=/tmp/nqptp-install install \
    && mkdir -p /out \
    && find /tmp/nqptp-install -type f -name nqptp -perm -111 -exec cp {} /out/nqptp \;


FROM alpine:3.23.4 AS shairport-build

ARG SHAIRPORT_SYNC_COMMIT=cf6998daa1876c5a8f97128a960c8afc0e731841

RUN apk add --no-cache \
      alsa-lib-dev \
      autoconf \
      automake \
      avahi-dev \
      build-base \
      dbus-dev \
      ffmpeg-dev \
      git \
      glib-dev \
      libconfig-dev \
      libgcrypt-dev \
      libplist-dev \
      libplist-util \
      libtool \
      linux-headers \
      libsodium-dev \
      openssl-dev \
      pkgconf \
      popt-dev \
      xxd

RUN git clone --filter=blob:none https://github.com/mikebrady/shairport-sync.git /src/shairport-sync \
    && cd /src/shairport-sync \
    && git fetch --depth 1 origin "${SHAIRPORT_SYNC_COMMIT}" \
    && git checkout --detach "${SHAIRPORT_SYNC_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${SHAIRPORT_SYNC_COMMIT}"

COPY patches/shairport-rc-diagnostics.patch /tmp/shairport-rc-diagnostics.patch

RUN cd /src/shairport-sync \
    && git apply --check /tmp/shairport-rc-diagnostics.patch \
    && git apply /tmp/shairport-rc-diagnostics.patch

RUN cd /src/shairport-sync \
    && autoreconf -fi \
    && ./configure \
      --prefix=/usr \
      --sysconfdir=/etc \
      --with-alsa \
      --with-avahi \
      --with-airplay-2 \
      --with-dbus-interface \
      --with-mpris-interface \
      --with-metadata \
      --with-metadata-pipe \
      --with-ssl=openssl \
      --with-pipe \
      --with-stdout \
    && make -j"$(getconf _NPROCESSORS_ONLN)" \
    && rm -rf /tmp/shairport-install \
    && make DESTDIR=/tmp/shairport-install install \
    && mkdir -p /out \
    && find /tmp/shairport-install -type f -name shairport-sync -perm -111 -exec cp {} /out/shairport-sync \;


FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION=1.4.17-rc.4
ARG BUILD_ARCH=local
ARG NQPTP_COMMIT=ab8fb67483411640fd7f1e193889482f2421c37c
ARG SHAIRPORT_SYNC_COMMIT=cf6998daa1876c5a8f97128a960c8afc0e731841

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.source="https://github.com/aoliveira07/tecnohead-multimidia" \
  org.opencontainers.image.description="TecnoHead Multimídia with pinned Shairport Sync AirPlay 2 and NQPTP"

RUN apk add --no-cache \
      alsa-lib \
      avahi \
      avahi-libs \
      ca-certificates \
      dbus \
      dbus-libs \
      ffmpeg \
      glib \
      libconfig \
      libgcrypt \
      libplist \
      libstdc++ \
      libuuid \
      libcrypto3 \
      libssl3 \
      libsodium \
      popt \
      python3 \
      py3-pip

COPY --from=nqptp-build /out/nqptp /usr/local/bin/nqptp
COPY --from=shairport-build /out/shairport-sync /usr/local/bin/shairport-sync
COPY --from=nqptp-build /src/nqptp/LICENSE /usr/share/licenses/nqptp/LICENSE
COPY --from=shairport-build /src/shairport-sync/COPYING /usr/share/licenses/shairport-sync/COPYING
COPY --from=shairport-build /src/shairport-sync/LICENSES /usr/share/licenses/shairport-sync/LICENSES
COPY --from=shairport-build /src/shairport-sync/tinyhttp/LICENSE /usr/share/licenses/shairport-sync/tinyhttp-LICENSE

COPY requirements.txt /requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages -r /requirements.txt

COPY app /app/app
COPY web /app/web
COPY airplay_volume_hook.py /usr/local/bin/tecnohead-airplay-volume-hook
COPY run.sh /run.sh
RUN chmod +x /run.sh /usr/local/bin/tecnohead-airplay-volume-hook

WORKDIR /app
ENV PYTHONPATH=/app \
    APP_VERSION="${BUILD_VERSION}" \
    NQPTP_COMMIT="${NQPTP_COMMIT}" \
    SHAIRPORT_SYNC_COMMIT="${SHAIRPORT_SYNC_COMMIT}"

CMD ["/run.sh"]
