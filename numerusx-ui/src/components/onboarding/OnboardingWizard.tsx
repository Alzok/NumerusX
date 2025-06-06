import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

import OnboardingStep1 from './OnboardingStep1';
import OnboardingStep2 from './OnboardingStep2';
import OnboardingStep3 from './OnboardingStep3';
import { useOnboarding } from '@/hooks/useOnboarding';

interface OnboardingWizardProps {
  isOpen: boolean;
  onComplete: () => void;
}

const OnboardingWizard: React.FC<OnboardingWizardProps> = ({ isOpen, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [step1Data, setStep1Data] = useState({});
  const [step2Data, setStep2Data] = useState({});
  const [step3Data, setStep3Data] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { completeOnboarding, validateStep1 } = useOnboarding();

  const totalSteps = 3;
  const progressPercentage = (currentStep / totalSteps) * 100;

  const stepTitles = {
    1: "Clés API et Sécurité",
    2: "Personnalisation",
    3: "Mode Opérationnel"
  };

  const stepDescriptions = {
    1: "Configurez vos clés API pour accéder aux services externes",
    2: "Personnalisez l'apparence et les préférences de l'interface",
    3: "Choisissez votre mode d'utilisation et vos paramètres de risque"
  };

  const handleNext = async () => {
    if (currentStep < totalSteps) {
      // Validate current step before proceeding
      if (currentStep === 1) {
        try {
          const validation = await validateStep1(step1Data);
          if (!validation.is_valid) {
            setError(`Erreurs de validation: ${validation.errors.join(', ')}`);
            return;
          }
          if (validation.warnings.length > 0) {
            // Show warnings but allow to proceed
            console.warn('Configuration warnings:', validation.warnings);
          }
        } catch (err) {
          setError('Erreur lors de la validation. Veuillez vérifier vos informations.');
          return;
        }
      }
      
      setError(null);
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      setError(null);
    }
  };

  const handleComplete = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const onboardingData = {
        step1: step1Data,
        step2: step2Data,
        step3: step3Data
      };

      await completeOnboarding(onboardingData);
      onComplete();
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la finalisation de la configuration');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isStepValid = (step: number): boolean => {
    switch (step) {
      case 1:
        return step1Data.google_api_key && step1Data.solana_private_key_bs58;
      case 2:
        return true; // Step 2 has default values
      case 3:
        return step3Data.operating_mode;
      default:
        return false;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <OnboardingStep1
            data={step1Data}
            onChange={setStep1Data}
            onValidationError={setError}
          />
        );
      case 2:
        return (
          <OnboardingStep2
            data={step2Data}
            onChange={setStep2Data}
          />
        );
      case 3:
        return (
          <OnboardingStep3
            data={step3Data}
            onChange={setStep3Data}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => {}} modal>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-center">
            🚀 Configuration Initiale de NumerusX
          </DialogTitle>
          <div className="text-center space-y-2">
            <p className="text-muted-foreground">
              Configurons votre bot de trading IA en quelques étapes simples
            </p>
            <div className="flex items-center justify-center space-x-4 mt-4">
              <div className="text-sm font-medium">
                Étape {currentStep} sur {totalSteps}
              </div>
              <Progress value={progressPercentage} className="w-64" />
            </div>
          </div>
        </DialogHeader>

        {/* Current Step Info */}
        <Card className="mx-6 mb-4">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">
              {stepTitles[currentStep]}
            </CardTitle>
            <CardDescription>
              {stepDescriptions[currentStep]}
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive" className="mx-6 mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto px-6">
          {renderStepContent()}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center p-6 border-t bg-muted/50">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 1}
          >
            Précédent
          </Button>

          <div className="flex space-x-2">
            {/* Step indicators */}
            {Array.from({ length: totalSteps }, (_, i) => (
              <div
                key={i + 1}
                className={`w-3 h-3 rounded-full ${
                  i + 1 < currentStep
                    ? 'bg-green-500'
                    : i + 1 === currentStep
                    ? 'bg-blue-500'
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>

          {currentStep < totalSteps ? (
            <Button
              onClick={handleNext}
              disabled={!isStepValid(currentStep)}
            >
              Suivant
            </Button>
          ) : (
            <Button
              onClick={handleComplete}
              disabled={!isStepValid(currentStep) || isSubmitting}
              className="bg-green-600 hover:bg-green-700"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Configuration...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Finaliser
                </>
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default OnboardingWizard; 