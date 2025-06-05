import { useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { apiClient } from '@/lib/apiClient';

/**
 * Hook pour configurer automatiquement l'API client avec Auth0
 * À utiliser dans le composant racine de l'app
 */
export const useApiClient = () => {
  const auth0 = useAuth0();

  useEffect(() => {
    // Configure l'API client avec le contexte Auth0
    apiClient.setAuth0Context(auth0);
  }, [auth0]);

  return apiClient;
};