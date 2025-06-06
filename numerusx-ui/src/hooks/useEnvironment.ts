import { useMemo } from 'react';

interface EnvironmentConfig {
  isLocalhost: boolean;
  isProduction: boolean;
  enableOnboarding: boolean;
  enableAuth0: boolean;
  apiUrl: string;
}

export const useEnvironment = (): EnvironmentConfig => {
  return useMemo(() => {
    const hostname = window.location.hostname;
    const isLocalhost = hostname === 'localhost' || 
                       hostname === '127.0.0.1' || 
                       hostname === '0.0.0.0' ||
                       hostname === '::1' ||
                       hostname.endsWith('.local');

    const isProduction = !isLocalhost && 
                        (process.env.NODE_ENV === 'production' ||
                         window.location.protocol === 'https:');

    return {
      isLocalhost,
      isProduction,
      enableOnboarding: true,        // Always enable onboarding (with auth)
      enableAuth0: true,             // Always use Auth0 authentication
      apiUrl: isLocalhost 
        ? 'http://localhost:8000' 
        : window.location.origin.replace(/:\d+$/, '') + ':8000'
    };
  }, []);
};

export default useEnvironment; 