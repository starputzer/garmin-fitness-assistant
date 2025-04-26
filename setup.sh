#!/bin/bash

# Farben für bessere Lesbarkeit
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Garmin Fitness Assistant - Setup Script ===${NC}"
echo -e "Dieses Script richtet die korrekte Verzeichnisstruktur ein"

# Stellen Sie sicher, dass wir im Hauptverzeichnis des Projekts sind
MAIN_DIR="/opt/garmin-fitness-assistant"
if [ ! -d "$MAIN_DIR" ]; then
  echo -e "${RED}Fehler: Das Hauptverzeichnis $MAIN_DIR existiert nicht${NC}"
  exit 1
fi

cd "$MAIN_DIR"
echo -e "${YELLOW}Arbeite im Verzeichnis: $(pwd)${NC}"

# Erstelle Backend-Struktur (falls nicht vorhanden)
echo -e "${GREEN}Erstelle Backend-Struktur...${NC}"
mkdir -p src/backend/analysis
mkdir -p src/backend/api
mkdir -p src/backend/llm
mkdir -p src/backend/parsers
mkdir -p src/common
mkdir -p tests
mkdir -p docs
mkdir -p data/storage

# Erstelle frontend-src Verzeichnis (Standard React-Struktur)
echo -e "${GREEN}Erstelle Frontend-Struktur...${NC}"
mkdir -p src/frontend/public
mkdir -p src/frontend/src/components/analysis
mkdir -p src/frontend/src/components/dashboard
mkdir -p src/frontend/src/components/upload
mkdir -p src/frontend/src/context
mkdir -p src/frontend/src/pages
mkdir -p src/frontend/src/services
mkdir -p src/frontend/src/styles

# Prüfe, ob Frontend-Dateien bereits existieren und verschiebe sie
echo -e "${GREEN}Verschiebe Frontend-Dateien in die korrekte Struktur...${NC}"

# Verschiebe vorhandene Komponenten
if [ -d "src/frontend/components" ]; then
  echo -e "${YELLOW}Verschiebe Komponenten...${NC}"
  
  # Analysis-Komponenten
  if [ -d "src/frontend/components/analysis" ]; then
    cp -r src/frontend/components/analysis/* src/frontend/src/components/analysis/ 2>/dev/null || :
    echo "  Analysis-Komponenten verschoben"
  fi
  
  # Dashboard-Komponenten
  if [ -d "src/frontend/components/dashboard" ]; then
    cp -r src/frontend/components/dashboard/* src/frontend/src/components/dashboard/ 2>/dev/null || :
    echo "  Dashboard-Komponenten verschoben"
  fi
  
  # Upload-Komponenten
  if [ -d "src/frontend/components/upload" ]; then
    cp -r src/frontend/components/upload/* src/frontend/src/components/upload/ 2>/dev/null || :
    echo "  Upload-Komponenten verschoben"
  fi
  
  # Layout und Navbar
  if [ -f "src/frontend/components/Layout.jsx" ]; then
    cp src/frontend/components/Layout.jsx src/frontend/src/components/ 2>/dev/null || :
    echo "  Layout.jsx verschoben"
  fi
  
  if [ -f "src/frontend/components/Navbar.jsx" ]; then
    cp src/frontend/components/Navbar.jsx src/frontend/src/components/ 2>/dev/null || :
    echo "  Navbar.jsx verschoben"
  fi
fi

# Verschiebe Context-Dateien
if [ -d "src/frontend/context" ]; then
  echo -e "${YELLOW}Verschiebe Context-Dateien...${NC}"
  cp -r src/frontend/context/* src/frontend/src/context/ 2>/dev/null || :
fi

# Verschiebe Pages
if [ -d "src/frontend/pages" ]; then
  echo -e "${YELLOW}Verschiebe Pages...${NC}"
  cp -r src/frontend/pages/* src/frontend/src/pages/ 2>/dev/null || :
fi

# Verschiebe Services
if [ -d "src/frontend/services" ]; then
  echo -e "${YELLOW}Verschiebe Services...${NC}"
  cp -r src/frontend/services/* src/frontend/src/services/ 2>/dev/null || :
fi

# Verschiebe Styles
if [ -d "src/frontend/styles" ]; then
  echo -e "${YELLOW}Verschiebe Styles...${NC}"
  cp -r src/frontend/styles/* src/frontend/src/styles/ 2>/dev/null || :
fi

# Verschiebe App.jsx
if [ -f "src/frontend/App.jsx" ]; then
  echo -e "${YELLOW}Verschiebe App.jsx...${NC}"
  cp src/frontend/App.jsx src/frontend/src/ 2>/dev/null || :
fi

# Erstelle index.js falls nicht vorhanden
echo -e "${GREEN}Erstelle index.js...${NC}"
cat > src/frontend/src/index.js << 'EOF'
import React from 'react';
import { createRoot } from 'react-dom/client';
import './styles/main.css';
import App from './App';

const root = createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# Erstelle index.html falls nicht vorhanden
if [ ! -f "src/frontend/public/index.html" ]; then
  echo -e "${GREEN}Erstelle index.html...${NC}"
  cat > src/frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Garmin Fitness Assistant</title>
  </head>
  <body>
    <noscript>Sie müssen JavaScript aktivieren, um diese App zu nutzen.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF
fi

# Erstelle eine Minimale App.jsx falls sie nicht existiert
if [ ! -f "src/frontend/src/App.jsx" ]; then
  echo -e "${GREEN}Erstelle minimale App.jsx...${NC}"
  cat > src/frontend/src/App.jsx << 'EOF'
import React from 'react';
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';

// Einfache Komponenten für den Start
const Layout = () => (
  <div>
    <h1>Garmin Fitness Assistant</h1>
    <Outlet />
  </div>
);

const Home = () => <div>Willkommen zur Garmin Fitness Assistant App</div>;

// Router für React Router 7
const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Home />
      }
    ]
  }
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
EOF
fi

echo -e "${GREEN}Setup abgeschlossen!${NC}"
echo -e "Sie können nun in das Verzeichnis 'src/frontend' wechseln und 'npm start' ausführen."
echo -e "${YELLOW}HINWEIS: Möglicherweise müssen Import-Pfade in den React-Dateien angepasst werden.${NC}"
