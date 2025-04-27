# backend/llm/advisor_factory.py

import platform

def get_training_advisor(model_name=None, model_endpoint=None):
    """Factory-Funktion, die basierend auf der Umgebung den richtigen Advisor zurückgibt"""
    if platform.system() == "Windows":
        from backend.llm.mock_implementations import MockTrainingAdvisor
        return MockTrainingAdvisor(model_name, model_endpoint)
    else:
        from backend.llm.real_implementations import RealTrainingAdvisor
        return RealTrainingAdvisor(model_name, model_endpoint)