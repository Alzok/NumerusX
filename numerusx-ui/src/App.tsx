import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbPage } from '@/components/ui/breadcrumb';
import SidebarComponent from '@/components/layout/Sidebar';
import DashboardPage from '@/pages/DashboardPage';
import TradingPage from '@/pages/TradingPage';
import CommandPage from '@/pages/CommandPage';
import SettingsPage from '@/pages/SettingsPage';
import LoginPage from '@/pages/LoginPage';
import { AuthenticationGuard } from '@/components/auth/AuthenticationGuard';
import { initSocketConnection, disconnectSocket } from '@/lib/socketClient';
import { useApiClient } from '@/hooks/useApiClient';
import './App.css';

// Layout component for authenticated routes
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const getCurrentPageTitle = () => {
    const path = window.location.pathname;
    switch (path) {
      case '/dashboard':
        return 'Dashboard';
      case '/trading':
        return 'Trading';
      case '/command':
        return 'Bot IA';
      case '/settings':
        return 'Paramètres';
      default:
        return 'Dashboard';
    }
  };

  return (
    <SidebarProvider>
      <SidebarComponent />
      <SidebarInset>
        {/* Header with breadcrumb */}
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbPage>{getCurrentPageTitle()}</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>
        
        {/* Main content */}
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
};

const App: React.FC = () => {
  const { isLoading, error, isAuthenticated } = useAuth0();
  
  // Configure l'API client avec Auth0
  useApiClient();

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
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-lg text-muted-foreground">Chargement de l'application...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <p className="text-lg text-destructive">Erreur d'authentification: {error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
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
        }
      }
    };

    connectSocket();

    return () => {
      isMounted = false;
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
        <Route path="*" element={<Navigate to="/dashboard" replace />} /> 
      </Routes>
    </AppLayout>
  );
};

export default App; 