# Rebuild only Shairport in the disposable Lab with sanitized RC lifecycle markers.
# The pinned production image remains the runtime base (including NQPTP), but
# the production App itself is never started or updated by this Dockerfile.
FROM alpine:3.23.4 AS shairport-lab-build

ARG SHAIRPORT_SYNC_COMMIT=cf6998daa1876c5a8f97128a960c8afc0e731841
ARG TECNOHEAD_PATCH_COMMIT=18deeb5637c18459ca29acb38c75550fe2c81161

RUN apk add --no-cache \
      alsa-lib-dev autoconf automake avahi-dev build-base dbus-dev ffmpeg-dev \
      git glib-dev libconfig-dev libgcrypt-dev libplist-dev libplist-util \
      libtool linux-headers libsodium-dev openssl-dev pkgconf popt-dev xxd

RUN git clone --filter=blob:none https://github.com/mikebrady/shairport-sync.git /src/shairport-sync \
    && cd /src/shairport-sync \
    && git fetch --depth 1 origin "${SHAIRPORT_SYNC_COMMIT}" \
    && git checkout --detach "${SHAIRPORT_SYNC_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${SHAIRPORT_SYNC_COMMIT}"

RUN git clone --filter=blob:none https://github.com/aoliveira07/tecnohead-multimidia.git /src/tecnohead-patches \
    && cd /src/tecnohead-patches \
    && git fetch --depth 1 origin "${TECNOHEAD_PATCH_COMMIT}" \
    && git checkout --detach "${TECNOHEAD_PATCH_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${TECNOHEAD_PATCH_COMMIT}"

COPY patches/shairport-rc-gate-diagnostics.patch /tmp/shairport-rc-gate-diagnostics.patch
COPY patches/shairport-rc-lifecycle-diagnostics.patch /tmp/shairport-rc-lifecycle-diagnostics.patch
COPY patches/shairport-rc-close-diagnostics.patch /tmp/shairport-rc-close-diagnostics.patch
COPY patches/shairport-lab-advertisement.patch /tmp/shairport-lab-advertisement.patch
COPY patches/shairport-lab-txt-matrix.patch /tmp/shairport-lab-txt-matrix.patch
COPY patches/shairport-lab-info-variant.patch /tmp/shairport-lab-info-variant.patch

RUN cd /src/shairport-sync \
    && git apply /src/tecnohead-patches/tecnohead_multimidia/patches/shairport-rc-diagnostics.patch \
    && git apply /src/tecnohead-patches/tecnohead_multimidia/patches/shairport-feature-comparison.patch \
    && git apply /src/tecnohead-patches/tecnohead_multimidia/patches/shairport-rc-now-playing-forward.patch \
    && git apply --check /tmp/shairport-rc-gate-diagnostics.patch \
    && git apply /tmp/shairport-rc-gate-diagnostics.patch \
    && git apply --check /tmp/shairport-rc-lifecycle-diagnostics.patch \
    && git apply /tmp/shairport-rc-lifecycle-diagnostics.patch \
    && git apply --check /tmp/shairport-rc-close-diagnostics.patch \
    && git apply /tmp/shairport-rc-close-diagnostics.patch \
    && git apply --check /tmp/shairport-lab-advertisement.patch \
    && git apply /tmp/shairport-lab-advertisement.patch \
    && git apply --check /tmp/shairport-lab-txt-matrix.patch \
    && git apply /tmp/shairport-lab-txt-matrix.patch \
    && git apply --check /tmp/shairport-lab-info-variant.patch \
    && git apply /tmp/shairport-lab-info-variant.patch

RUN cd /src/shairport-sync \
    && autoreconf -fi \
    && ./configure --prefix=/usr --sysconfdir=/etc --with-alsa --with-avahi \
      --with-airplay-2 --with-dbus-interface --with-mpris-interface \
      --with-metadata --with-metadata-pipe --with-ssl=openssl --with-pipe --with-stdout \
    && make -j"$(getconf _NPROCESSORS_ONLN)" \
    && make DESTDIR=/tmp/shairport-install install \
    && mkdir -p /out \
    && find /tmp/shairport-install -type f -name shairport-sync -perm -111 -exec cp {} /out/shairport-sync \;

FROM ghcr.io/aoliveira07/tecnohead-multimidia:1.4.17-rc.9

LABEL io.hass.version="0.1.9" \
      io.hass.type="app" \
      org.opencontainers.image.description="Isolated TecnoHead AirPlay 2 Home-card laboratory"

COPY --from=shairport-lab-build /out/shairport-sync /usr/local/bin/shairport-sync
COPY lab.py /opt/tecnohead-airplay-lab/lab.py
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
