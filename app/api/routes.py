import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.monitor import MonitorService

router = APIRouter(prefix="/api", tags=["monitor"])
monitor = MonitorService()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/monitor/start")
async def start_monitor() -> dict:
    await monitor.start()
    return {"status": "started", "state": monitor.state().model_dump()}


@router.post("/monitor/stop")
async def stop_monitor() -> dict:
    await monitor.stop()
    return {"status": "stopped", "state": monitor.state().model_dump()}


@router.get("/monitor/state")
def monitor_state() -> dict:
    return monitor.state().model_dump()


@router.get("/risk/top")
def top_risk() -> list[dict]:
    return [item.model_dump(mode="json") for item in monitor.risk_results()[:50]]


@router.get("/gain/top")
def top_gain_profiles() -> list[dict]:
    return [item.model_dump(mode="json") for item in monitor.gain_results()[:50]]


@router.get("/picks/top")
def top_potential_picks(
    limit: int = 20,
    min_score: int | None = None,
    min_risk_reward: float | None = None,
) -> list[dict]:
    rows = monitor.potential_picks(
        limit=limit,
        min_score=min_score,
        min_risk_reward=min_risk_reward,
    )
    return [item.model_dump(mode="json") for item in rows]


@router.get("/signals/unified")
async def unified_signals() -> list[dict]:
    rows = await monitor.unified_signals()
    return [row.model_dump(mode="json") for row in rows]


@router.get("/stream")
async def stream_events() -> StreamingResponse:
    async def event_generator():
        while True:
            payload = {"state": monitor.state().model_dump(), "events": monitor.event_snapshot()[:20]}
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
