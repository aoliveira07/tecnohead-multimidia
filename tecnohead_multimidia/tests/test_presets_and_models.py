from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.presets import PROJECTOR_OFF_B64, PROJECTOR_ON_B64, default_ir_profile
from app.models import CommandFormat, IRCommand


def test_authorized_presets_are_loaded_with_safe_defaults():
    profile = default_ir_profile()
    assert profile.on.value == PROJECTOR_ON_B64
    assert profile.off.value == PROJECTOR_OFF_B64
    assert profile.on_sends == 1
    assert profile.off_sends == 2
    assert profile.off_interval_seconds == 5.0


def test_base64_prefix_is_added_only_at_transport_boundary():
    command = IRCommand(format=CommandFormat.BROADLINK_B64, value=PROJECTOR_ON_B64)
    assert command.to_ha_command() == f"b64:{PROJECTOR_ON_B64}"


def test_double_prefix_is_rejected():
    with pytest.raises(ValidationError):
        IRCommand(format=CommandFormat.BROADLINK_B64, value=f"b64:{PROJECTOR_ON_B64}")
