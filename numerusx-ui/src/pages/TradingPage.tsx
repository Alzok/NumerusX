import React from 'react';

const TradingPage: React.FC = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-4">Trading Activity</h1>
      <div className="bg-card p-6 rounded-lg shadow-md">
        <p className="text-muted-foreground">
          Recent trades, open orders, and performance analysis will be shown here.
        </p>
        {/* Placeholder for trade tables and charts */}
      </div>
    </div>
  );
};

export default TradingPage; 