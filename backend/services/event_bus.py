import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from redis.asyncio import Redis
from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger(__name__)


class EventBus:
    """Redis Pub/Sub and Event History service for MASDS streaming events."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def publish(
        self,
        session_id: str,
        event_type: str,
        agent_name: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Publish an event to the session channel and persist it in the Redis event history list.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        event_data = {
            "session_id": session_id,
            "event_type": event_type,
            "agent_name": agent_name,
            "payload": payload or {},
            "timestamp": timestamp,
        }

        serialized = json.dumps(event_data, default=str)
        channel = f"ws:{session_id}"
        history_key = f"session:{session_id}:events"

        try:
            # 1. Publish to real-time pub/sub channel
            await self.redis.publish(channel, serialized)

            # 2. Push to Redis list (LPUSH puts newest at index 0)
            await self.redis.lpush(history_key, serialized)

            # 3. Ensure 48 hour TTL on event list
            await self.redis.expire(history_key, 172800)
        except Exception as e:
            logger.error(
                "event_bus_publish_failed",
                session_id=session_id,
                event_type=event_type,
                error=str(e),
            )
            raise

        return event_data

    async def subscribe_websocket(self, session_id: str, websocket: WebSocket) -> None:
        """
        Subscribe to session channel and forward incoming pub/sub messages to the WebSocket.
        Gracefully handles WebSocket disconnects and cancellation.
        """
        channel_name = f"ws:{session_id}"
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel_name)

        try:
            while True:
                # Listen for messages with timeout to allow coroutine cancellation checks
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is not None and message.get("type") == "message":
                    raw_data = message.get("data")
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")

                    await websocket.send_text(raw_data)

                # Keep coroutine responsive
                await asyncio.sleep(0.01)

        except (WebSocketDisconnect, asyncio.CancelledError):
            logger.info("websocket_disconnected", session_id=session_id)
        except Exception as e:
            logger.error("websocket_stream_error", session_id=session_id, error=str(e))
        finally:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
            except Exception as close_err:
                logger.warning(
                    "pubsub_close_error",
                    session_id=session_id,
                    error=str(close_err),
                )

    async def get_event_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve persisted events for session in chronological order (oldest first).
        """
        history_key = f"session:{session_id}:events"
        try:
            # LRANGE returns [0, -1]. Since LPUSH was used, index 0 is newest.
            raw_events = await self.redis.lrange(history_key, 0, -1)
            events = []
            # Reverse to get chronological order (oldest to newest)
            for item in reversed(raw_events):
                if isinstance(item, bytes):
                    item = item.decode("utf-8")
                events.append(json.loads(item))
            return events
        except Exception as e:
            logger.error(
                "get_event_history_failed",
                session_id=session_id,
                error=str(e),
            )
            return []
