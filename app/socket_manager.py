import socketio
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import jwt
from jwt import InvalidTokenError

from app.config import get_config

logger = logging.getLogger(__name__)

class SocketManager:
    """Manages Socket.IO server and emits events."""
    _sio_server: Optional[socketio.AsyncServer] = None
    _sio_app: Optional[socketio.ASGIApp] = None
    _authenticated_clients: Dict[str, Dict[str, Any]] = {}

    def __init__(self, cors_allowed_origins="*"):
        if SocketManager._sio_server is None:
            SocketManager._sio_server = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins=cors_allowed_origins,
                # logger=True, # Enable for socketio detailed logs
                # engineio_logger=True # Enable for engineio detailed logs
            )
            SocketManager._sio_app = socketio.ASGIApp(SocketManager._sio_server)
            self._register_handlers()
            logger.info(f"Socket.IO AsyncServer initialized with CORS: {cors_allowed_origins}")

    @property
    def app(self) -> Optional[socketio.ASGIApp]:
        return SocketManager._sio_app

    @property
    def sio(self) -> Optional[socketio.AsyncServer]:
        return SocketManager._sio_server

    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data."""
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(
                token, 
                get_config().security.jwt_secret_key, 
                algorithms=[get_config().JWT_ALGORITHM]
            )
            return payload
        except InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying JWT token: {e}")
            return None

    def _register_handlers(self):
        """Register all Socket.IO event handlers."""
        if not self.sio:
            return

        @self.sio.event
        async def connect(sid: str, environ: Dict, auth: Optional[Dict] = None):
            """Handle client connection with JWT authentication."""
            try:
                # Extract token from auth or headers
                token = None
                if auth and 'token' in auth:
                    token = auth['token']
                elif 'HTTP_AUTHORIZATION' in environ:
                    token = environ['HTTP_AUTHORIZATION']
                
                if not token:
                    logger.warning(f"Client {sid} connection rejected: No authentication token")
                    raise socketio.exceptions.ConnectionRefusedError('Authentication token required')
                
                # Verify token
                user_data = self._verify_jwt_token(token)
                if not user_data:
                    logger.warning(f"Client {sid} connection rejected: Invalid token")
                    raise socketio.exceptions.ConnectionRefusedError('Invalid authentication token')
                
                # Store authenticated client info
                SocketManager._authenticated_clients[sid] = {
                    'user_data': user_data,
                    'connected_at': datetime.utcnow().isoformat(),
                    'last_activity': datetime.utcnow().isoformat()
                }
                
                logger.info(f"Client connected: sid={sid}, user={user_data.get('username', 'unknown')}")
                
                # Send connection confirmation
                await self.sio.emit('connection_status', {
                    'status': 'connected',
                    'sid': sid,
                    'user': user_data.get('username'),
                    'server_time': datetime.utcnow().isoformat()
                }, room=sid)
                
                # Send initial system status
                await self._send_initial_status(sid)
                
            except Exception as e:
                logger.error(f"Error during client connection: {e}")
                raise socketio.exceptions.ConnectionRefusedError('Connection failed')

        @self.sio.event
        async def disconnect(sid: str):
            """Handle client disconnection."""
            user_info = SocketManager._authenticated_clients.pop(sid, {})
            username = user_info.get('user_data', {}).get('username', 'unknown')
            logger.info(f"Client disconnected: sid={sid}, user={username}")

        @self.sio.on('subscribe_to_channel')
        async def handle_subscribe(sid: str, data: Dict):
            """Handle subscription to specific channels."""
            if sid not in SocketManager._authenticated_clients:
                await self.sio.emit('error', {'message': 'Not authenticated'}, room=sid)
                return
            
            channel = data.get('channel')
            if not channel:
                await self.sio.emit('error', {'message': 'Channel name required'}, room=sid)
                return
            
            # Join the client to the channel room
            await self.sio.enter_room(sid, channel)
            await self.sio.emit('subscription_status', {
                'channel': channel,
                'status': 'subscribed'
            }, room=sid)
            
            logger.debug(f"Client {sid} subscribed to channel: {channel}")

        @self.sio.on('unsubscribe_from_channel')
        async def handle_unsubscribe(sid: str, data: Dict):
            """Handle unsubscription from channels."""
            if sid not in SocketManager._authenticated_clients:
                return
            
            channel = data.get('channel')
            if channel:
                await self.sio.leave_room(sid, channel)
                await self.sio.emit('subscription_status', {
                    'channel': channel,
                    'status': 'unsubscribed'
                }, room=sid)

        @self.sio.on('ping')
        async def handle_ping(sid: str, data: Dict):
            """Handle ping for keepalive."""
            if sid in SocketManager._authenticated_clients:
                SocketManager._authenticated_clients[sid]['last_activity'] = datetime.utcnow().isoformat()
                await self.sio.emit('pong', {
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': data
                }, room=sid)

        @self.sio.on('get_bot_status')
        async def handle_get_bot_status(sid: str, data: Dict):
            """Handle request for current bot status."""
            if sid not in SocketManager._authenticated_clients:
                await self.sio.emit('error', {'message': 'Not authenticated'}, room=sid)
                return
            
            # This would typically get real bot status
            # For now, send mock data
            bot_status = {
                'running': True,
                'uptime': '2h 34m',
                'current_cycle': 156,
                'last_decision': 'HOLD',
                'next_cycle_in': '45s'
            }
            await self.sio.emit('bot_status_response', bot_status, room=sid)

        @self.sio.on('request_portfolio_update')
        async def handle_portfolio_request(sid: str, data: Dict):
            """Handle request for portfolio update."""
            if sid not in SocketManager._authenticated_clients:
                await self.sio.emit('error', {'message': 'Not authenticated'}, room=sid)
                return
            
            # This would get real portfolio data
            portfolio_data = {
                'total_value_usd': 10000.0,
                'sol_balance': 50.0,
                'usdc_balance': 5000.0,
                'pnl_24h': 123.45,
                'positions': []
            }
            await self.sio.emit('portfolio_update', portfolio_data, room=sid)

    async def _send_initial_status(self, sid: str):
        """Send initial status data to newly connected client."""
        try:
            # Send initial bot status
            await self.sio.emit('bot_status_update', {
                'running': True,
                'uptime': '2h 34m',
                'status': 'MONITORING'
            }, room=sid)
            
            # Send initial market data
            await self.sio.emit('market_data_update', {
                'pair': 'SOL/USDC',
                'price': 57.65,
                'change_24h': 2.34,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
            
        except Exception as e:
            logger.error(f"Error sending initial status to {sid}: {e}")

    # --- Emitter Methods ---
    async def emit_to_all(self, event: str, data: Any):
        """Emit event to all authenticated clients."""
        if self.sio:
            try:
                await self.sio.emit(event, data)
                logger.debug(f"Emitted '{event}' to all clients. Data: {str(data)[:200]}...")
            except Exception as e:
                logger.error(f"Error emitting event '{event}' to all: {e}", exc_info=True)
        else:
            logger.warning(f"Socket.IO server not initialized. Cannot emit event '{event}'.")

    async def emit_to_sid(self, sid: str, event: str, data: Any):
        """Emit event to specific client by session ID."""
        if self.sio:
            try:
                await self.sio.emit(event, data, room=sid)
                logger.debug(f"Emitted '{event}' to SID {sid}. Data: {str(data)[:200]}...")
            except Exception as e:
                logger.error(f"Error emitting event '{event}' to SID {sid}: {e}", exc_info=True)
        else:
            logger.warning(f"Socket.IO server not initialized. Cannot emit event '{event}' to SID {sid}.")

    async def emit_to_room(self, room: str, event: str, data: Any):
        """Emit event to specific room/channel."""
        if self.sio:
            try:
                await self.sio.emit(event, data, room=room)
                logger.debug(f"Emitted '{event}' to room {room}. Data: {str(data)[:200]}...")
            except Exception as e:
                logger.error(f"Error emitting event '{event}' to room {room}: {e}", exc_info=True)
        else:
            logger.warning(f"Socket.IO server not initialized. Cannot emit event '{event}' to room {room}.")

    async def emit_to_authenticated_clients(self, event: str, data: Any):
        """Emit event only to authenticated clients."""
        if self.sio:
            for sid in SocketManager._authenticated_clients.keys():
                await self.emit_to_sid(sid, event, data)

    # --- Specific Event Emitters (as per todo/01-todo-core.md Task 1.10.1) ---
    async def emit_bot_status_update(self, data: Dict):
        """Emit bot status update to all authenticated clients."""
        data['timestamp'] = datetime.utcnow().isoformat()
        await self.emit_to_authenticated_clients('bot_status_update', data)

    async def emit_portfolio_update(self, data: Dict):
        """Emit portfolio update to all authenticated clients."""
        data['timestamp'] = datetime.utcnow().isoformat()
        await self.emit_to_authenticated_clients('portfolio_update', data)

    async def emit_new_trade_executed(self, data: Dict):
        """Emit new trade notification to all authenticated clients."""
        data['timestamp'] = datetime.utcnow().isoformat()
        await self.emit_to_authenticated_clients('new_trade_executed', data)

    async def emit_ai_agent_decision(self, data: Dict):
        """Emit AI agent decision to all authenticated clients."""
        data['timestamp'] = datetime.utcnow().isoformat()
        await self.emit_to_authenticated_clients('ai_agent_decision', data)

    async def emit_market_data_update(self, data: Dict):
        """Emit market data update."""
        data['timestamp'] = datetime.utcnow().isoformat()
        pair = data.get('pair', 'general')
        # Emit to specific pair room and all authenticated clients
        await self.emit_to_room(f"market_{pair}", 'market_data_update', data)
        await self.emit_to_authenticated_clients('market_data_update', data)

    async def emit_system_health_update(self, data: Dict):
        """Emit system health update to all authenticated clients."""
        data['timestamp'] = datetime.utcnow().isoformat()
        await self.emit_to_authenticated_clients('system_health_update', data)

    async def emit_new_log_entry(self, data: Dict):
        """Emit new log entry for real-time log streaming."""
        data['timestamp'] = datetime.utcnow().isoformat()
        # Only emit to clients subscribed to logs channel
        await self.emit_to_room('logs', 'new_log_entry', data)

    # --- Utility Methods ---
    def get_authenticated_clients_count(self) -> int:
        """Get number of authenticated clients."""
        return len(SocketManager._authenticated_clients)

    def get_client_info(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get information about specific client."""
        return SocketManager._authenticated_clients.get(sid)

    async def disconnect_client(self, sid: str, reason: str = "Server disconnect"):
        """Disconnect specific client."""
        if self.sio and sid in SocketManager._authenticated_clients:
            await self.sio.disconnect(sid)
            logger.info(f"Disconnected client {sid}: {reason}")

# Global instance (singleton-like usage for convenience)
socket_manager: Optional[SocketManager] = None

def get_socket_manager(cors_allowed_origins="*") -> SocketManager:
    """Get global socket manager instance."""
    global socket_manager
    if socket_manager is None:
        socket_manager = SocketManager(cors_allowed_origins=cors_allowed_origins)
    return socket_manager


if __name__ == "__main__":
    # Example usage / test snippet
    logging.basicConfig(level=logging.DEBUG)
    sm = get_socket_manager()

    async def test_emit():
        if sm.sio:
            logger.info("Socket.IO server initialized.")
            await sm.emit_bot_status_update({"status": "TESTING", "cycle": 0})
            await sm.emit_to_all("test_event", {"message": "Hello from SocketManager test"})
        else:
            logger.error("Socket.IO server not initialized.")

    import asyncio
    asyncio.run(test_emit()) 