import platform
import os

# Standard-Konfiguration
CONFIG = {
    "use_mock_llm": platform.system() == "Windows",
    "data_dir": "./data",
    "storage_dir": "./data/storage",
    # Weitere Konfigurationsoptionen...
}

# Überschreiben mit Umgebungsvariablen
if os.environ.get("USE_MOCK_LLM") is not None:
    CONFIG["use_mock_llm"] = os.environ.get("USE_MOCK_LLM") == "1"