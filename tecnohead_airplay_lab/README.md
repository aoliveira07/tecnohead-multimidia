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
`advertisement` option provides five restricted, lab-only variants:

| Advertisement | Own TecnoHead model | Classic metadata bits 15–17 added | Bit 50 advertised |
| --- | --- | --- | --- |
| `stock` | No | No | Stock |
| `tecnohead_model` | Yes | No | Stock |
| `classic_bits` | No | Yes | Stock |
| `tecnohead_model_classic_bits` | Yes | Yes | Stock |
| `tecnohead_model_classic_bits_no_bit50` | Yes | Yes | No |

The v0.1.11 `no_bit50` variant is a lab-only, opt-in *reduction* of the
current combined announcement: it clears only advertised feature bit 50,
without disabling Shairport's internal plist parser or adding vendor features.
It must be compared directly with `tecnohead_model_classic_bits` in M1. The
sender may stop providing rich metadata when bit 50 is absent; record this
separately from the Casa card result. The other `classic_bits` variants retain
bit 50 (binary-plist Now Playing) and only advertise formats the receiver
parses. AirPlay may still choose a single format;
these variants do **not** guarantee two metadata streams. They never set bit 26
or 51, which published protocol research associates with MFi. A speaker icon
is a separate observation from a working Home card. The RC relay is
experimental: RTSP 2xx responses do not prove Home UI success. Use `M1` with
one advertisement at a time for the combined classification/relay experiment.
Return to `B0` + `stock` after testing.

The independent `network_mode` option defaults to `ipv4_only`, preserving the
current explicit IPv4 listener and Avahi IPv4-only advertisement. The
experimental `dual_stack` option removes only Shairport Sync's single-address
bind and enables Avahi IPv6/AAAA publication. It does not change the Lab's
identity, feature mask, metadata profile, RC relay or audio output. Confirm an
AAAA record and an actual IPv6 AirPlay session before interpreting a Home-card
test. A missing AAAA record or failed connection makes the experiment
inconclusive; restore `ipv4_only` and restart the Lab. Do not apply this
option to the production Cozinha/Piscina receivers.

The independent `txt_variant` option (v0.1.7) compares truthful, Lab-only
AirPlay discovery fields. Each choice changes the `_airplay._tcp` TXT record
and the corresponding `GET /info` TXT payload, leaving the selected metadata
profile, feature mask and IPv4/IPv6 mode untouched:

| TXT variant | Difference from stock |
| --- | --- |
| `stock` | No extra field; default and rollback setting |
| `own_manufacturer` | `manufacturer=TecnoHead` |
| `own_manufacturer_serial` | Own manufacturer and stable `THLAB-…` serial derived from the Lab's own ID |
| `required_sender_zero` | `rsf=0x0`, no extra sender capability requested |
| `without_fex` | Omits the optional `fex` field; retains the actual `features` mask |

These are protocol probes, not a claim that the icon or Casa card will change.
Test one variant at a time on the **same Lab accessory**, first checking
AirPlay connection, then the Casa card during Apple Music playback. If a
variant prevents connection, restore `stock` immediately. Do not interpret
an mDNS record, an RTSP acknowledgement, or an icon change as Home control
success; only visible metadata and a functional pause/volume control count.
No variant includes an Apple/MFi certificate or advertises MFi authentication.

The independent `info_variant` option (v0.1.8) isolates one difference in
the endpoint's `GET /info` response. `stock` retains Shairport Sync's original
plist. `omit_audio_only_ui` removes only the existing
`playbackCapabilities.supportsUIForAudioOnlyContent=false` key; it does not
set that capability to `true`, remove the other `playbackCapabilities` keys,
change TXT/`features`/`statusFlags`, or change the AirPlay identity. First
verify the response field difference and AirPlay connection, then inspect
the same Lab card in Casa during playback. If the card remains empty, restore
`stock`; absence of this key is not evidence that the UI will be enabled.

The v0.1.9 `omit_playback_capabilities` variant removes the **entire**
`playbackCapabilities` dictionary from `GET /info`, matching one structural
difference seen in the WiiM/Denon comparison. This is a separate experiment,
not a claim of those products' identity or capabilities. All other response
fields and Lab settings stay unchanged. After testing, restore `stock`;
AirPlay connectivity and a native Casa card must be checked independently.

Lab v0.1.10 adds an administrator-only, bounded command probe for the
**audio/PTP session event channel**, separate from the RC Now Playing relay.
It uses the Supervisor's existing stdin action; it opens no HTTP port and
does not create another HomeKit accessory. While Apple Music is playing
**only on this Lab**, run `hassio.app_stdin` in Home Assistant Developer
Tools with `app: b622e1ca_tecnohead_airplay_lab` and
`input: {command: pause}`; wait at least two seconds, then use
`input: {command: play}`. The Lab accepts no other commands or extra JSON
fields, and declines a command if it has seen no recent PCM. A D-Bus reply
and the Shairport channel/POST markers are transport evidence only: verify
the iPhone actually pauses/resumes. The Lab still discards audio; do not
interpret a missing sound change as failure. All output is sanitized.

Only counters and field *presence* are logged. Never print track names,
artwork, payloads, audio, IPs or pairing details. Review the logs after each
test, then compare the same lab card in Apple Home. On completion stop the lab
app; it is configured not to start at boot. Restore the original TecnoHead
Multimídia app only by enabling its own start switch and pressing Start.
