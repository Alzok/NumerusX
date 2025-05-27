import React from 'react';
import { useTranslation } from 'react-i18next';

const DashboardPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-4">{t('dashboard.title')}</h1>
      <div className="bg-card p-6 rounded-lg shadow-md">
        <p className="text-muted-foreground">
          {t('dashboard.welcomeMessage')}
        </p>
        {/* Placeholder for charts and data widgets */}
      </div>
    </div>
  );
};

export default DashboardPage; 