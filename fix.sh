#!/bin/bash

# Entferne die doppelten Frontend-Dateien (behalte nur die in src/frontend/src)
echo "Entferne verbliebene doppelte Strukturen..."

# Entferne doppelte Komponenten-Verzeichnisse
if [ -d "src/frontend/components" ] && [ -d "src/frontend/src/components" ]; then
    rm -rf src/frontend/components
fi

# Entferne doppelte Context-Verzeichnisse
if [ -d "src/frontend/context" ] && [ -d "src/frontend/src/context" ]; then
    rm -rf src/frontend/context
fi

# Entferne doppelte Pages-Verzeichnisse
if [ -d "src/frontend/pages" ] && [ -d "src/frontend/src/pages" ]; then
    rm -rf src/frontend/pages
fi

# Entferne doppelte Services-Verzeichnisse
if [ -d "src/frontend/services" ] && [ -d "src/frontend/src/services" ]; then
    rm -rf src/frontend/services
fi

# Entferne doppelte Styles-Verzeichnisse
if [ -d "src/frontend/styles" ] && [ -d "src/frontend/src/styles" ]; then
    rm -rf src/frontend/styles
fi

echo "Bereinigung abgeschlossen."
