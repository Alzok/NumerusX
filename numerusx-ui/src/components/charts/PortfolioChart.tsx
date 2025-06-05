import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

// Enregistrer les composants Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PortfolioDataPoint {
  timestamp: string;
  total_value_usd: number;
  pnl_usd?: number;
}

interface PortfolioChartProps {
  data: PortfolioDataPoint[];
  timeframe?: '24h' | '7d' | '30d' | '90d';
  isLoading?: boolean;
  className?: string;
}

export const PortfolioChart: React.FC<PortfolioChartProps> = ({
  data = [],
  timeframe = '24h',
  isLoading = false,
  className = '',
}) => {
  // Préparation des données pour Chart.js
  const chartData = useMemo(() => {
    if (!data.length) return null;

    const labels = data.map(point => {
      const date = new Date(point.timestamp);
      if (timeframe === '24h') {
        return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      } else {
        return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });
      }
    });

    const values = data.map(point => point.total_value_usd);

    return {
      labels,
      datasets: [
        {
          label: 'Valeur Portfolio (USD)',
          data: values,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: 'rgb(34, 197, 94)',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
        },
      ],
    };
  }, [data, timeframe]);

  // Calcul des statistiques
  const stats = useMemo(() => {
    if (!data.length) return null;

    const firstValue = data[0]?.total_value_usd || 0;
    const lastValue = data[data.length - 1]?.total_value_usd || 0;
    const change = lastValue - firstValue;
    const changePercent = firstValue > 0 ? (change / firstValue) * 100 : 0;

    return {
      current: lastValue,
      change,
      changePercent,
      isPositive: change >= 0,
    };
  }, [data]);

  // Options du graphique
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        callbacks: {
          label: function(context: any) {
            return `Valeur: $${context.raw.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}`;
          }
        }
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          color: '#6b7280',
          font: {
            size: 11,
          },
        },
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          color: '#6b7280',
          font: {
            size: 11,
          },
          callback: function(value: any) {
            return '$' + value.toLocaleString('fr-FR');
          }
        },
      },
    },
  };

  if (isLoading) {
    return (
      <div className={`bg-card rounded-lg border p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (!data.length || !chartData || !stats) {
    return (
      <div className={`bg-card rounded-lg border p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <DollarSign className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-500">Aucune donnée disponible</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-card rounded-lg border p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold mb-1">Évolution du Portfolio</h3>
          <div className="flex items-center space-x-4">
            <div className="text-2xl font-bold">
              ${stats.current.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
            </div>
            <div className={`flex items-center space-x-1 ${
              stats.isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
              {stats.isPositive ? 
                <TrendingUp className="h-4 w-4" /> : 
                <TrendingDown className="h-4 w-4" />
              }
              <span className="text-sm font-medium">
                {stats.isPositive ? '+' : ''}${stats.change.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
              </span>
              <span className="text-sm">
                ({stats.isPositive ? '+' : ''}{stats.changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}; 
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

// Enregistrer les composants Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PortfolioDataPoint {
  timestamp: string;
  total_value_usd: number;
  pnl_usd?: number;
}

interface PortfolioChartProps {
  data: PortfolioDataPoint[];
  timeframe?: '24h' | '7d' | '30d' | '90d';
  isLoading?: boolean;
  className?: string;
}

export const PortfolioChart: React.FC<PortfolioChartProps> = ({
  data = [],
  timeframe = '24h',
  isLoading = false,
  className = '',
}) => {
  // Préparation des données pour Chart.js
  const chartData = useMemo(() => {
    if (!data.length) return null;

    const labels = data.map(point => {
      const date = new Date(point.timestamp);
      if (timeframe === '24h') {
        return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      } else {
        return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });
      }
    });

    const values = data.map(point => point.total_value_usd);

    return {
      labels,
      datasets: [
        {
          label: 'Valeur Portfolio (USD)',
          data: values,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: 'rgb(34, 197, 94)',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
        },
      ],
    };
  }, [data, timeframe]);

  // Calcul des statistiques
  const stats = useMemo(() => {
    if (!data.length) return null;

    const firstValue = data[0]?.total_value_usd || 0;
    const lastValue = data[data.length - 1]?.total_value_usd || 0;
    const change = lastValue - firstValue;
    const changePercent = firstValue > 0 ? (change / firstValue) * 100 : 0;

    return {
      current: lastValue,
      change,
      changePercent,
      isPositive: change >= 0,
    };
  }, [data]);

  // Options du graphique
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        callbacks: {
          label: function(context: any) {
            return `Valeur: $${context.raw.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}`;
          }
        }
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          color: '#6b7280',
          font: {
            size: 11,
          },
        },
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          color: '#6b7280',
          font: {
            size: 11,
          },
          callback: function(value: any) {
            return '$' + value.toLocaleString('fr-FR');
          }
        },
      },
    },
  };

  if (isLoading) {
    return (
      <div className={`bg-card rounded-lg border p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (!data.length || !chartData || !stats) {
    return (
      <div className={`bg-card rounded-lg border p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <DollarSign className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-500">Aucune donnée disponible</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-card rounded-lg border p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold mb-1">Évolution du Portfolio</h3>
          <div className="flex items-center space-x-4">
            <div className="text-2xl font-bold">
              ${stats.current.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
            </div>
            <div className={`flex items-center space-x-1 ${
              stats.isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
              {stats.isPositive ? 
                <TrendingUp className="h-4 w-4" /> : 
                <TrendingDown className="h-4 w-4" />
              }
              <span className="text-sm font-medium">
                {stats.isPositive ? '+' : ''}${stats.change.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
              </span>
              <span className="text-sm">
                ({stats.isPositive ? '+' : ''}{stats.changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}; 