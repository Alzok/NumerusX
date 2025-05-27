import React, { useEffect } from 'react';
import { Routes, Route, Outlet, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react'; // Import useAuth0
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import Footer from '@/components/layout/Footer';
import DashboardPage from '@/pages/DashboardPage';
import TradingPage from '@/pages/TradingPage';
import CommandPage from '@/pages/CommandPage';
import SettingsPage from '@/pages/SettingsPage';
import LoginPage from '@/pages/LoginPage'; // Assuming you have a LoginPage
import { AuthenticationGuard } from '@/components/auth/AuthenticationGuard'; // Import the guard
import { initSocketConnection, disconnectSocket } from '@/lib/socketClient'; // Import socket functions
import './App.css';

// Layout component for authenticated routes
const AppLayout: React.FC = () => (
  <div className="flex flex-col min-h-screen bg-background text-foreground">
    <Header />
    <div className="flex flex-1 pt-14"> {/* Add padding-top to account for sticky header height */}
      <Sidebar className="w-64 hidden md:block fixed top-14 left-0 h-[calc(100vh-56px)]" /> {/* Adjust width, top, and height */}
      <main className="flex-1 p-4 md:p-6 lg:p-8 md:ml-64"> {/* Add margin-left to account for sidebar width */}
        <Outlet /> {/* Nested routes will render here */}
      </main>
    </div>
    {/* Footer can be optional within the authenticated layout or outside */}
    {/* <Footer /> */}
  </div>
);

// Separate layout for public routes like Login if needed
// const PublicLayout: React.FC = () => (<Outlet />);

const App: React.FC = () => {
  const { isLoading, error, isAuthenticated } = useAuth0();

  useEffect(() => {
    // Cleanup socket connection when the main App unmounts or user is no longer authenticated
    return () => {
      if (!isAuthenticated) {
        disconnectSocket();
      }
    };
  }, [isAuthenticated]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-lg text-muted-foreground">Loading application...</p>
        {/* You can replace this with a more sophisticated spinner/loader component */}
      </div>
    );
  }

  // Could add more robust error handling here, e.g., display a specific error page
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-lg text-red-500">Authentication Error: {error.message}</p>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {/* All other routes are protected and use ProtectedRoutes component */}
      <Route 
        path="/*" 
        element={<AuthenticationGuard component={ProtectedRoutes} />} 
      />
    </Routes>
  );
};

// This component will be wrapped by AuthenticationGuard
const ProtectedRoutes: React.FC = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  useEffect(() => {
    let isMounted = true;
    const connectSocket = async () => {
      if (isAuthenticated && isMounted) {
        try {
          const token = await getAccessTokenSilently();
          console.log('Auth0 Access Token for Socket:', token ? 'obtained' : 'not obtained');
          initSocketConnection(token); 
        } catch (e) {
          console.error('Error getting access token or connecting socket:', e);
          // Handle error, maybe redirect to login or show a message
        }
      }
    };

    connectSocket();

    return () => {
      isMounted = false;
      // Optional: Disconnect socket on component unmount if not handled elsewhere or if user logs out
      // disconnectSocket(); 
    };
  }, [isAuthenticated, getAccessTokenSilently]);

  return (
    <AppLayout>
      <Routes>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="trading" element={<TradingPage />} />
        <Route path="command" element={<CommandPage />} />
        <Route path="settings" element={<SettingsPage />} />
        {/* Fallback for any route not matched within the authenticated layout */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} /> 
      </Routes>
    </AppLayout>
  );
};

export default App; 