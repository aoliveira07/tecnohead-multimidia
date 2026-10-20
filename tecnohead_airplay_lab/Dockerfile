# Reuse the exact Shairport Sync/NQPTP build already used by the paused app.
# The old app code is present in the base image but is never started here.
FROM ghcr.io/aoliveira07/tecnohead-multimidia:1.4.17-rc.9

LABEL io.hass.version="0.1.1" \
      io.hass.type="app" \
      org.opencontainers.image.description="Isolated TecnoHead AirPlay 2 Home-card laboratory"

COPY lab.py /opt/tecnohead-airplay-lab/lab.py
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
