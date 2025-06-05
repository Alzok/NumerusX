import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { Auth0Provider } from '@auth0/auth0-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { store } from './app/store'
import App from './App.tsx'
import './lib/i18n'
import './index.css'

// Configuration React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

// Auth0 Configuration - REMPLACEZ PAR VOS VALEURS REELLES (.env)
const AUTH0_DOMAIN = import.meta.env.VITE_APP_AUTH0_DOMAIN || "YOUR_AUTH0_DOMAIN"
const AUTH0_CLIENT_ID = import.meta.env.VITE_APP_AUTH0_CLIENT_ID || "YOUR_AUTH0_CLIENT_ID"
const AUTH0_AUDIENCE = import.meta.env.VITE_APP_AUTH0_AUDIENCE || "YOUR_API_IDENTIFIER" // Si vous protégez une API backend

if (!AUTH0_DOMAIN || AUTH0_DOMAIN === "YOUR_AUTH0_DOMAIN" || 
    !AUTH0_CLIENT_ID || AUTH0_CLIENT_ID === "YOUR_AUTH0_CLIENT_ID") {
  console.warn(
    "Auth0 domain or client ID is not configured. Please set VITE_APP_AUTH0_DOMAIN and VITE_APP_AUTH0_CLIENT_ID in your .env file."
  )
  // Vous pourriez vouloir afficher une erreur à l'utilisateur ou désactiver les fonctionnalités d'auth ici
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Auth0Provider
        domain={AUTH0_DOMAIN}
        clientId={AUTH0_CLIENT_ID}
        authorizationParams={{
          redirect_uri: window.location.origin + '/dashboard', // Ou une page de callback dédiée
          audience: AUTH0_AUDIENCE, // Si applicable
          scope: "openid profile email read:current_user update:current_user_metadata" // Exemple de scopes
        }}
        cacheLocation="localstorage" // Recommandé pour les SPAs
      >
        <Provider store={store}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </Provider>
      </Auth0Provider>
    </QueryClientProvider>
  </React.StrictMode>,
) 