"""
graph_orchestrator.py
This module serves as the main orchestrator for executing the Q&A processing workflow graph.
It provides the entry point function that initializes the workflow state, compiles the graph,
and manages the execution of the entire document processing pipeline.

The orchestrator is responsible for:
- Setting up the initial workflow state with input parameters
- Compiling the LangGraph StateGraph with optional debugging
- Executing the complete workflow asynchronously
- Returning the final processed state

This module acts as a bridge between external callers and the internal graph workflow,
providing a clean interface for running the document-to-Q&A processing pipeline.

Key Dependencies:
- LangGraph: For state graph compilation and execution
- graph_constructor: For StateDictionary type definition

Usage Pattern:
    result = await stategraph_run(
        input_docs_path="path/to/document.docx",
        uncompiled_graph=my_graph,
        example_docs_path="path/to/examples.json",
        debug=False
    )

"""

from typing import Any, Coroutine

from langgraph.graph import StateGraph

from src.models import StateDictionary


async def stategraph_run(
        initial_state: StateDictionary,
        uncompiled_graph: StateGraph,
        debug:bool = False
)-> Coroutine[Any, Any, StateDictionary]:
    """
        Execute the complete Q&A processing workflow graph with the provided inputs.

    This is the main orchestration function that initializes the workflow state,
    compiles the provided StateGraph, and executes the entire document processing
    pipeline. It handles the complete flow from document parsing through Q&A
    generation, evaluation, refinement, and final upload to the vector database.

    Args:

        initial_state (StateDictionary): Initial state of the workflow.
        uncompiled_graph (StateGraph): The LangGraph StateGraph instance containing
            all the workflow nodes and edges, ready for compilation and execution.
            that will be used by the evaluator for quality comparison and guidance.
        debug (bool, optional): Enable debug mode for graph compilation, which
            provides additional logging and introspection capabilities. Defaults to False.

    Returns:
        Coroutine[Any, Any, StateDictionary]: An async coroutine that yields the
            final StateDictionary containing:
            - status (str): Final workflow status message
            - original_document (str): Parsed document text content
            - original_document_path (str): Input document path (unchanged)
            - generated_qa (Dict): Initially generated Q&A pairs
            - examples_qa (List): Loaded example Q&A pairs for reference
            - examples_path (str): Example document path (unchanged)
            - evaluator_response (Dict): Final evaluation results
            - refined_qa (Dict): Final refined Q&A pairs (if refinement occurred)
            - max_retry (int): Total number of retry iterations performed
            - error (Dict | None): Any error information if the workflow failed

    """



    compiled_graph = uncompiled_graph.compile(debug=debug)

    result = await compiled_graph.ainvoke(input= initial_state)

    return result


