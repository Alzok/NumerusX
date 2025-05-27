import socketio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class SocketManager:
    """Manages Socket.IO server and emits events."""
    _sio_server: Optional[socketio.AsyncServer] = None
    _sio_app: Optional[socketio.ASGIApp] = None

    def __init__(self, cors_allowed_origins="*"):
        if SocketManager._sio_server is None:
            SocketManager._sio_server = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins=cors_allowed_origins,
                # logger=True, # Enable for socketio detailed logs
                # engineio_logger=True # Enable for engineio detailed logs
            )
            SocketManager._sio_app = socketio.ASGIApp(SocketManager._sio_server)
            self._register_default_handlers()
            logger.info(f"Socket.IO AsyncServer initialized with CORS: {cors_allowed_origins}")

    @property
    def app(self) -> Optional[socketio.ASGIApp]:
        return SocketManager._sio_app

    @property
    def sio(self) -> Optional[socketio.AsyncServer]:
        return SocketManager._sio_server

    def _register_default_handlers(self):
        if not self.sio:
            return

        @self.sio.event
        async def connect(sid: str, environ: Dict, auth: Optional[Dict] = None):
            # TODO: Implement JWT authentication here (Task 1.10.1 from 01-todo-core.md)
            # For now, allow all connections and log
            logger.info(f"Client connected: sid={sid}, auth={auth}")
            # Example: Check auth token
            # if not auth or not self._is_valid_token(auth.get('token')):
            #     logger.warning(f"Client {sid} connection rejected due to invalid/missing token.")
            #     raise socketio.exceptions.ConnectionRefusedError('Authentication failed')
            await self.sio.emit('connection_status', {'status': 'connected', 'sid': sid}, room=sid)

        @self.sio.event
        async def disconnect(sid: str):
            logger.info(f"Client disconnected: sid={sid}")

        # Example: Handler for a message from client
        @self.sio.on('client_command')
        async def handle_client_command(sid: str, data: Dict):
            logger.info(f"Received client_command from {sid}: {data}")
            # TODO: Process command and route to DexBot or other services
            # Example: await self.emit_to_sid(sid, 'command_ack', {'received_command': data.get('command')})
            pass
    
    # --- Emitter Methods ---
    async def emit_to_all(self, event: str, data: Any):
        if self.sio:
            try:
                await self.sio.emit(event, data)
                logger.debug(f"Emitted '{event}' to all clients. Data: {str(data)[:200]}...")
            except Exception as e:
                logger.error(f"Error emitting event '{event}' to all: {e}", exc_info=True)
        else:
            logger.warning(f"Socket.IO server not initialized. Cannot emit event '{event}'.")

    async def emit_to_sid(self, sid: str, event: str, data: Any):
        if self.sio:
            try:
                await self.sio.emit(event, data, room=sid)
                logger.debug(f"Emitted '{event}' to SID {sid}. Data: {str(data)[:200]}...")
            except Exception as e:
                logger.error(f"Error emitting event '{event}' to SID {sid}: {e}", exc_info=True)
        else:
            logger.warning(f"Socket.IO server not initialized. Cannot emit event '{event}' to SID {sid}.")

    async def emit_to_room(self, room: str, event: str, data: Any):
        if self.sio:
            try:
                await self.sio.emit(event, data, room=room)
                logger.debug(f"Emitted '{event}' to room {room}. Data: {str(data)[:200]}...")
            except Exception as e:
                logger.error(f"Error emitting event '{event}' to room {room}: {e}", exc_info=True)
        else:
            logger.warning(f"Socket.IO server not initialized. Cannot emit event '{event}' to room {room}.")

    # --- Specific Event Emitters (as per todo/01-todo-core.md Task 1.10.1) ---
    async def emit_bot_status(self, data: Dict):
        await self.emit_to_all('bot_status_update', data)

    async def emit_portfolio_update(self, data: Dict):
        await self.emit_to_all('portfolio_update', data)

    async def emit_new_trade_executed(self, data: Dict):
        await self.emit_to_all('new_trade_executed', data)

    async def emit_ai_agent_decision(self, data: Dict):
        await self.emit_to_all('ai_agent_decision', data)

    async def emit_market_data_update(self, data: Dict): # Typically per pair, so might go to a room
        # Example: if data contains a pair symbol, emit to a room named after the pair
        # pair_symbol = data.get('pair')
        # if pair_symbol:
        #     await self.emit_to_room(pair_symbol, 'market_data_update', data)
        # else:
        await self.emit_to_all('market_data_update', data)

    async def emit_system_health_update(self, data: Dict):
        await self.emit_to_all('system_health_update', data)

    async def emit_new_log_entry(self, data: Dict):
        await self.emit_to_all('new_log_entry', data)

# Global instance (singleton-like usage for convenience)
# This allows other modules to import and use socket_manager.emit_...()
# Ensure it's initialized once, typically in main.py or where the FastAPI app is created.
socket_manager: Optional[SocketManager] = None

def get_socket_manager(cors_allowed_origins="*") -> SocketManager:
    global socket_manager
    if socket_manager is None:
        socket_manager = SocketManager(cors_allowed_origins=cors_allowed_origins)
    return socket_manager


if __name__ == "__main__":
    # Example usage / test snippet (would require an ASGI server to run)
    logging.basicConfig(level=logging.DEBUG)
    sm = get_socket_manager()

    async def test_emit():
        if sm.sio:
            logger.info("Socket.IO server seems initialized via get_socket_manager().")
            # These emits won't actually go anywhere without a connected client and running server
            await sm.emit_bot_status({"status": "TESTING", "cycle": 0})
            await sm.emit_to_all("test_event", {"message": "Hello from SocketManager test"})
        else:
            logger.error("Socket.IO server not initialized in test snippet.")

    # To run this test, you would need to integrate with uvicorn, e.g.:
    # import uvicorn
    # async def main():
    #     app_for_uvicorn = socketio.ASGIApp(sm.sio) # Get the ASGIApp from the manager
    #     config = uvicorn.Config(app_for_uvicorn, host="127.0.0.1", port=5000, log_level="info")
    #     server = uvicorn.Server(config)
    #     await server.serve()
    #     # After server starts, you could connect a client and then call test_emit()
    # asyncio.run(main())

    # For a simple non-server test:
    import asyncio
    asyncio.run(test_emit()) 