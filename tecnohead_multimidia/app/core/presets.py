"""Generic presets explicitly authorized by the TecnoHead handoff.

These are the only IR payloads shipped in source. Client-learned values remain in
the private /data configuration file and are never written to diagnostics.
"""

from app.models import CommandFormat, IRCommand, IRProfile

PROJECTOR_ON_B64 = (
    "JgBYAAABJ5MUEhI3ExITEhM3EzYUERMSFDYTEhM3EzYUERQREzcTNxITEzcTERMSExIUERMSFBEUNhQRFDYTNhQ2FDYTNxM2EwAFIwABJkoTAAxXAAEnShQADQU="
)
PROJECTOR_OFF_B64 = (
    "JgCAAAABKJIVEBU1FBEUERQ1FTUVEBUQFTUUERQ1FTUVEBUQFTUUNRURFDUVNRQ1FRAVNRMSFRAVNRITFBEUERQ1ExIVNRM3EgAFJQABKUcVAAxXAAEoSBMADFkAASdJEwAMWQABJ0kTAAxZAAEoSRIADFkAASdKEwAMWQABJ0kTAA0FAAAAAAAAAAA="
)


def default_ir_profile() -> IRProfile:
    return IRProfile(
        on=IRCommand(format=CommandFormat.BROADLINK_B64, value=PROJECTOR_ON_B64),
        off=IRCommand(format=CommandFormat.BROADLINK_B64, value=PROJECTOR_OFF_B64),
        on_sends=1,
        off_sends=2,
        off_interval_seconds=4.0,
    )


def restore_ir_profile(remote_entity_id: str | None = None) -> IRProfile:
    profile = default_ir_profile()
    profile.remote_entity_id = remote_entity_id
    return profile
