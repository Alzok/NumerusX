import React, { useEffect } from 'react';
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useTranslation } from 'react-i18next';

const LoginPage: React.FC = () => {
  const { loginWithRedirect, isAuthenticated, isLoading } = useAuth0();
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <p className="text-lg text-muted-foreground">{t('generic.loading')}</p>
      </div>
    );
  }

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-primary to-secondary p-4">
      <div className="w-full max-w-md p-8 space-y-8 bg-card rounded-xl shadow-2xl text-card-foreground">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight">{t('loginPage.welcomeTitle')}</h1>
          <p className="mt-2 text-muted-foreground">{t('loginPage.signInPrompt')}</p>
        </div>
        
        <Button 
          onClick={() => loginWithRedirect({ appState: { returnTo: '/dashboard' } })}
          className="w-full text-lg py-3"
          size="lg"
        >
          {t('loginPage.loginButton')}
        </Button>

        <p className="text-xs text-center text-muted-foreground">
          {t('loginPage.termsNotice')}
        </p>
      </div>
    </div>
  );
};

export default LoginPage; 