"""
graph_workflow_schemas.py

This module defines the data structures and schemas for a graph-based workflow system
that processes documents to generate synthetic question-answer pairs using language models.
The workflow includes generation, evaluation, and refinement steps with retry logic.

The module supports a multi-stage workflow:
1. Document processing and initial QA generation
2. Evaluation of generated content quality
3. Refinement based on evaluation feedback
4. Retry mechanisms with configurable limits

Key Components:
    - Response models for LLM interactions (generation, evaluation, refinement)
    - State management for workflow progression
    - Node configuration for graph construction
    - Conditional logic for workflow branching

Classes:
    LlmGenerationResponse: Structured response from QA generation step
    LlmEvaluatorResponse: Evaluation results with reasoning and decision
    LlmRefinerResponse: Refined QA pairs with improvement reasoning
    EvalDecision: Enumeration for workflow decision points
    StateDictionary: Complete workflow state container
    NodeFunctionsTuple: Node configuration for graph construction

Usage:
    This module is typically used to configure LangGraph workflows for
    automated question-answer generation from documents with quality control.
"""

from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Literal, NamedTuple, Optional, TypedDict, Union

from langchain_core.documents import Document
from pydantic import BaseModel, Field

class LlmGenerationResponse(BaseModel):
    response:List[Dict[str, Any]] =Field(..., description="A Generation response with Question as key and answer as value")

class LlmEvaluatorResponse(BaseModel):
    reasoning: Dict[str, Any] = Field(..., description="The reasoning related to the Evaluation category chosen")
    evaluation: Literal["retry", "correct"] = Field(..., description="The evaluation category chosen")

class LlmRefinerResponse(BaseModel):
    response:List[Dict[str, Any]] =Field(..., description="A Generation response with Question as key and answer as value")
    reasoning: Dict[str, Any] = Field(..., description="The reasoning related to the  changes done in the synthetic QA")

class EvalDecision(Enum):
    """
    EvalDecision enumeration. This small class represents the conditional mapping used for creating conditional edges.
    """
    RETRY = "retry"
    CORRECT = "correct"
    MAX_RETRY = "max_retry"


class StateDictionary(TypedDict):
    """
    This class represents the status of the information at any give pass in the graph flow.

    arguments:
    :arg status (str): the string that informs the name of the node in which the status is being StateDictionary is processed.
    :arg original_document: The list of docs that have been chunked and processed for the first llm worker.
    :arg generated_qa: The first generation made by the llm.
    :arg examples_path: The path to the annotated human examples
    :arg examples_qa: The examples of real question answers done by students.
    :arg evaluator_response: The json format specific response of the evaluation of the first synthetic qa and its score.
    :arg refined_qa: The second generation made by the llm.
    :arg max_retry: The number of times the reflexion and reasoning steps can be executed.
    :arg error: A json format error that informs if anything has failed in the status flow of the graph.
    """
    status: str | None
    original_document_path: str | None
    original_document: List[Document] | str | None
    generated_qa: Optional[Dict[str, str] | Coroutine[Any, Any, Dict[str, str]]] | None
    examples_path: str | None
    examples_qa: Optional[List[Dict[str, Any]] |Dict[str, Any] | None]
    evaluator_response: Optional[Dict[str, str] | Coroutine[Any, Any, Dict[str, str]]] | None
    refined_qa: Optional[Dict[str, str] | Coroutine[Any, Any, Dict[str, str]]] | None
    max_retry: Optional[int] | None
    error: Optional[Dict[str, str]]


class NodeFunctionsTuple(NamedTuple):
    """
    This class represents a tuple that includes the function to be executed on the StateGraph as node,
    and the specific name.

    :arg function(Union [Callable, Coroutine]): The function type for the node.
    :arg node_name (str): The name of the node.
    :arg edge_type: The edge type of the node.
    :arg conditional_mapping: Optional argument related to conditional edges and decision-making.
    """
    function: Union[Callable, Coroutine]
    node_name: str
    edge_type: Literal["directed", "conditional"]
    conditional_mapping: Optional[Dict[EvalDecision, str]] = None
    loop_back_to: Optional[str] = None
