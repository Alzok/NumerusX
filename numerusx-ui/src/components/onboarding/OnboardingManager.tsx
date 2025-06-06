import React, { useState, useEffect } from 'react';
import { useOnboarding, SystemStatus } from '@/hooks/useOnboarding';
import { useEnvironment } from '@/hooks/useEnvironment';
import OnboardingWizard from './OnboardingWizard';
import StatusIndicator from '../system/StatusIndicator';

interface OnboardingManagerProps {
  children: React.ReactNode;
}

const OnboardingManager: React.FC<OnboardingManagerProps> = ({ children }) => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { getSystemStatus } = useOnboarding();
  const { enableOnboarding } = useEnvironment();

  useEffect(() => {
    checkSystemStatus();
  }, []);

  const checkSystemStatus = async () => {
    try {
      setIsLoading(true);
      const status = await getSystemStatus();
      setSystemStatus(status);
      
      // Show onboarding if system is not configured AND we're in localhost environment
      if (!status.is_configured && enableOnboarding) {
        setShowOnboarding(true);
      }
    } catch (error) {
      console.error('Failed to check system status:', error);
      // If we can't get status, assume onboarding is needed
      setShowOnboarding(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOnboardingComplete = async () => {
    setShowOnboarding(false);
    // Refresh system status after onboarding
    await checkSystemStatus();
  };

  // Show loading state while checking system status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Vérification du système...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Main Application */}
      <div className="min-h-screen">
        {/* Status Indicator - Always visible when system is configured */}
        {systemStatus?.is_configured && (
          <div className="fixed top-4 right-4 z-40">
            <StatusIndicator compact />
          </div>
        )}
        
        {children}
      </div>

      {/* Onboarding Wizard - Modal overlay */}
      <OnboardingWizard
        isOpen={showOnboarding}
        onComplete={handleOnboardingComplete}
      />
    </>
  );
};

export default OnboardingManager; 