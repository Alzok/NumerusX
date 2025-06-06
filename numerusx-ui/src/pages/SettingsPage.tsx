import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { 
  Settings, 
  Key, 
  Palette, 
  Shield, 
  Save, 
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  TestTube,
  Zap
} from "lucide-react";

import { useOnboarding } from '@/hooks/useOnboarding';
import OnboardingStep1 from '@/components/onboarding/OnboardingStep1';
import OnboardingStep2 from '@/components/onboarding/OnboardingStep2';
import OnboardingStep3 from '@/components/onboarding/OnboardingStep3';
import StatusIndicator from '@/components/system/StatusIndicator';

const SettingsPage: React.FC = () => {
  const [currentConfig, setCurrentConfig] = useState<any>(null);
  const [step1Data, setStep1Data] = useState<any>({});
  const [step2Data, setStep2Data] = useState<any>({});
  const [step3Data, setStep3Data] = useState<any>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('api-keys');

  const { 
    getCurrentConfiguration, 
    completeOnboarding, 
    getSystemStatus,
    updateOperatingMode 
  } = useOnboarding();

  useEffect(() => {
    loadCurrentConfiguration();
  }, []);

  const loadCurrentConfiguration = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const config = await getCurrentConfiguration();
      setCurrentConfig(config);
      
      // Populate form data
      if (config.step1) setStep1Data(config.step1);
      if (config.step2) setStep2Data(config.step2);
      if (config.step3) setStep3Data(config.step3);
      
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement de la configuration');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);
      setSuccess(null);

      const onboardingData = {
        step1: step1Data,
        step2: step2Data,
        step3: step3Data
      };

      await completeOnboarding(onboardingData);
      setSuccess('Configuration mise à jour avec succès !');
      
      // Reload configuration
      await loadCurrentConfiguration();
      
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la sauvegarde');
    } finally {
      setIsSaving(false);
    }
  };

  const handleModeSwitch = async (newMode: 'test' | 'production') => {
    try {
      setIsSaving(true);
      setError(null);
      
      await updateOperatingMode(newMode);
      setSuccess(`Mode changé en ${newMode === 'test' ? 'Test' : 'Production'}`);
      
      // Update step3 data to reflect the change
      setStep3Data((prev: any) => ({ ...prev, operating_mode: newMode }));
      
    } catch (err: any) {
      setError(err.message || 'Erreur lors du changement de mode');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Chargement de la configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Paramètres</h1>
          <p className="text-muted-foreground mt-1">
            Gérez la configuration de votre bot de trading NumerusX
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <StatusIndicator />
          
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="bg-green-600 hover:bg-green-700"
          >
            {isSaving ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Sauvegarde...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Sauvegarder
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-700">{success}</AlertDescription>
        </Alert>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Actions Rapides</span>
          </CardTitle>
          <CardDescription>
            Changements fréquents et actions importantes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Mode d'Opération</div>
              <div className="text-sm text-muted-foreground">
                {step3Data.operating_mode === 'test' 
                  ? 'Mode Test - Simulation sans vrais fonds' 
                  : 'Mode Production - Trading avec vrais fonds'
                }
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <Badge variant={step3Data.operating_mode === 'test' ? 'secondary' : 'destructive'}>
                {step3Data.operating_mode === 'test' ? (
                  <><TestTube className="w-3 h-3 mr-1" /> Test</>
                ) : (
                  <><Zap className="w-3 h-3 mr-1" /> Production</>
                )}
              </Badge>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleModeSwitch(
                  step3Data.operating_mode === 'test' ? 'production' : 'test'
                )}
                disabled={isSaving}
              >
                {step3Data.operating_mode === 'test' ? (
                  <>
                    <Zap className="mr-2 h-3 w-3" />
                    Passer en Production
                  </>
                ) : (
                  <>
                    <TestTube className="mr-2 h-3 w-3" />
                    Passer en Test
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Configuration Tabs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Configuration Détaillée</span>
          </CardTitle>
          <CardDescription>
            Modifiez tous les aspects de votre configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="api-keys" className="flex items-center space-x-2">
                <Key className="h-4 w-4" />
                <span>Clés API</span>
              </TabsTrigger>
              <TabsTrigger value="theme" className="flex items-center space-x-2">
                <Palette className="h-4 w-4" />
                <span>Apparence</span>
              </TabsTrigger>
              <TabsTrigger value="trading" className="flex items-center space-x-2">
                <Shield className="h-4 w-4" />
                <span>Trading</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="api-keys" className="mt-6">
              <OnboardingStep1
                data={step1Data}
                onChange={setStep1Data}
                onValidationError={setError}
              />
            </TabsContent>

            <TabsContent value="theme" className="mt-6">
              <OnboardingStep2
                data={step2Data}
                onChange={setStep2Data}
              />
            </TabsContent>

            <TabsContent value="trading" className="mt-6">
              <OnboardingStep3
                data={step3Data}
                onChange={setStep3Data}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Configuration Summary */}
      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-base">Résumé de Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium block">Mode:</span>
              <Badge variant={step3Data.operating_mode === 'test' ? 'secondary' : 'destructive'} className="mt-1">
                {step3Data.operating_mode === 'test' ? 'Test' : 'Production'}
              </Badge>
            </div>
            
            <div>
              <span className="font-medium block">Thème:</span>
              <span className="capitalize">{step2Data.theme_palette || 'slate'}</span>
            </div>
            
            <div>
              <span className="font-medium block">Solde Initial:</span>
              <span>${(step3Data.initial_balance_usd || 1000).toLocaleString()}</span>
            </div>
            
            <div>
              <span className="font-medium block">Max par Trade:</span>
              <span>${step3Data.max_trade_size_usd || 100}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Warning for Production Mode */}
      {step3Data.operating_mode === 'production' && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>Mode Production Actif:</strong> Vous utilisez de vrais fonds. 
            Assurez-vous que tous vos paramètres sont corrects avant de faire du trading.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default SettingsPage; 