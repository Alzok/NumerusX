import { withAuthenticationRequired } from "@auth0/auth0-react";
import React, { ComponentType } from "react";

interface AuthenticationGuardProps {
  component: ComponentType;
}

export const AuthenticationGuard: React.FC<AuthenticationGuardProps> = ({ component }) => {
  const Component = withAuthenticationRequired(component, {
    // Show a loading indicator while the user is redirecting to Auth0
    // or when checking the session
    onRedirecting: () => (
      <div className="flex items-center justify-center h-screen">
        <p className="text-lg text-muted-foreground">Redirecting to login...</p>
        {/* You can add a spinner or a more sophisticated loading component here */}
      </div>
    ),
  });

  return <Component />;
}; 