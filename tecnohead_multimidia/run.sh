#!/command/with-contenv bashio
set -eu
# The protected audio-stream URL contains a short-lived capability token.
# Uvicorn's access log would print that URL verbatim in the HAOS App logs.
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${INGRESS_PORT:-18199}" --no-access-log
