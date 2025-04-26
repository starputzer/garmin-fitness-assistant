#!/bin/bash

# Farben für bessere Lesbarkeit
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Garmin Fitness Assistant - Setup Script (Standard React-Struktur) ===${NC}"
echo -e "Dieses Script richtet eine standardmäßige React-Projektstruktur ein"

# Stellen Sie sicher, dass wir im Hauptverzeichnis des Projekts sind
MAIN_DIR="/opt/garmin-fitness-assistant"
if [ ! -d "$MAIN_DIR" ]; then
  echo -e "${RED}Fehler: Das Hauptverzeichnis $MAIN_DIR existiert nicht${NC}"
  exit 1
fi

cd "$MAIN_DIR"
echo -e "${YELLOW}Arbeite im Verzeichnis: $(pwd)${NC}"

# Erstelle eine saubere Projektstruktur
echo -e "${GREEN}Erstelle Standard-Projektstruktur...${NC}"

# Backend
mkdir -p backend/analysis
mkdir -p backend/api
mkdir -p backend/llm
mkdir -p backend/parsers

# Frontend mit Standard React-Struktur
mkdir -p frontend/public
mkdir -p frontend/src/components/analysis
mkdir -p frontend/src/components/dashboard
mkdir -p frontend/src/components/upload
mkdir -p frontend/src/context
mkdir -p frontend/src/pages
mkdir -p frontend/src/services
mkdir -p frontend/src/styles

# Gemeinsame Module
mkdir -p common

# Andere Verzeichnisse
mkdir -p data/storage
mkdir -p docs
mkdir -p tests

# Prüfe, ob Frontend-Dateien bereits existieren und kopiere sie in die neue Struktur
echo -e "${GREEN}Kopiere existierende Dateien in die neue Struktur...${NC}"

# Kopiere Backend-Dateien
if [ -d "src/backend" ]; then
  echo -e "${YELLOW}Kopiere Backend-Dateien...${NC}"
  cp -r src/backend/analysis/* backend/analysis/ 2>/dev/null || :
  cp -r src/backend/api/* backend/api/ 2>/dev/null || :
  cp -r src/backend/llm/* backend/llm/ 2>/dev/null || :
  cp -r src/backend/parsers/* backend/parsers/ 2>/dev/null || :
fi

# Kopiere Common-Dateien
if [ -d "src/common" ]; then
  echo -e "${YELLOW}Kopiere gemeinsame Module...${NC}"
  cp -r src/common/* common/ 2>/dev/null || :
fi

# Kopiere Frontend-Dateien
if [ -d "src/frontend" ]; then
  echo -e "${YELLOW}Kopiere Frontend-Dateien...${NC}"
  
  # Komponenten
  if [ -d "src/frontend/components" ]; then
    echo "  Kopiere Komponenten..."
    cp -r src/frontend/components/analysis/* frontend/src/components/analysis/ 2>/dev/null || :
    cp -r src/frontend/components/dashboard/* frontend/src/components/dashboard/ 2>/dev/null || :
    cp -r src/frontend/components/upload/* frontend/src/components/upload/ 2>/dev/null || :
    
    # Layout und Navbar
    if [ -f "src/frontend/components/Layout.jsx" ]; then
      cp src/frontend/components/Layout.jsx frontend/src/components/ 2>/dev/null || :
    fi
    
    if [ -f "src/frontend/components/Navbar.jsx" ]; then
      cp src/frontend/components/Navbar.jsx frontend/src/components/ 2>/dev/null || :
    fi
  fi
  
  # Context
  if [ -d "src/frontend/context" ]; then
    echo "  Kopiere Context-Dateien..."
    cp -r src/frontend/context/* frontend/src/context/ 2>/dev/null || :
  fi
  
  # Pages
  if [ -d "src/frontend/pages" ]; then
    echo "  Kopiere Pages..."
    cp -r src/frontend/pages/* frontend/src/pages/ 2>/dev/null || :
  fi
  
  # Services
  if [ -d "src/frontend/services" ]; then
    echo "  Kopiere Services..."
    cp -r src/frontend/services/* frontend/src/services/ 2>/dev/null || :
  fi
  
  # Styles
  if [ -d "src/frontend/styles" ]; then
    echo "  Kopiere Styles..."
    cp -r src/frontend/styles/* frontend/src/styles/ 2>/dev/null || :
  fi
  
  # App.jsx
  if [ -f "src/frontend/App.jsx" ]; then
    echo "  Kopiere App.jsx..."
    cp src/frontend/App.jsx frontend/src/ 2>/dev/null || :
  fi
  
  # index.html
  if [ -f "src/frontend/public/index.html" ]; then
    echo "  Kopiere index.html..."
    cp src/frontend/public/index.html frontend/public/ 2>/dev/null || :
  fi
  
  # package.json
  if [ -f "src/frontend/package.json" ]; then
    echo "  Kopiere package.json..."
    cp src/frontend/package.json frontend/ 2>/dev/null || :
  fi
  
  # package-lock.json
  if [ -f "src/frontend/package-lock.json" ]; then
    echo "  Kopiere package-lock.json..."
    cp src/frontend/package-lock.json frontend/ 2>/dev/null || :
  fi
fi

# Erstelle index.js
echo -e "${GREEN}Erstelle index.js...${NC}"
cat > frontend/src/index.js << 'EOF'
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
if [ ! -f "frontend/public/index.html" ]; then
  echo -e "${GREEN}Erstelle index.html...${NC}"
  cat > frontend/public/index.html << 'EOF'
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
if [ ! -f "frontend/src/App.jsx" ]; then
  echo -e "${GREEN}Erstelle minimale App.jsx...${NC}"
  cat > frontend/src/App.jsx << 'EOF'
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

# Erstelle package.json falls nicht vorhanden
if [ ! -f "frontend/package.json" ]; then
  echo -e "${GREEN}Erstelle package.json...${NC}"
  cat > frontend/package.json << 'EOF'
{
  "name": "garmin-fitness-assistant-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "axios": "^1.9.0",
    "chart.js": "^4.4.9",
    "react": "^19.1.0",
    "react-chartjs-2": "^5.3.0",
    "react-dom": "^19.1.0",
    "react-router-dom": "^7.5.2"
  },
  "devDependencies": {
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
EOF
fi

# Erstelle main.py für Backend
echo -e "${GREEN}Erstelle main.py für Backend...${NC}"
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
Garmin Fitness Assistant - Hauptskript

Dieses Skript startet den Garmin Fitness Assistant
mit der angegebenen Konfiguration.
"""

import os
import sys
import argparse
from pathlib import Path

# Backend Module
from backend.api.web_api import WebAPI
from backend.parsers.garmin_parser import GarminParser
from backend.analysis.run_analyzer import RunAnalyzer
from backend.llm.training_advisor import LLMTrainingAdvisor
from common.data_repository import GarminDataRepository

def parse_args():
    parser = argparse.ArgumentParser(description='Garmin Fitness Assistant')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=8000, help='Port number')
    parser.add_argument('--data-dir', type=str, default='./data', help='Data directory')
    parser.add_argument('--storage-dir', type=str, default='./data/storage', help='Storage directory')
    parser.add_argument('--model-name', type=str, default='llama3:8b-instruct-q4_1', help='LLM model name')
    parser.add_argument('--model-endpoint', type=str, default='http://localhost:11434', help='LLM API endpoint')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Verzeichnisse erstellen, falls nicht vorhanden
    os.makedirs(args.data_dir, exist_ok=True)
    os.makedirs(args.storage_dir, exist_ok=True)
    
    # Komponenten initialisieren
    print(f"Initialisiere Komponenten...")
    parser = GarminParser(data_dir=args.data_dir)
    analyzer = RunAnalyzer()
    advisor = LLMTrainingAdvisor(model_name=args.model_name, model_endpoint=args.model_endpoint)
    repository = GarminDataRepository(storage_path=args.storage_dir)
    
    # API initialisieren und starten
    print(f"Starte API-Server auf {args.host}:{args.port}...")
    api = WebAPI(
        host=args.host,
        port=args.port,
        parser=parser,
        analyzer=analyzer,
        advisor=advisor,
        repository=repository
    )
    
    api.start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

# Erstelle .gitignore oder aktualisiere sie
if [ -f ".gitignore" ]; then
  echo -e "${GREEN}Aktualisiere .gitignore...${NC}"
  
  # Füge Frontend-spezifische Einträge hinzu
  grep -q "frontend/node_modules/" .gitignore || echo "frontend/node_modules/" >> .gitignore
  grep -q "frontend/build/" .gitignore || echo "frontend/build/" >> .gitignore
  grep -q "frontend/.env" .gitignore || echo "frontend/.env" >> .gitignore
  grep -q "frontend/npm-debug.log" .gitignore || echo "frontend/npm-debug.log*" >> .gitignore
else
  echo -e "${GREEN}Erstelle .gitignore...${NC}"
  cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/

# Virtuelle Umgebungen
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Frontend
frontend/node_modules/
frontend/build/
frontend/.env
frontend/.env.local
frontend/.env.development.local
frontend/.env.test.local
frontend/.env.production.local
frontend/npm-debug.log*
frontend/yarn-debug.log*
frontend/yarn-error.log*

# Daten
data/
*.csv
*.json
uploads/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Logs
logs/
*.log

# Betriebssystem
.DS_Store
Thumbs.db
EOF
fi

# Erstelle README.md falls nicht vorhanden
if [ ! -f "README.md" ]; then
  echo -e "${GREEN}Erstelle README.md...${NC}"
  cat > README.md << 'EOF'
# Garmin Fitness Assistant

Ein Python-basierter Assistent zur Analyse von Garmin-Fitnessdaten und Generierung von personalisierten Trainingsempfehlungen.

## Features

- Verarbeitung von Garmin-Exportdaten
- Analyse von Laufmetriken und Fortschritt
- Personalisierte Trainingsempfehlungen basierend auf individuellen Daten
- Web-Interface zur Visualisierung von Daten und Prognosen

## Installation

### Backend (Python)

```bash
# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # oder unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Frontend (React)

```bash
# In das Frontend-Verzeichnis wechseln
cd frontend

# Abhängigkeiten installieren
npm install
```

## Ausführen

### Backend starten

```bash
python main.py --host 0.0.0.0 --port 8000
```

### Frontend starten

```bash
cd frontend
npm start
```

Die Anwendung ist dann unter http://localhost:3000 verfügbar, während das Backend unter http://localhost:8000 läuft.

## Daten importieren

Exportieren Sie Ihre Daten aus Garmin Connect und laden Sie die folgenden Dateien hoch:
- RunRacePredictions_*.json
- TrainingHistory_*.json
- MetricsHeatAltitudeAcclimation_*.json
- SummarizedActivities_*.json
EOF
fi

echo -e "${GREEN}Setup abgeschlossen!${NC}"
echo -e "Die Projektstruktur wurde in eine Standard-React-Struktur umgewandelt."
echo -e "Bitte beachten Sie folgende Änderungen:"
echo -e "${YELLOW}1. Backend-Code ist jetzt in /backend/ statt in /src/backend/${NC}"
echo -e "${YELLOW}2. Frontend-Code ist jetzt in /frontend/ statt in /src/frontend/${NC}"
echo -e "${YELLOW}3. main.py wurde im Hauptverzeichnis erstellt, um das Backend zu starten${NC}"
echo -e ""
echo -e "Installieren Sie die Node-Module im Frontend-Verzeichnis:"
echo -e "${GREEN}cd frontend && npm install${NC}"
echo -e ""
echo -e "Starten Sie das Backend mit:"
echo -e "${GREEN}python main.py${NC}"
echo -e ""
echo -e "Starten Sie das Frontend mit:"
echo -e "${GREEN}cd frontend && npm start${NC}"
echo -e ""
echo -e "${YELLOW}HINWEIS: Möglicherweise müssen Import-Pfade in den React- und Python-Dateien angepasst werden.${NC}"
