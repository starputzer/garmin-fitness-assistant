from setuptools import setup, find_packages

setup(
    name="garmin-fitness-assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pandas",
        "numpy",
        "matplotlib",
        "plotly",
        "streamlit",
        "pydantic",
        "python-multipart",
        "requests",
    ],
)
