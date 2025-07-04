"""
client_setup.py

This module contains the llm engines that run inside the graph.
IMPORTANT: Parameters are loaded dynamically from config.yaml and are not hardcoded.
"""

import os

import yaml  # type: ignore
from dotenv import dotenv_values  # type: ignore

from src.utils import create_engine

# Load environment variables from the .env.azure file
env_vars =  os.environ.values()
# Ensure all required environment variables are injected into os.environ
required_keys = [
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "OPENAI_API_VERSION",
    "AZURE_DEPLOYMENT"
]

for key in required_keys:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")


# Load engine parameters from config.yaml
CONFIG_PATH = "src/application/config.yaml"

with open(CONFIG_PATH, "r") as file:
    config = yaml.safe_load(file)

# Engines
GENERATOR_ENGINE = create_engine(config["llm_engines"]["generator"])
EVALUATOR_ENGINE = create_engine(config["llm_engines"]["evaluator"])
REFINER_ENGINE = create_engine(config["llm_engines"]["refiner"])
