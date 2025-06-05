import * as React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="border-t py-6 md:py-0">
      <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
        <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
          Built by NumerusX Team. The source code is available on GitHub (Placeholder).
        </p>
        <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
                Status: <span className="text-green-500 font-semibold">Operational (Placeholder)</span>
            </span>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 