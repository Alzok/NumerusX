import { io, Socket } from 'socket.io-client';
import { store, AppDispatch } from '@/app/store'; // Assuming store and AppDispatch are exported

// Import Redux slice actions - adjust paths and action names as per your slices
// Example, replace with your actual slice actions:
// import { updateBotStatus } from '@/features/system/systemSlice'; 
// import { updatePortfolio } from '@/features/portfolio/portfolioSlice';
// import { addLogEntry } from '@/features/logging/loggingSlice';
// import { newAiDecision } from '@/features/aiAgent/aiAgentSlice';
// import { updateMarketData } from '@/features/market/marketSlice';

let socket: Socket | null = null;

const VITE_APP_SOCKET_URL = import.meta.env.VITE_APP_SOCKET_URL || 'http://localhost:8000'; // Default if not set

export const getSocket = (): Socket | null => socket;

export const initSocketConnection = (authToken?: string) => {
  if (socket && socket.connected) {
    console.log('Socket already connected.');
    return socket;
  }

  console.log(`Attempting to connect to Socket.IO server at ${VITE_APP_SOCKET_URL} with token: ${authToken ? ' vorhanden' : 'nicht vorhanden'}`);

  // Ensure previous socket is disconnected if any
  if (socket) {
    socket.disconnect();
  }

  const connectionOptions: any = {
    reconnectionAttempts: 5,
    reconnectionDelay: 3000,
    transports: ['websocket', 'polling'], // Prefer WebSocket
  };

  if (authToken) {
    connectionOptions.auth = { token: authToken };
    // Or if your backend expects it in query:
    // connectionOptions.query = { token: authToken };
  }

  socket = io(VITE_APP_SOCKET_URL, connectionOptions);
  const dispatch: AppDispatch = store.dispatch;

  socket.on('connect', () => {
    console.log('Socket.IO connected successfully. Socket ID:', socket?.id);
    // dispatch(updateBotStatus({ isConnected: true })); // Example: update connection status in Redux
  });

  socket.on('disconnect', (reason: string) => {
    console.warn('Socket.IO disconnected:', reason);
    // dispatch(updateBotStatus({ isConnected: false, reason }));
    if (reason === 'io server disconnect') {
      // The server explicitly disconnected the socket, re-attempting connection might not be wise immediately.
      // Potentially clear auth token if it's an auth issue.
    }
  });

  socket.on('connect_error', (error: Error) => {
    console.error('Socket.IO connection error:', error.message, error.name, error.stack);
    // dispatch(updateBotStatus({ connectionError: error.message }));
  });

  // Register listeners for backend events
  socket.on('bot_status_update', (data: any) => {
    console.log('🤖 Bot Status Update:', data);
    // TODO: dispatch(updateBotStatus(data)); 
  });

  socket.on('portfolio_update', (data: any) => {
    console.log('💰 Portfolio Update:', data);
    // Invalider le cache React Query pour forcer le reload
    // TODO: queryClient.invalidateQueries(['portfolio']);
  });

  socket.on('new_trade_executed', (data: any) => {
    console.log('💱 New Trade Executed:', data);
    // Invalider le cache des trades pour afficher le nouveau
    // TODO: queryClient.invalidateQueries(['trades']);
  });

  socket.on('ai_decision_update', (data: any) => {
    console.log('🧠 AI Decision Update:', data);
    // TODO: dispatch(newAiDecision(data));
  });

  socket.on('market_data_update', (data: any) => {
    console.log('📈 Market Data Update:', data);
    // TODO: dispatch(updateMarketData(data)); 
  });
  
  socket.on('system_alert', (data: { message: string; type: 'error' | 'success' | 'warning'; timestamp: string }) => {
    console.log('🚨 System Alert:', data);
    // TODO: Implémenter toast notifications
    // toast[data.type](data.message);
  });

  socket.on('emergency_stop', (data: any) => {
    console.log('🆘 Emergency Stop Triggered:', data);
    // TODO: Rediriger vers une page d'alerte ou afficher modal
  });

  return socket;
};

export const disconnectSocket = () => {
  if (socket) {
    console.log('Disconnecting Socket.IO...');
    socket.disconnect();
    socket = null;
  }
};

// Example function to emit an event
export const emitSocketEvent = (eventName: string, data?: any) => {
  if (socket && socket.connected) {
    socket.emit(eventName, data);
  } else {
    console.warn(`Socket not connected. Cannot emit event '${eventName}'.`);
  }
};

// Specific event emitters (examples)
export const startBot = () => emitSocketEvent('start_bot');
export const stopBot = () => emitSocketEvent('stop_bot');
export const getBotStatus = () => emitSocketEvent('get_bot_status');

// Consider calling initSocketConnection in your main App component or after successful login.
// The authToken should be retrieved from your auth provider (e.g., Auth0). 