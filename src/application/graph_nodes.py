"""
Graph Nodes for Q&A Processing Workflow

This module contains the core nodes for a graph-based workflow that processes Word documents
to generate, evaluate, and refine question-answer pairs using Large Language Models (LLMs).
The workflow includes document parsing, Q&A generation, evaluation with retry logic, refinement,
and final upload to a Qdrant vector database.

The workflow follows this pattern:
1. Parse Word document -> Extract text content
2. Generate Q&A pairs -> Use LLM to create questions and answers
3. Evaluate Q&A quality -> Use LLM evaluator to assess quality
4. Refine if needed -> Improve Q&A pairs based on evaluation feedback
5. Upload to Qdrant -> Store final Q&A pairs in vector database

Key Dependencies:
- LangChain: Document processing and LLM interactions
- Azure OpenAI: Language model provider
- Qdrant: Vector database for storing Q&A pairs
- Pydantic: Data validation and serialization

Error Handling:
All nodes implement comprehensive error handling with state preservation,
allowing the workflow to gracefully handle failures and maintain execution context.
"""

import asyncio
from itertools import tee
import os
from typing import Any, Coroutine, Dict, List, Tuple, Iterator
from uuid import uuid4

import aiohttp # type: ignore
from dotenv import  dotenv_values # type: ignore
from langchain_community.document_loaders import UnstructuredWordDocumentLoader # type: ignore
from langchain_core.documents import Document # type: ignore
from langchain_core.output_parsers import JsonOutputParser # type: ignore
from langchain_core.prompts import ChatPromptTemplate # type: ignore
from langchain_openai import AzureChatOpenAI # type: ignore
from pydantic import BaseModel # type: ignore


from src.client import QdrantClientAsync
from src.models import (
    EvalDecision,
    LlmEvaluatorResponse,
    StateDictionary,
    QdrantBotAnswerConformer,
    LlmGenerationResponse
)
from src.utils import lazy_load_json_qa_sample, load_markdown, setup_custom_logging, encode_document
from .client_setup import EVALUATOR_ENGINE, GENERATOR_ENGINE, REFINER_ENGINE





graph_logger = setup_custom_logging(logger_name="langgraph.log", log_file_path="logs")


async def parse_wordformat_document(state: StateDictionary)->StateDictionary:
    """
    Parse a Word document (.docx) and extract its text content.

    This function loads a Word document from the file path specified in the state,
    extracts all text content using LangChain's UnstructuredWordDocumentLoader,
    and stores the concatenated text in the state dictionary.

    Args:
        state (StateDictionary): The workflow state containing:
            - original_document_path (str): Path to the .docx file to parse
            - error (dict | None): Any existing error state

    Returns:
        StateDictionary: Updated state containing:
            - original_document (str): Extracted text content from the document
            - status (str): Success message or error details
            - error (dict | None): Error information if parsing failed

    Side Effects:
        - Logs success/error messages
        - Modifies the input state dictionary in-place

    Error Handling:
        - Returns early if state already contains an error
        - Logs detailed error information for debugging
    """

    if state["error"] is not None:
        graph_logger.error(f"Error encountered in the node within the function {parse_wordformat_document.__name__}\n\n Details: {state["error"]}")
        return state
    loader_instance =  UnstructuredWordDocumentLoader(state["original_document_path"])

    docs: Iterator[Document] = loader_instance.lazy_load()

    state["status"]  = "Parsing docx file step completed"
    state["original_document"] = "\n".join(d.page_content for d in docs )
    graph_logger.info("Parsing docx file step completed for parsing documents step. ")
    return state


async def llm_call(
        state: StateDictionary,
        llm_engine: AzureChatOpenAI,
        system_prompt: Tuple[str, ...],
        user_prompt: Tuple[str, ...],
        invoke_args: Dict[str, Any],
        json_parser: BaseModel = LlmGenerationResponse,
) -> Dict[str, str] | Coroutine[Any, Any, Dict[str, str]] | None:
    """
    Execute a standardized LLM call using prompt chaining in LangChain.

    This is a utility function that implements the common workflow pattern
    for LLM interactions across different nodes in the graph. It constructs
    a prompt chain, invokes the LLM with structured output parsing, and
    returns the parsed response.

    Args:
        state (StateDictionary): Current workflow state for error checking
        llm_engine (AzureChatOpenAI): The Azure OpenAI LLM instance to use
        system_prompt (Tuple[str, ...]): System-level instructions for the LLM
        user_prompt (Tuple[str, ...]): User-level instructions and context
        invoke_args (Dict[str, Any]): Arguments to pass to the LLM chain
        json_parser (BaseModel, optional): Pydantic model for structured output.
            Defaults to LlmGenerationResponse.

    Returns:
        Coroutine[None, None, Dict[str, Any] | None]: Async coroutine that yields
            the parsed LLM response as a dictionary, or None if an error occurred.

    Raises:
        Exception: Propagates any exceptions from the LLM chain invocation

    Design Notes:
        - Reduces code duplication across different LLM-calling nodes
        - Enforces consistent prompt structure and output parsing
        - Provides centralized error handling for LLM interactions
        - Uses LangChain's chain composition (prompt | llm | parser)
    """
    if state["error"] is not None:
        graph_logger.error(f"Error encountered in the node within the internal function {llm_call.__name__}\n\n Details: {state["error"]}")
        return state  # type: ignore

    llm = llm_engine
    parser = JsonOutputParser(pydantic_object=json_parser)
    prompt = ChatPromptTemplate.from_messages([
        system_prompt,
        user_prompt,
    ])
    chain = prompt | llm | parser

    result = await chain.ainvoke(invoke_args)
    return result

async def qa_generator_node(state:StateDictionary)->StateDictionary | None:
    """
    Generate question-answer pairs from document content using an LLM.

    This node takes the parsed document content and uses a generator LLM
    to create relevant question-answer pairs. It loads system and user prompts
    from markdown files and formats them with the document content.

    Args:
        state (StateDictionary): Workflow state containing:
            - original_document (str): The text content to generate Q&A from
            - error (dict | None): Any existing error state

    Returns:
        StateDictionary | None: Updated state containing:
            - generated_qa (Dict[str, Any]): The generated Q&A pairs
            - status (str): Success/error status message
            - error (dict | None): Error details if generation failed

    Prompt Files Required:
        - src/prompts/system_prompt_generator_node.md
        - src/prompts/user_prompt_generator_node.md

    Error Handling:
        - Returns early if state contains existing errors
        - Catches and logs LLM invocation exceptions
        - Sets error status and details in state on failure

    Side Effects:
        - Logs progress and completion messages
        - Modifies state dictionary in-place
    """

    if state["error"] is not None:
        graph_logger.error(
            f"Error encountered in the node within the function {qa_refiner_node.__name__}\n\n Details: {state["error"]}")
        return state


    system_prompt =tuple("".join(
        load_markdown(
            directory_path="prompts",
            markdown_file_name="system_prompt_generator_node"
        )
    ).split("\n"))

    user_prompt = tuple( "".join(
        load_markdown(
            directory_path="prompts",
            markdown_file_name="user_prompt_generator_node"
        )
    ).split("\n"))

    parser = JsonOutputParser(pydantic_object=LlmGenerationResponse)
    generator_params ={
        "docs": state["original_document"],
        "format_instructions": parser.get_format_instructions()
    }
    try:
        result:Dict[str, str] | Coroutine[Any, Any, Dict[str, str]] | None = await llm_call(
            state=state,
            llm_engine=GENERATOR_ENGINE,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            invoke_args=generator_params

        )

    except Exception as e:
        state["status"] = "Error in the Generator_qa step"
        state["error"] = {
            "status": "error",
            "message": str(e),
        }
        graph_logger.error(e)
        return state


    state["status"] = "Generator_qa step completed"
    state["generated_qa"] = result
    graph_logger.info("Generator qa step completed")
    return state


async def evaluator_node(state: StateDictionary)->StateDictionary| None:
    """
    Evaluate the quality of generated question-answer pairs using an LLM evaluator.

    This node takes generated Q&A pairs and evaluates their quality against
    example Q&A pairs. The evaluator determines whether the generated content
    meets quality standards or needs refinement. It loads example Q&A pairs
    for comparison and uses specialized evaluation prompts.

    Args:
        state (StateDictionary): Workflow state containing:
            - generated_qa (Dict[str, Any]): Q&A pairs to evaluate
            - examples_qa (List | None): Example Q&A pairs for comparison
            - examples_path (str): Path to example Q&A JSON file
            - error (dict | None): Any existing error state

    Returns:
        Coroutine[None,None, Dict[str, Any]| None]: Async coroutine that yields
            updated state containing:
            - evaluator_response (Dict[str, Any]): Evaluation results and decision
            - examples_qa (List): Loaded example Q&A pairs
            - status (str): Success/error status message
            - error (dict | None): Error details if evaluation failed

    Prompt Files Required:
        - src/prompts/system_prompt_evaluator_node.md
        - src/prompts/user_prompt_evaluator_node.md

    Default Behavior:
        - Uses fallback example path if examples_qa is None
        - Loads examples from benchmark/benchmark_files/original_export/qdrant_data_export.json

    Error Handling:
        - Returns early if state contains existing errors
        - Catches and logs LLM evaluation exceptions
        - Preserves retry count information for workflow control
    """

    if state["error"] is not None:
        graph_logger.error(
            f"Error encountered in the node within the function {evaluator_node.__name__}\n\n Details: {state["error"]}")
        return state

    if state["examples_path"] is None:
        json_path = "benchmark/benchmark_files/original_export/qdrant_data_export.json"
        unnecessary = {"id", "category"}
        raw_examples = lazy_load_json_qa_sample(json_path)
        conformed_examples = [{k: v for k, v in raw_example.items() if k not in unnecessary} for raw_example in raw_examples]
        state["examples_qa"] = conformed_examples

    unnecessary = {"id", "category"}
    raw_examples = lazy_load_json_qa_sample(state["examples_path"])  # type: ignore
    conformed_examples = [{k:v for k, v in raw_example.items() if k not in unnecessary} for raw_example in raw_examples]
    state["examples_qa"] = conformed_examples

    system_prompt =tuple("".join(
        load_markdown(
            directory_path="prompts",
            markdown_file_name="system_prompt_evaluator_node"
        )
    ).split("\n"))

    user_prompt = tuple( "".join(
        load_markdown(
            directory_path="prompts",
            markdown_file_name="user_prompt_evaluator_node"
        )
    ).split("\n"))


    parser = JsonOutputParser(pydantic_object=LlmEvaluatorResponse)
    if state["max_retry"] == 0:
        evaluator_params ={
            "generated_qa": state["generated_qa"],
            "examples": state["examples_qa"],
            "format_instructions": parser.get_format_instructions()
        }
    else:
        evaluator_params ={
            "generated_qa": state["refined_qa"],
            "examples": state["examples_qa"],
            "format_instructions": parser.get_format_instructions()
        }
    try:
        result: Dict[str, Any] = await llm_call(
            state=state,
            llm_engine=EVALUATOR_ENGINE,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            invoke_args=evaluator_params,
            json_parser= LlmEvaluatorResponse,
        )
    except Exception as e:
        state["status"] = "Error in the evaluator_qa step"
        state["error"] = {
            "status": "error",
            "message": str(e),
        }
        graph_logger.error(e)
        return state


    state["status"] = "Evaluator_qa step completed"
    state["evaluator_response"] = result
    graph_logger.info(f"Evaluator qa step completed. Pass number {state["max_retry"]}")
    return state

async def evaluator_router(state:StateDictionary)-> EvalDecision | StateDictionary:
    """
    Route workflow execution based on evaluator decision and retry logic.

    This is a router function used for conditional edges in the workflow graph.
    It examines the evaluator's decision and the current retry count to determine
    the next step in the workflow: retry generation, proceed with refinement,
    or exit due to maximum retries reached.

    Args:
        state (StateDictionary): Workflow state containing:
            - evaluator_response (Dict): Contains 'evaluation' key with decision
            - max_retry (int): Current number of retry attempts
            - error (dict | None): Any existing error state

    Returns:
        EvalDecision | StateDictionary: One of the following:
            - EvalDecision.RETRY: If evaluation is "retry" and retries < 3
            - EvalDecision.MAX_RETRY: If evaluation is "retry" but max retries reached
            - EvalDecision.CORRECT: If evaluation indicates acceptable quality
            - StateDictionary: Returns state unchanged if error exists

    Routing Logic:
        - MAX_RETRY (3): Stop retrying, proceed with current Q&A pairs
        - RETRY: Continue refinement loop, increment retry counter
        - CORRECT: Q&A pairs meet quality standards, proceed to upload

    Design Notes:
        - Implements circuit breaker pattern to prevent infinite loops
        - Provides clear decision points for graph workflow navigation
        - Maintains error state propagation through routing decisions
    """
    if state["error"] is not None:
        return state
    evaluation = state["evaluator_response"]["evaluation"]
    if evaluation == "retry":

        if state["max_retry"] == 3:
            return EvalDecision.MAX_RETRY
        else:

            return EvalDecision.RETRY

    else:
        return EvalDecision.CORRECT

async def qa_refiner_node(state:StateDictionary)-> Coroutine[None,None, Dict[str, Any]| None]:
    """
    Refine and improve question-answer pairs based on evaluation feedback.

    This node takes generated Q&A pairs that didn't meet quality standards
    and uses an LLM to refine them. It incorporates feedback from the evaluator
    and example Q&A pairs to produce improved versions. The refined Q&A pairs
    will be re-evaluated in the next iteration.

    Args:
        state (StateDictionary): Workflow state containing:
            - generated_qa (Dict[str, Any]): Original Q&A pairs to refine
            - examples_qa (List): Example Q&A pairs for guidance
            - max_retry (int): Current retry count
            - error (dict | None): Any existing error state

    Returns:
        Coroutine[None,None, Dict[str, Any]| None]: Async coroutine that yields
            updated state containing:
            - refined_qa (Dict[str, Any]): Improved Q&A pairs
            - max_retry (int): Incremented retry counter
            - status (str): Success/error status with iteration number
            - error (dict | None): Error details if refinement failed

    Prompt Files Required:
        - src/prompts/system_prompt_refiner_node.md
        - src/prompts/user_prompt_refiner_node.md

    Retry Management:
        - Increments max_retry counter for workflow control
        - Provides iteration-specific status messages
        - Works with evaluator_router to manage retry limits

    Error Handling:
        - Returns early if state contains existing errors
        - Catches and logs LLM refinement exceptions
        - Maintains retry count even on failures
    """

    if state["error"] is not None:
        graph_logger.error(f"Error encountered in the node within the function {qa_refiner_node.__name__}\n\n Details: {state["error"]}")
        return state


    system_prompt =tuple("".join(
        load_markdown(
            directory_path="prompts",
            markdown_file_name="system_prompt_refiner_node"
        )
    ).split("\n"))

    user_prompt = tuple( "".join(
        load_markdown(
            directory_path="prompts",
            markdown_file_name="user_prompt_refiner_node"
        )
    ).split("\n"))
    parser = JsonOutputParser(pydantic_object=LlmGenerationResponse)
    if state["max_retry"] == 0:
        refiner_args ={
            "generated_qa": state["generated_qa"],
            "format examples": state["examples_qa"],
            "evaluator instructions" : state["evaluator_response"],
            "format_instructions": parser.get_format_instructions()
        }
    else:
        refiner_args = {
            "generated_qa": state["refined_qa"],
            "format examples": state["examples_qa"],
            "evaluator instructions" : state["evaluator_response"],
            "format_instructions": parser.get_format_instructions()
        }
    try:
        result: Coroutine[None,None, Dict[str, Any]| None] = await llm_call(
            state=state,
            llm_engine=REFINER_ENGINE,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            invoke_args=refiner_args,
            json_parser= LlmGenerationResponse,
        )
    except Exception as e:
        state["status"] = "Error in the refiner_qa step"
        state["error"] = {
            "status": "error",
            "message": str(e),
        }
        graph_logger.error(e)
        return state


    state["max_retry"] += 1
    state["status"] = f"Refiner_qa step completed in the iteration number {state["max_retry"]}"
    state["refined_qa"] = result
    graph_logger.info(f"Refiner_qa step completed in the iteration number {state["max_retry"]}")
    return state






async def upload_points_to_qdrant(state: StateDictionary)->Coroutine[None,None, Dict[str, Any]| None]:
    """
    Upload refined question-answer pairs to Qdrant vector database.

    This is the final node in the workflow that takes the processed and refined
    Q&A pairs and uploads them to a Qdrant collection for storage and retrieval.
    It creates the collection if it doesn't exist and uploads documents in batches
    for efficiency.

    Args:
        state (StateDictionary): Workflow state containing:
            - refined_qa (Dict[str, Any]): Final Q&A pairs to upload
            - error (dict | None): Any existing error state

    Returns:
        Coroutine[None,None, Dict[str, Any]| None]: Async coroutine that yields
            updated state containing:
            - status (str): Success/error status message
            - error (dict | None): Error details if upload failed

    Environment Variables Required:
        - QDRANT_API_KEY: Authentication key for Qdrant service
        - URL: Qdrant service endpoint URL
        - SYNTHETIC_DOCS_COLLECTION: Target collection name for Q&A pairs

    Qdrant Configuration:
        - Collection: SYNTHETIC_DOCS_COLLECTION from environment
        - Vector size: 3072 dimensions (for embedding compatibility)
        - Batch size: 50 documents per upload batch
        - Data model: QdrantValidator for validation

    Connection Management:
        - Uses aiohttp.ClientSession for async HTTP operations
        - Includes proper headers with API key authentication
        - Automatically handles collection creation if needed

    Error Handling:
        - Returns early if state contains existing errors
        - Catches upload exceptions and sets error state
        - Provides detailed error graph_logger for debugging

    Side Effects:
        - Creates Qdrant collection if it doesn't exist
        - Uploads documents to remote vector database
        - Logs success/failure messages
    """


    if state["error"] is not None:
        graph_logger.error(f"Error encountered in the node within the function {upload_points_to_qdrant.__name__}\n\n Details: {state["error"]}")
        return state
    DOTENV_PATH = "src/application/.env.qdrant"
    env_vars = dotenv_values(DOTENV_PATH)

    # Ensure all required environment variables are injected into os.environ
    required_keys = {
        "QDRANT_API_KEY",
        "URL",
        "SYNTHETIC_DOCS_COLLECTION"

    }

    for key in required_keys:
        value = env_vars.get(key)
        if not value:
            raise ValueError(f"Missing required environment variable: {key}")
        os.environ[key] = value

    if isinstance(state["refined_qa"], str):
        graph_logger.warning(f"{state['refined_qa']} is a runtime string, converting to dictionary format")
        import json
        state["refined_qa"] = json.loads(state["refined_qa"])

    text_generator = (d["text"] for d in state["refined_qa"]["response"])
    answer_generator = (d["answer"] for d in state["refined_qa"]["response"])

    original_generator = ({
        "text": text,
        "answer" : answer,
        "category": "general",
        "metadata" : {
            "source" : state["original_document_path"]
        }
    } for text, answer in zip(text_generator, answer_generator))

    prepared_collection_generator_for_encoding, prepared_collection_generator_for_uploading = tee(original_generator)
    docs_to_encode = [doc["text"] for doc in prepared_collection_generator_for_encoding]
    encoded_docs = await asyncio.gather(*(encode_document(doc= doc) for doc in docs_to_encode))
    graph_logger.info("All documents encoded")
    formated_collection = []
    for vector, upload_dict in zip(encoded_docs, prepared_collection_generator_for_uploading):
        upload_dict["vector"] = vector
        formated_collection.append(upload_dict)
    conformed_collection = []
    for dic in formated_collection:
        conformed_collection.append({

            "id": str(uuid4()),
            "vector" : dic["vector"],
            "payload": {
                "text": dic["text"],
                "answer" : dic["answer"],
                "category" : dic["category"],
                "additional_metadata" : dic["metadata"]
                }
            })

    async with aiohttp.ClientSession() as session:
        client = QdrantClientAsync(data_model=QdrantBotAnswerConformer, collection_name=env_vars["SYNTHETIC_DOCS_COLLECTION"], base_url=env_vars["URL"],
                                   session=session, headers={
                "Content-Type": "application/json",
                "api-key": env_vars["QDRANT_API_KEY"]
            }, dense_size=3072)
        try:
            await client.create_collection()

            await client.upload_documents(items=conformed_collection, batch_size=50)
            state["status"] = "successfully uploaded documents"

        except Exception as e:
            state["status"] = "error uploading documents to Qdrant collection"
            state["error"] = {
                "status": "error",
                "message": str(e),
            }
            graph_logger.error(e)
            return state
        state["status"] = "successfully uploaded documents"
        graph_logger.info("Successfully uploaded documents")
        # A PARTIR DE AQUÍ HAY QUE HACER LA LÓGICA DE GUARDADO
        return state