"""
utilities.py

This module aims to provide several functionalities that are broader on scope than the rest of the source code.
The functions are written in a functional programming style, with lazy evaluation and performance complaince in mind.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Generator

from langchain_openai import AzureChatOpenAI
import numpy as np

def setup_logging(log_file_path: str)-> None:
    """
    Small utility function to set up logging using the python module logging.
    :param log_file_path: The path in which the log will be saved.
    :return: None
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_markdown(markdown_file_name: str, directory_path: str) -> Generator[str, None, None]:
    """
    Generator that yields the content of a markdown file as a string.

    :param markdown_file_name: The name of the markdown file (without extension).
    :param directory_path: The directory where the markdown file is located.
    :yield: The markdown content as a string.
    """
    path = Path(directory_path) / f"{markdown_file_name}.md"
    logging.info(f"Loading markdown from: {path.resolve()}")

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found at: {path.resolve()}")

    yield path.read_text(encoding="utf-8")


def load_json_qa_sample(json_path: str) -> Dict[str, str]:
    """
    Load a JSON file containing Q&A pairs and return a random sample of 5 entries.

    Args:
        json_path (str): Path to the JSON file. The file is expected to contain a list of dictionaries,
                         each representing a Q&A pair.

    Returns:
        Dict[str, str]: A list of 5 randomly selected Q&A dictionaries.
    """
    with open(json_path, "r", encoding="utf-8") as json_file:
        full = json.load(json_file)
    sample = np.random.choice(full, size=5).tolist()
    return sample


def create_engine(params: dict) -> AzureChatOpenAI:
    """
    Create and return an AzureChatOpenAI engine using provided configuration parameters.

    Args:
        params (dict): A dictionary of engine parameters. Expected keys:
                       - "temperature" (float)
                       - "top_p" (float)
                       - "frequency_penalty" (float)
                       - "presence_penalty" (float)

    Returns:
        AzureChatOpenAI: An instance of AzureChatOpenAI configured with the given parameters.
    """
    return AzureChatOpenAI(
        azure_deployment=os.environ["AZURE_DEPLOYMENT"],
        temperature=params.get("temperature", 0.7),
        top_p=params.get("top_p", 1.0),
        frequency_penalty=params.get("frequency_penalty", 0.0),
        presence_penalty=params.get("presence_penalty", 0.0),
    )

