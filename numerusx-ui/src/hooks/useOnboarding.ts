import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/apiClient';

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  missing_required: string[];
}

export interface SystemStatus {
  is_configured: boolean;
  operating_mode: 'test' | 'production';
  theme_name: string;
  theme_palette: string;
  last_configuration_update?: string;
  configuration_version: number;
  status_indicator: 'operational' | 'test' | 'error';
  status_message: string;
}

export interface OnboardingData {
  step1: any;
  step2: any;
  step3: any;
}

export const useOnboarding = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getSystemStatus = useCallback(async (): Promise<SystemStatus> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.get('/onboarding/status');
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get system status';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const validateStep1 = useCallback(async (step1Data: any): Promise<ValidationResult> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.post('/onboarding/validate-step1', step1Data);
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Validation failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const completeOnboarding = useCallback(async (onboardingData: OnboardingData) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.post('/onboarding/complete', onboardingData);
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Onboarding completion failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateOperatingMode = useCallback(async (mode: 'test' | 'production') => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.post(`/onboarding/update-mode?mode=${mode}`);
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Mode update failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getCurrentConfiguration = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.get('/onboarding/configuration');
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get configuration';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getThemePalettes = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.get('/onboarding/theme-palettes');
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get theme palettes';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isLoading,
    error,
    getSystemStatus,
    validateStep1,
    completeOnboarding,
    updateOperatingMode,
    getCurrentConfiguration,
    getThemePalettes,
  };
}; 