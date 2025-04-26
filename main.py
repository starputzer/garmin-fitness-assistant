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
