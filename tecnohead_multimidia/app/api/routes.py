from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.core.audio import AudioActionError
from app.core.discovery import AreaValidationError
from app.core.ha_client import HomeAssistantError
from app.core.ir_transport import IRSequenceError, IRSequenceUncertain
from app.models import (
    AreaProfileUpdate,
    AudioCommandRequest,
    AudioGroupRequest,
    AudioMuteRequest,
    AudioPlaybackRequest,
    AudioSourceRequest,
    AudioVolumeRequest,
    IRTestRequest,
    ModeRequest,
    MultiroomUpdate,
    RestorePresetRequest,
)
from app.runtime import Runtime

router = APIRouter(prefix="/api")


def runtime_from(request: Request) -> Runtime:
    return request.app.state.runtime


def translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, (AreaValidationError, ValueError)):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, AudioActionError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, IRSequenceUncertain):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, (IRSequenceError, HomeAssistantError)):
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=500, detail="falha interna do TecnoHead Multimídia")


@router.get("/health")
async def health(request: Request):
    runtime = runtime_from(request)
    return {"ok": True, "app_version": runtime.settings.app_version}


@router.get("/status")
async def status(request: Request):
    return await runtime_from(request).status()


@router.get("/areas")
async def areas(request: Request, refresh: bool = Query(default=False)):
    runtime = runtime_from(request)
    try:
        return await runtime.discover(refresh=refresh)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.get("/areas/{area_id}")
async def area(area_id: str, request: Request):
    runtime = runtime_from(request)
    try:
        profile = await runtime.get_profile(area_id)
        descriptors = await runtime.discover()
    except Exception as exc:
        raise translate_error(exc) from exc
    descriptor = next((item for item in descriptors if item.area_id == area_id), None)
    if descriptor is None:
        raise HTTPException(status_code=404, detail="Área não encontrada no Home Assistant")
    return {**descriptor.model_dump(mode="json"), "profile": profile.model_dump(mode="json")}


@router.put("/areas/{area_id}")
async def save_area(area_id: str, payload: AreaProfileUpdate, request: Request):
    try:
        profile = await runtime_from(request).save_profile(area_id, payload)
        return profile.model_dump(mode="json")
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/areas/{area_id}/mode")
async def request_mode(area_id: str, payload: ModeRequest, request: Request):
    try:
        result = await runtime_from(request).request_mode(area_id, payload.mode, reason="panel")
        return result
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/areas/{area_id}/wait")
async def wait_area(area_id: str, request: Request):
    await runtime_from(request).wait_area(area_id)
    return await runtime_from(request).status()


@router.post("/areas/{area_id}/ir/test")
async def test_ir(area_id: str, payload: IRTestRequest, request: Request):
    try:
        return await runtime_from(request).test_ir(area_id, payload.direction, payload.confirmed)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.get("/areas/{area_id}/ir/check")
async def check_ir_entity(area_id: str, request: Request):
    try:
        return await runtime_from(request).check_ir_entity(area_id)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/areas/{area_id}/ir/restore")
async def restore_ir(area_id: str, payload: RestorePresetRequest, request: Request):
    try:
        profile = await runtime_from(request).restore_presets(area_id, payload.confirmed)
        return profile.model_dump(mode="json")
    except Exception as exc:
        raise translate_error(exc) from exc


@router.get("/events")
async def events(request: Request, limit: int = Query(default=100, ge=1, le=300)):
    runtime = runtime_from(request)
    return [event.model_dump(mode="json") for event in list(runtime.events)[-limit:]]


@router.get("/diagnostics")
async def diagnostics(request: Request):
    return await runtime_from(request).diagnostics()


@router.get("/audio")
async def audio(request: Request):
    try:
        return await runtime_from(request).audio_payload()
    except Exception as exc:
        raise translate_error(exc) from exc


@router.get("/audio/airplay/{zone_id}/stream")
async def audio_airplay_stream(zone_id: str, request: Request, token: str = Query(min_length=16, max_length=256)):
    """Serve only the short-lived PCM-to-MP3 stream for a running endpoint.

    The URL is generated internally after Shairport Sync receives audio. It is
    intentionally not listed in the UI or diagnostics, and the random token
    prevents an unrelated LAN client from opening a zone stream by guessing a
    path. There is no arbitrary URL proxy here.
    """

    runtime = runtime_from(request)
    if not runtime.airplay:
        raise HTTPException(status_code=404, detail="ponte AirPlay não está disponível")
    try:
        stream = runtime.airplay.stream(zone_id, token)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="stream AirPlay inexistente ou token expirado") from exc
    return StreamingResponse(
        stream,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.put("/audio")
async def save_audio(payload: MultiroomUpdate, request: Request):
    try:
        config = await runtime_from(request).save_audio(payload)
        return config.model_dump(mode="json")
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/audio/zones/{zone_id}/volume")
async def audio_volume(zone_id: str, payload: AudioVolumeRequest, request: Request):
    try:
        return await runtime_from(request).audio_set_volume(zone_id, payload)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/audio/zones/{zone_id}/mute")
async def audio_mute(zone_id: str, payload: AudioMuteRequest, request: Request):
    try:
        return await runtime_from(request).audio_set_mute(zone_id, payload)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/audio/zones/{zone_id}/source")
async def audio_source(zone_id: str, payload: AudioSourceRequest, request: Request):
    try:
        return await runtime_from(request).audio_select_source(zone_id, payload)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/audio/zones/{zone_id}/playback")
async def audio_playback(zone_id: str, payload: AudioPlaybackRequest, request: Request):
    try:
        return await runtime_from(request).audio_playback(zone_id, payload)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/audio/group/join")
async def audio_join(payload: AudioGroupRequest, request: Request):
    try:
        return await runtime_from(request).audio_join(payload)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/audio/group/share-pool-to-kitchen")
async def audio_share_pool_to_kitchen(payload: AudioCommandRequest, request: Request):
    try:
        return await runtime_from(request).audio_share_pool_to_kitchen(payload)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.post("/audio/group/{zone_id}/unjoin")
async def audio_unjoin(zone_id: str, payload: AudioCommandRequest, request: Request):
    try:
        return await runtime_from(request).audio_unjoin(zone_id, payload)
    except Exception as exc:
        raise translate_error(exc) from exc


@router.get("/manual")
async def manual():
    return {
        "repository": "https://github.com/aoliveira07/tecnohead-multimidia",
        "install": "Settings → Apps → App Store → Repositories → adicionar a URL do repositório",
        "safety": "IR confirma somente processamento pelo Home Assistant; o projetor não fornece feedback físico pelo IR.",
    }
