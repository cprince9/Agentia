import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import structlog
from redis.asyncio import Redis, from_url as redis_from_url

from ...config.settings import get_settings
from ...services.event_bus import EventBus
from ..dependencies import get_redis

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{session_id}")
async def websocket_session_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """
    Real-time streaming WebSocket endpoint.
    - Replays all prior events on connection.
    - Streams live pub/sub events.
    - Sends 30-second ping heartbeats.
    - Gracefully handles client disconnection.
    """
    await websocket.accept()
    logger.info("websocket_connected", session_id=session_id)

    settings = get_settings()
    redis = redis_from_url(settings.REDIS_URL, decode_responses=False)
    event_bus = EventBus(redis=redis)

    ping_task = None
    stream_task = None

    try:
        # 1. Event Replay: Send all past events in chronological order
        history = await event_bus.get_event_history(session_id)
        for past_event in history:
            await websocket.send_text(json.dumps(past_event, default=str))

        # 2. Heartbeat task (sends ping every 30 seconds)
        async def heartbeat():
            while True:
                await asyncio.sleep(30)
                try:
                    await websocket.send_text(json.dumps({"event_type": "PING", "timestamp": "now"}))
                except Exception:
                    break

        ping_task = asyncio.create_task(heartbeat())

        # 3. Stream real-time events from Redis pub/sub
        stream_task = asyncio.create_task(event_bus.subscribe_websocket(session_id, websocket))

        # Wait on streaming task or client close
        await stream_task

    except WebSocketDisconnect:
        logger.info("websocket_client_disconnected", session_id=session_id)
    except Exception as e:
        logger.warning("websocket_session_error", session_id=session_id, error=str(e))
    finally:
        if ping_task and not ping_task.done():
            ping_task.cancel()
        if stream_task and not stream_task.done():
            stream_task.cancel()
        await redis.aclose()
        logger.info("websocket_connection_closed", session_id=session_id)
