"""
utilities.py

This module aims to provide several functionalities that are broader on scope than the rest of the source code.
The functions are written in a functional programming style, with lazy evaluation and performance complaince in mind.
"""
import json
import logging
import os
import random
from pathlib import Path
from typing import Any,Coroutine, Dict, Generator, List

import aiohttp
import ijson
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from src.models import StateDictionary

load_dotenv(dotenv_path=".env.embedding")

AZURE_RESOURCE = os.getenv("ENDPOINT").rstrip("/")
DEPLOYMENT = os.getenv("DEPLOYMENT")
API_VERSION = os.getenv("API_VERSION")
AZURE_EMBEDDING_ENDPOINT = f"{AZURE_RESOURCE}/openai/deployments/{DEPLOYMENT}/embeddings?api-version={API_VERSION}"
AZURE_API_KEY = os.getenv("CREDENTIALS")






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


def lazy_load_json_qa_sample(json_path: str, sample_size: int = 5) -> List[Dict[str, Any]]:
    """
    Loads lazily a JSON file containing Q&A pairs and return a random sample of 5 entries.
    This function uses the reservoir sampling algorithm for memory efficient loads and selection
    of the samples.

    Args:
        json_path (str): Path to the JSON file. The file is expected to contain a list of dictionaries,
                         each representing a Q&A pair.
        sample_size (int, optional): Number of entries to return. Defaults to 5.

    Returns:
        List[Dict[str, str]]: A list of 5 randomly selected Q&A dictionaries.

    """
    reservoir = []
    try:
        with open(json_path, "r", encoding="utf-8") as json_file:
            parser = ijson.items(json_file, "item")
            for index, item in enumerate(parser):
                if index < sample_size:
                    reservoir.append(item)

                else:
                    j = random.randint(0, index)
                    if j < sample_size:
                        reservoir[j] = item
        return reservoir
    except FileNotFoundError:

        raise FileNotFoundError(f"Prompt file not found at: {json_path}")





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

async def encode_document(doc: str) -> List[float]:
    """
    Encodes the title using Azure embedding endpoint and returns a document dict.
    """

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }
    payload = {
        "input": doc
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(AZURE_EMBEDDING_ENDPOINT, headers=headers, json=payload) as resp:
            response_data = await resp.json()

            vector = response_data.get("data", [{}])[0].get("embedding")

            if not vector:
                raise ValueError(f"Failed to extract embedding from response: {response_data}")

            return  vector

async def save_conformed_points_for_internal_search(state: StateDictionary)->Coroutine[None,None, Dict[str, Any]| None]:
    """

    :param state:
    :return:
    """
    state["upload_author"] = str(state["upload_author"]) #workaround for an error of json serialization.
    cleaned_state = {
        **state,
        "refined_qa": [
            {k: v for k, v in qa_item.items() if k != "vector"}
            for qa_item in state.get("refined_qa", [])
        ]
    }
    with open("assets/processed_docs/processed_documents.jsonl", "a", encoding="utf-8") as json_file:
        json_file.write(json.dumps(cleaned_state) + "\n")