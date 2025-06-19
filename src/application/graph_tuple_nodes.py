"""
graph_tuple_nodes.py

This module defines the declarative configuration for the Q&A processing workflow graph.
It maps individual node functions to their graph properties, including edge types,
conditional routing logic, and loop-back behaviors. This configuration serves as the
blueprint for constructing the LangGraph StateGraph that orchestrates the entire
document processing pipeline.

The configuration follows a declarative approach where each node is defined with:
- The function to execute
- A unique node name for graph identification
- Edge type (directed or conditional)
- Conditional routing mappings for decision points
- Loop-back targets for iterative refinement

Workflow Structure:
    document_parser → qa_generator → evaluator → [conditional routing]
                                        ↑              ↓
                                    qa_refiner ← [retry logic]
                                        ↓
                                  qdrant_uploader → END

Key Design Patterns:
- Linear progression for main workflow steps
- Conditional branching based on evaluation results
- Loop-back mechanism for iterative refinement
- Circuit breaker pattern to prevent infinite loops
- Terminal node for workflow completion

Graph Properties:
- Directed edges: Simple one-to-one node connections
- Conditional edges: Multi-path routing based on evaluation logic
- Loop-back edges: Enable iterative improvement cycles
- Termination: Automatic connection to END node when no loop-back specified

Dependencies:
- graph_workflow_schemas: For EvalDecision enum and NodeFunctionsTuple structure
- graph_nodes: For all the node function implementations

Usage:
This configuration is consumed by graph construction utilities that build
the actual LangGraph StateGraph for execution by the orchestrator.
"""

from src.models import EvalDecision, NodeFunctionsTuple
from .graph_nodes import (
    parse_wordformat_document,
    qa_generator_node,
    evaluator_node,
    qa_refiner_node,
    conform_points_to_qdrant,
    upload_points_to_qdrant
)

NODES_FUNCS = (

    NodeFunctionsTuple(
        function=parse_wordformat_document,
        node_name="document_parser",
        edge_type="directed",
    ),
    NodeFunctionsTuple(
        function=qa_generator_node,
        node_name="qa_generator",
        edge_type="directed",
    ),
    NodeFunctionsTuple(
        function=evaluator_node,
        node_name="evaluator",
        edge_type="conditional",  # Changed to conditional since evaluator_router decides the path
        conditional_mapping={
            EvalDecision.RETRY: "qa_refiner",
            EvalDecision.CORRECT: "conform_points_to_qdrant",
            EvalDecision.MAX_RETRY: "conform_points_to_qdrant",
        }
    ),
    NodeFunctionsTuple(
        function=qa_refiner_node,
        node_name="qa_refiner",
        edge_type="directed",
        loop_back_to="evaluator"  # This creates the loop back to evaluator
    ),
    NodeFunctionsTuple(
        function=conform_points_to_qdrant,
        node_name="conform_points_to_qdrant",
        edge_type="directed",
    ),
    NodeFunctionsTuple(
        function=upload_points_to_qdrant,
        node_name="qdrant_uploader",
        edge_type="directed",
        # No loop_back_to, so this will connect to END
    )
)
