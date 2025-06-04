import React, { useEffect } from 'react';
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useTranslation } from 'react-i18next';
import { Zap, LogIn, Loader2 } from 'lucide-react';

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
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-lg text-muted-foreground">{t('generic.loading')}</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-900 dark:to-slate-800 p-4">
      <Card className="w-full max-w-md shadow-2xl">
        <CardHeader className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">NumerusX</h1>
              <p className="text-xs text-muted-foreground">Trading Bot IA</p>
            </div>
          </div>
          
          <div>
            <CardTitle className="text-2xl">{t('loginPage.welcomeTitle')}</CardTitle>
            <CardDescription className="mt-2">
              {t('loginPage.signInPrompt')}
            </CardDescription>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <Button 
            onClick={() => loginWithRedirect({ appState: { returnTo: '/dashboard' } })}
            className="w-full"
            size="lg"
          >
            <LogIn className="h-4 w-4 mr-2" />
            {t('loginPage.loginButton')}
          </Button>

          <Separator />

          <div className="space-y-2 text-center">
            <h3 className="text-sm font-medium">Fonctionnalités</h3>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>• Trading automatisé avec IA Gemini 2.5 Flash</li>
              <li>• Intégration Jupiter DEX v6 pour Solana</li>
              <li>• Dashboard en temps réel</li>
              <li>• Gestion de portfolio avancée</li>
            </ul>
          </div>

          <p className="text-xs text-center text-muted-foreground">
            {t('loginPage.termsNotice')}
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage; 