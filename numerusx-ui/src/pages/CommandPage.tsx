import React from 'react';

const CommandPage: React.FC = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-4">Command Center</h1>
      <div className="bg-card p-6 rounded-lg shadow-md">
        <p className="text-muted-foreground">
          Bot controls, strategy selection, and manual trade entry will be available here.
        </p>
        {/* Placeholder for control elements */}
      </div>
    </div>
  );
};

export default CommandPage; 