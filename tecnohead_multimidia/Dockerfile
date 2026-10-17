FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION=1.2.10
ARG BUILD_ARCH=local

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

RUN apk add --no-cache python3 py3-pip

COPY requirements.txt /requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages -r /requirements.txt

COPY app /app/app
COPY web /app/web
COPY run.sh /run.sh
RUN chmod +x /run.sh

WORKDIR /app
ENV PYTHONPATH=/app

CMD ["/run.sh"]
