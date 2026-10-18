from __future__ import annotations

import pytest

from app.core.ha_client import HomeAssistantClient
from app.settings import Settings


@pytest.mark.asyncio
async def test_call_service_uses_authenticated_websocket_target() -> None:
    client = HomeAssistantClient(Settings(supervisor_token="test-token"))
    captured: dict[str, object] = {}

    async def fake_websocket_command(command: dict[str, object]) -> dict[str, bool]:
        captured.update(command)
        return {"success": True}

    client.websocket_command = fake_websocket_command  # type: ignore[method-assign]

    result = await client.call_service(
        "media_player",
        "volume_set",
        entity_id="media_player.kitchen",
        data={"volume_level": 0.2},
    )

    assert result == {"success": True}
    assert captured == {
        "type": "call_service",
        "domain": "media_player",
        "service": "volume_set",
        "target": {"entity_id": "media_player.kitchen"},
        "service_data": {"volume_level": 0.2},
    }
