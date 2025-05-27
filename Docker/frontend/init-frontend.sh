#!/bin/sh
set -e

# Directory where the frontend app should reside inside the container
APP_DIR="/app/numerusx-ui"
PACKAGE_JSON_PATH="${APP_DIR}/package.json"

# Check if package.json exists. If not, initialize the project.
if [ ! -f "$PACKAGE_JSON_PATH" ]; then
  echo "No existing project found at $APP_DIR. Initializing new Vite + React + TS project..."

  # Create the target directory if it doesn't exist (it should, due to docker volume mount, but good practice)
  mkdir -p $APP_DIR
  cd $APP_DIR

  # 1. Initialize Vite Project (React + TypeScript)
  # npm create vite@latest . -- --template react-ts
  # The above command is interactive. We need a non-interactive way.
  # Vite itself doesn't offer a direct non-interactive template selection via CLI flags easily for `npm create vite`.
  # Alternative: Use a community template or scaffold manually.
  # For simplicity, we'll assume a basic structure is created or use a degit-like approach if needed.
  # Let's try with the standard way and see if it can be made non-interactive by piping defaults or using flags if available.

  echo "Initializing Vite project... (This might take a moment)"
  # Create a minimal package.json to start with
  echo '{
    "name": "numerusx-ui",
    "private": true,
    "version": "0.0.0",
    "type": "module"
  }' > package.json

  # Install Vite, React, TypeScript, and related dependencies
  npm install vite@latest @vitejs/plugin-react typescript react react-dom @types/react @types/react-dom

  # Create basic Vite config
  echo 'import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Listen on all addresses, including 0.0.0.0
    port: 5173
  }
})' > vite.config.ts

  # Create tsconfig.json
  echo '{
    "compilerOptions": {
      "target": "ES2020",
      "useDefineForClassFields": true,
      "lib": ["ES2020", "DOM", "DOM.Iterable"],
      "module": "ESNext",
      "skipLibCheck": true,
      "moduleResolution": "bundler",
      "allowImportingTsExtensions": true,
      "resolveJsonModule": true,
      "isolatedModules": true,
      "noEmit": true,
      "jsx": "react-jsx",
      "strict": true,
      "noUnusedLocals": true,
      "noUnusedParameters": true,
      "noFallthroughCasesInSwitch": true
    },
    "include": ["src"],
    "references": [{ "path": "./tsconfig.node.json" }]
  }' > tsconfig.json

  echo '{
    "compilerOptions": {
      "composite": true,
      "skipLibCheck": true,
      "module": "ESNext",
      "moduleResolution": "bundler",
      "allowSyntheticDefaultImports": true
    },
    "include": ["vite.config.ts"]
  }' > tsconfig.node.json

  # Create public directory and index.html
  mkdir public
  echo '<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NumerusX UI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>' > public/index.html
  cp ../logo.jpg public/vite.svg # Placeholder icon, assuming logo.jpg is in parent of numerusx-ui

  # Create src directory and basic files
  mkdir src
  echo 'import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App.tsx"
import "./index.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)' > src/main.tsx

  echo 'function App() {
  return (
    <>
      <h1>Welcome to NumerusX UI (Vite + React + TS)</h1>
    </>
  )
}

export default App' > src/App.tsx

  echo '' > src/index.css # Empty CSS file for now, Tailwind will populate

  echo "Vite project initialized."

  # 2. Install Tailwind CSS
  echo "Installing Tailwind CSS..."
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  echo "Tailwind CSS installed and initialized."

  # 3. Setup Shadcn UI (non-interactive using defaults)
  echo "Setting up Shadcn UI..."
  # Shadcn UI typically requires an interactive init. We'll create a default components.json
  # and guide the user to run `npx shadcn-ui add <component>` later.

  echo '{
    "$schema": "https://ui.shadcn.com/schema.json",
    "style": "default",
    "rsc": false,
    "tsx": true,
    "tailwind": {
      "config": "tailwind.config.js",
      "css": "src/index.css",
      "baseColor": "slate",
      "cssVariables": true
    },
    "aliases": {
      "components": "@/components",
      "utils": "@/lib/utils"
    }
  }' > components.json

  # Configure tailwind.config.js for Shadcn UI
  # This is a basic configuration. User might need to adjust.
  echo "Configuring Tailwind for Shadcn UI..."
  sed -i 's|content: \[\]|content: [\n    ".\/pages\/\*\*\/\*.{ts,tsx}",\n    ".\/components\/\*\*\/\*.{ts,tsx}",\n    ".\/app\/\*\*\/\*.{ts,tsx}",\n    ".\/src\/\*\*\/\*.{ts,tsx}",\n  ]|g' tailwind.config.js

cat << EOF > tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './features/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
	],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
EOF

  # Configure src/index.css for Tailwind base styles + Shadcn UI variables
  echo "Configuring CSS for Tailwind and Shadcn UI..."
cat << EOF > src/index.css
@tailwind base;
@tailwind components;
@tailwind utilities;
 
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
 
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
 
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
 
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
 
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
 
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
 
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
 
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
 
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
 
    --radius: 0.5rem;
  }
 
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
 
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
 
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
 
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
 
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
 
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
 
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
 
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
 
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 215 20.2% 65.1%;
  }
}
 
@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
EOF

  echo "Shadcn UI basic setup complete. You may need to run 'npx shadcn-ui@latest add <component_name>' for specific components."
  echo "Initial project setup finished."

else
  echo "Existing project found at $APP_DIR. Skipping initialization."
  cd $APP_DIR
fi

# Always run install in case dependencies changed
echo "Running npm install..."
npm install

# Start the development server
echo "Starting Vite development server on port 5173..."
npm run dev -- --host 0.0.0.0 