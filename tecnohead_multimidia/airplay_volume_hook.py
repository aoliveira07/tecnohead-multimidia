#!/usr/bin/python3
"""Forward Shairport Sync's AirPlay dB volume to the App socket."""

from __future__ import annotations

import math
import socket
import sys


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        return 0
    socket_path, value = argv[1], argv[2].strip()
    try:
        numeric = float(value)
    except ValueError:
        return 0
    if not math.isfinite(numeric) or numeric < -144.0 or numeric > 0.1:
        return 0
    client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        client.sendto(value.encode("ascii", errors="ignore"), socket_path)
    except OSError:
        # A restart must never block or terminate Shairport Sync. The next
        # AirPlay event will be handled after the App is ready again.
        return 0
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
