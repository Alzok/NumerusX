import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { Auth0ContextInterface } from '@auth0/auth0-react';

// Configuration de base de l'API
const API_BASE_URL = import.meta.env.VITE_APP_BACKEND_URL || 'http://localhost:8000';

export interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
}

export class ApiClient {
  private axiosInstance: AxiosInstance;
  private auth0Context: Auth0ContextInterface<any> | null = null;

  constructor(config: ApiClientConfig = {}) {
    this.axiosInstance = axios.create({
      baseURL: config.baseURL || API_BASE_URL,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Configure Auth0 context pour l'authentification automatique
   */
  public setAuth0Context(auth0: Auth0ContextInterface<any>) {
    this.auth0Context = auth0;
  }

  /**
   * Configure les intercepteurs pour l'authentification et la gestion d'erreurs
   */
  private setupInterceptors() {
    // Intercepteur de requête : ajouter le token Auth0
    this.axiosInstance.interceptors.request.use(
      async (config) => {
        if (this.auth0Context?.isAuthenticated) {
          try {
            const token = await this.auth0Context.getAccessTokenSilently();
            config.headers.Authorization = `Bearer ${token}`;
          } catch (error) {
            console.warn('Failed to get Auth0 token:', error);
            // Continue sans token - certaines routes peuvent être publiques
          }
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Intercepteur de réponse : gestion d'erreurs globale
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401 && this.auth0Context) {
          // Token expiré ou invalide - essayer de se reconnecter
          try {
            await this.auth0Context.loginWithRedirect();
          } catch (authError) {
            console.error('Failed to redirect to login:', authError);
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // === MÉTHODES HTTP DE BASE ===

  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.get<T>(url, config);
    return response.data;
  }

  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.post<T>(url, data, config);
    return response.data;
  }

  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.put<T>(url, data, config);
    return response.data;
  }

  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.delete<T>(url, config);
    return response.data;
  }

  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.patch<T>(url, data, config);
    return response.data;
  }

  // === MÉTHODES API SPÉCIFIQUES ===

  // Bot Control
  public async getBotStatus() {
    return this.get('/api/v1/bot/status');
  }

  public async startBot() {
    return this.post('/api/v1/bot/start');
  }

  public async stopBot() {
    return this.post('/api/v1/bot/stop');
  }

  public async emergencyStop() {
    return this.post('/api/v1/bot/emergency-stop');
  }

  // Portfolio
  public async getPortfolioSnapshot() {
    return this.get('/api/v1/portfolio/snapshot');
  }

  public async getPortfolioHistory(days?: number) {
    return this.get(`/api/v1/portfolio/history${days ? `?days=${days}` : ''}`);
  }

  // Trades
  public async getTradeHistory(limit = 50, offset = 0) {
    return this.get(`/api/v1/trades/history?limit=${limit}&offset=${offset}`);
  }

  public async executeManualTrade(tradeData: {
    pair: string;
    type: 'BUY' | 'SELL';
    amount_usd: number;
  }) {
    return this.post('/api/v1/trades/manual', tradeData);
  }

  // AI Decisions
  public async getAiDecisionHistory(limit = 50, offset = 0) {
    return this.get(`/api/v1/ai-decisions/history?limit=${limit}&offset=${offset}`);
  }

  public async getAiDecisionDetail(decisionId: string) {
    return this.get(`/api/v1/ai-decisions/${decisionId}`);
  }

  // Configuration
  public async getConfiguration() {
    return this.get('/api/v1/config');
  }

  public async updateConfiguration(config: Record<string, any>) {
    return this.post('/api/v1/config', config);
  }

  // System
  public async getSystemHealth() {
    return this.get('/api/v1/system/health');
  }

  public async getSystemLogs(limit = 100, service?: string) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (service) params.append('service_filter', service);
    return this.get(`/api/v1/system/logs?${params}`);
  }
}

// Instance globale
export const apiClient = new ApiClient();

// Types pour les réponses API
export interface BotStatus {
  is_running: boolean;
  current_pair?: string;
  portfolio_value_usd: number;
  uptime_seconds?: number;
  last_decision_timestamp?: string;
}

export interface PortfolioSnapshot {
  total_value_usd: number;
  pnl_24h_usd: number;
  positions: Array<{
    asset: string;
    amount: number;
    avg_buy_price: number;
    current_price: number;
    value_usd: number;
  }>;
  available_cash_usdc: number;
  timestamp_utc: string;
}

export interface TradeEntry {
  trade_id: string;
  pair: string;
  type: string;
  amount_tokens: number;
  price_usd: number;
  timestamp_utc: string;
  status: string;
  reason_source: string;
}

export interface AiDecisionEntry {
  decision_id: string;
  decision: string;
  token_pair: string;
  confidence: number;
  reasoning_snippet: string;
  timestamp_utc: string;
}

export interface SystemHealth {
  overall_status: string;
  services: Array<{
    service_name: string;
    status: string;
    details?: string;
  }>;
  timestamp_utc: string;
} 
