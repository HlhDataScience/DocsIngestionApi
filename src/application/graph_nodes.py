from typing import List, Coroutine

from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_core.documents import Document
from langchain_text_splitters import NLTKTextSplitter

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.models.response_schemas import GraphStateResponse
from .client_setup import LLM_ENGINE
from .graph_constructor import StateDictionary
import os
from typing import Any, Dict, Coroutine
from dotenv import load_dotenv
import aiohttp

from application.graph_constructor import StateDictionary
from models import QdrantValidator, DocxValidator
from src.client.implementations import QdrantClientAsync

def parse_wordformat_document(state: StateDictionary, document_path: str)->StateDictionary:

    loader_instance = UnstructuredWordDocumentLoader(document_path)

    docs: List[Document] = loader_instance.load_and_split(
        text_splitter=NLTKTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
    )

    state["status"]  = "Parsing docx file step completed"
    state["original_document"] = "\n".join(d.page_content for d in docs )
    return state



async def worker1_node(state:StateDictionary)-> Coroutine[None, None, StateDictionary]:

    if "error" in state:
        return state

    try:
        llm = LLM_ENGINE

        parser = JsonOutputParser(pydantic_object=GraphStateResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "something here"
                ),
                (
                    "user",
                    "something here using {docs}\n\n{format_instructions}"
                ),
            ]
        )

        chain =  prompt | llm | parser

        result = chain.ainvoke(
            {
                "text" : state["original_document"],
                "format_instructions" : parser.get_instructions(),
            }
        )
        state["worker1_generated_qa"] = result
        return state
    except Exception as e:
        state["error"] = {
            "status": "error",
            "message": str(e),
        }
    return state

async def evaluator(state: StateDictionary)-> StateDictionary:

    if "error" in state:
        return state

    try:
        llm = LLM_ENGINE

        parser = JsonOutputParser(pydantic_object=GraphStateResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "something here"
                ),
                (
                    "user",
                    "something here using {docs}\n\n{format_instructions}"
                ),
            ]
        )

        chain =  prompt | llm | parser

        result = chain.ainvoke(
            {
                "text" : state["original_document"],
                "format_instructions" : parser.get_instructions(),
            }
        )
        state["worker1_generated_qa"] = result
        return state
    except Exception as e:
        state["error"] = {
            "status": "error",
            "message": str(e),
        }
    return state


async def worker2_node(state:StateDictionary)-> StateDictionary:

    if "error" in state:
        return state

    try:
        llm = LLM_ENGINE

        parser = JsonOutputParser(pydantic_object=GraphStateResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "something here"
                ),
                (
                    "user",
                    "something here using {docs}\n\n{format_instructions}"
                ),
            ]
        )

        chain =  prompt | llm | parser

        result = chain.ainvoke(
            {
                "text" : state["original_document"],
                "format_instructions" : parser.get_instructions(),
            }
        )
        state["worker2_generated_qa"] = result
        return state
    except Exception as e:
        state["error"] = {
            "status": "error",
            "message": str(e),
        }
    return state




load_dotenv(dotenv_path=".env.qdrant")

QDRANT_API_KEY= os.getenv("QDRANT_API_KEY")
URL= os.getenv("URL")
ORIGINAL_COLLECTION= os.getenv("ORIGINAL_COLLECTION")
SYNTHETIC_DOCS_COLLECTION= os.getenv("SYNTHETIC_DOCS_COLLECTION")

async def upload_points_to_qdrant(state: StateDictionary)->Coroutine[Any, Any, StateDictionary]:

    if state["error"] is not None:
        return state

    async with aiohttp.ClientSession() as session:
        client = QdrantClientAsync(
            data_model=QdrantValidator,
            data_conformer=DocxValidator,
            collection_name=SYNTHETIC_DOCS_COLLECTION,
            base_url=URL,
            session=session,
            headers={
                "Content-Type": "application/json",
                "api-key": QDRANT_API_KEY
            },
            dense_size= 3072

        )
        try:
            await client.create_collection()

            await client.upload_documents(items=state["worker2_generated_qa"])
            state["status"] = "success"
            return state
        except Exception as e:
            print(e)
            return state



