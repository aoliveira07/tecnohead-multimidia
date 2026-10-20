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

The lab does **not** offer arbitrary `features` masks, MFi authentication,
commercial/Apple model spoofing, or a HomePod/WiiM/Denon persona. The separate
`advertisement` option provides four restricted, lab-only variants:

| Advertisement | Own TecnoHead model | Classic metadata bits 15–17 added |
| --- | --- | --- |
| `stock` | No | No |
| `tecnohead_model` | Yes | No |
| `classic_bits` | No | Yes |
| `tecnohead_model_classic_bits` | Yes | Yes |

The `classic_bits` variants retain bit 50 (binary-plist Now Playing) and only
advertise formats the receiver parses. AirPlay may still choose a single format;
these variants do **not** guarantee two metadata streams. They never set bit 26
or 51, which published protocol research associates with MFi. A speaker icon
is a separate observation from a working Home card. The RC relay is
experimental: RTSP 2xx responses do not prove Home UI success. Use `M1` with
one advertisement at a time for the combined classification/relay experiment.
Return to `B0` + `stock` after testing.

Only counters and field *presence* are logged. Never print track names,
artwork, payloads, audio, IPs or pairing details. Review the logs after each
test, then compare the same lab card in Apple Home. On completion stop the lab
app; it is configured not to start at boot. Restore the original TecnoHead
Multimídia app only by enabling its own start switch and pressing Start.
