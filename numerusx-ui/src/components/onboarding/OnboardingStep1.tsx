import React, { useState, useEffect } from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { 
  Eye, EyeOff, ExternalLink, Info, Key, Shield, Wallet, 
  CheckCircle, AlertTriangle, HelpCircle 
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface OnboardingStep1Props {
  data: any;
  onChange: (data: any) => void;
  onValidationError: (error: string | null) => void;
}

const OnboardingStep1: React.FC<OnboardingStep1Props> = ({ data, onChange, onValidationError }) => {
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [validationStatus, setValidationStatus] = useState<Record<string, 'valid' | 'invalid' | 'pending'>>({});

  const togglePasswordVisibility = (field: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleInputChange = (field: string, value: string) => {
    const newData = { ...data, [field]: value };
    onChange(newData);
    
    // Basic validation
    validateField(field, value);
  };

  const validateField = (field: string, value: string) => {
    let isValid = false;
    
    switch (field) {
      case 'google_api_key':
        isValid = value.length > 30 && value.startsWith('AI');
        break;
      case 'solana_private_key_bs58':
        isValid = value.length >= 80 && value.length <= 90; // Base58 format approximation
        break;
      case 'solana_rpc_url':
        isValid = value.startsWith('https://') && value.includes('solana');
        break;
      case 'auth0_domain':
        isValid = !value || value.includes('.auth0.com');
        break;
      default:
        isValid = true;
    }
    
    setValidationStatus(prev => ({
      ...prev,
      [field]: isValid ? 'valid' : 'invalid'
    }));
  };

  const apiKeyFields = [
    {
      id: 'google_api_key',
      label: 'Clé API Google (Gemini)',
      placeholder: 'AIzaSy...',
      required: true,
      type: 'password',
      description: 'Clé API pour Google AI (Gemini)',
      helpText: 'Obtenez votre clé sur Google AI Studio',
      helpUrl: 'https://makersuite.google.com/app/apikey'
    },
    {
      id: 'jupiter_api_key',
      label: 'Clé API Jupiter (Optionnel)',
      placeholder: 'Entrez votre clé Jupiter...',
      required: false,
      type: 'password',
      description: 'Clé API pour Jupiter (trading avancé)',
      helpText: 'Optionnel - améliore les performances de trading'
    },
    {
      id: 'jupiter_pro_api_key',
      label: 'Clé API Jupiter Pro (Optionnel)',
      placeholder: 'Entrez votre clé Jupiter Pro...',
      required: false,
      type: 'password',
      description: 'Clé API pour Jupiter Pro (fonctionnalités avancées)'
    },
    {
      id: 'dexscreener_api_key',
      label: 'Clé API DexScreener (Optionnel)',
      placeholder: 'Entrez votre clé DexScreener...',
      required: false,
      type: 'password',
      description: 'Pour données de marché étendues'
    }
  ];

  const securityFields = [
    {
      id: 'solana_private_key_bs58',
      label: 'Clé Privée Solana',
      placeholder: 'Entrez votre clé privée en format Base58...',
      required: true,
      type: 'password',
      description: 'Clé privée de votre wallet Solana (format Base58)',
      helpText: 'ATTENTION: Gardez cette clé secrète et sécurisée'
    },
    {
      id: 'solana_rpc_url',
      label: 'URL RPC Solana',
      placeholder: 'https://api.devnet.solana.com',
      required: false,
      type: 'text',
      description: 'Endpoint RPC pour les transactions Solana',
      helpText: 'Utilise devnet par défaut, changez pour mainnet en production'
    }
  ];

  const authFields = [
    {
      id: 'auth0_domain',
      label: 'Domaine Auth0 (Optionnel)',
      placeholder: 'votre-tenant.auth0.com',
      required: false,
      type: 'text',
      description: 'Domaine de votre tenant Auth0',
      helpText: 'Laissez vide pour désactiver l\'authentification'
    },
    {
      id: 'auth0_client_id',
      label: 'Client ID Auth0 (Optionnel)',
      placeholder: 'Entrez votre Client ID Auth0...',
      required: false,
      type: 'text',
      description: 'Identifiant client Auth0'
    },
    {
      id: 'auth0_audience',
      label: 'Audience Auth0 (Optionnel)',
      placeholder: 'https://api.numerusx.com',
      required: false,
      type: 'text',
      description: 'Audience de votre API Auth0'
    }
  ];

  const renderField = (field: any) => {
    const isPassword = field.type === 'password';
    const showPassword = showPasswords[field.id];
    const status = validationStatus[field.id];
    const value = data[field.id] || '';

    return (
      <div key={field.id} className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={field.id} className="flex items-center space-x-2">
            <span>{field.label}</span>
            {field.required && <Badge variant="destructive" className="text-xs">Requis</Badge>}
            {field.helpText && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <HelpCircle className="h-4 w-4 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p>{field.helpText}</p>
                    {field.helpUrl && (
                      <a 
                        href={field.helpUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 inline-flex items-center mt-1"
                      >
                        Voir la documentation <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    )}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </Label>
          
          {/* Validation Status */}
          {value && (
            <div className="flex items-center">
              {status === 'valid' && <CheckCircle className="h-4 w-4 text-green-500" />}
              {status === 'invalid' && <AlertTriangle className="h-4 w-4 text-red-500" />}
            </div>
          )}
        </div>

        <div className="relative">
          <Input
            id={field.id}
            type={isPassword && !showPassword ? 'password' : 'text'}
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleInputChange(field.id, e.target.value)}
            className={`pr-10 ${
              status === 'valid' ? 'border-green-500' : 
              status === 'invalid' ? 'border-red-500' : ''
            }`}
          />
          {isPassword && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
              onClick={() => togglePasswordVisibility(field.id)}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          )}
        </div>

        {field.description && (
          <p className="text-sm text-muted-foreground">{field.description}</p>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <Alert>
        <Shield className="h-4 w-4" />
        <AlertDescription>
          <strong>Sécurité:</strong> Toutes vos clés seront chiffrées et stockées de manière sécurisée. 
          Seules les données nécessaires sont transmises aux services externes.
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="api-keys" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="api-keys" className="flex items-center space-x-2">
            <Key className="h-4 w-4" />
            <span>Clés API</span>
          </TabsTrigger>
          <TabsTrigger value="wallet" className="flex items-center space-x-2">
            <Wallet className="h-4 w-4" />
            <span>Portefeuille</span>
          </TabsTrigger>
          <TabsTrigger value="auth" className="flex items-center space-x-2">
            <Shield className="h-4 w-4" />
            <span>Authentification</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="api-keys" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Key className="h-5 w-5" />
                <span>Clés API Externes</span>
              </CardTitle>
              <CardDescription>
                Configurez vos clés d'accès aux services externes pour le trading et l'IA.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {apiKeyFields.map(renderField)}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="wallet" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Wallet className="h-5 w-5" />
                <span>Configuration Solana</span>
              </CardTitle>
              <CardDescription>
                Configurez votre portefeuille Solana et l'accès au réseau.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {securityFields.map(renderField)}
              
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Conseil:</strong> Commencez avec le devnet pour les tests, 
                  puis passez au mainnet une fois votre configuration validée.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="auth" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Authentification (Optionnel)</span>
              </CardTitle>
              <CardDescription>
                Configurez Auth0 pour sécuriser l'accès à votre application.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {authFields.map(renderField)}
              
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  L'authentification peut être configurée plus tard. 
                  Si vous laissez ces champs vides, l'accès sera libre (mode développement).
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Summary */}
      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-base">Résumé de Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Clés API configurées:</span>
              <span className="ml-2">
                {[...apiKeyFields, ...securityFields, ...authFields]
                  .filter(field => data[field.id])
                  .length} / {[...apiKeyFields, ...securityFields, ...authFields].length}
              </span>
            </div>
            <div>
              <span className="font-medium">Champs requis:</span>
              <span className="ml-2">
                {[...apiKeyFields, ...securityFields]
                  .filter(field => field.required && data[field.id])
                  .length} / {[...apiKeyFields, ...securityFields].filter(field => field.required).length}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OnboardingStep1; 