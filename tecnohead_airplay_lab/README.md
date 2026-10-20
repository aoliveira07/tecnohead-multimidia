# TecnoHead AirPlay Lab

One disposable, independently paired AirPlay 2 receiver for investigating the
native Apple Home card. It produces no physical sound and has no Home Assistant
Core/MQTT/LinkPlay integration. Never select an existing Cozinha/Piscina/WiiM/
Denon identity as its device ID. The laboratory identity persists in the app's
`/data` and can be removed from Apple Home without affecting the old devices.

The `profile` option is applied on app restart:

| Profile | Classic metadata/artwork request | RC Now Playing relay |
| --- | --- | --- |
| B0 | No | No |
| M1 | No | Yes, only after legitimate RC connection |
| M2 | Yes | No |
| M3 | Yes | Yes, only after legitimate RC connection |

The lab uses stock Shairport feature negotiation for these profiles; it does
**not** offer arbitrary `features` masks, MFi authentication, model spoofing,
or a HomePod/WiiM/Denon persona. A speaker icon is a separate observation from
a working Home card. The RC relay is experimental: ACKs do not prove UI success.

Only counters and field *presence* are logged. Never print track names,
artwork, payloads, audio, IPs or pairing details. Review the logs after each
test, then compare the same lab card in Apple Home. On completion stop the lab
app; it is configured not to start at boot. Restore the original TecnoHead
Multimídia app only by enabling its own start switch and pressing Start.
