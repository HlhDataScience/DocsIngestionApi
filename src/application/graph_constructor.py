"""
graph_constructor.py

This module contains the factory pattern function to create self reflecting graph patterns. It uses the NamedTuple
NodeFunctionsTuple to estructure the different steps of the flow.
"""


from typing import Callable, Optional, Tuple

from langgraph.graph import END, StateGraph, START  # type: ignore

from src.models import EvalDecision, NodeFunctionsTuple, StateDictionary
from src.utils import setup_custom_logging

logger = setup_custom_logging(logger_name= "langgraph.log",log_file_path="logs")
def self_reflecting_stategraph_factory_constructor(state_dict: type[StateDictionary],
                                   node_functions: Tuple[NodeFunctionsTuple, ...],
                                   router_function: Optional[Callable[
                                       [StateDictionary], EvalDecision | StateDictionary]] = None) -> StateGraph:
    """
    This function creates a StateGraph from a state dictionary and a node function tuple.
    :param router_function: The router function to be used for the state graph when need to decide a conditional step.
    :param state_dict: The status dictionary that represents the flow of information at any time give within the StateGraph.
    :param node_functions: A tuple of NodeFunctions representing the node functions.
    :return: the StateGraph with all the nodes added
    """
    graph_constructor = StateGraph(state_dict)

    # First pass: Add all nodes
    for fn in node_functions:
        logger.info(f"Adding node {fn.node_name}")
        graph_constructor.add_node(fn.node_name, fn.function)


    # Collect all nodes that are targets of conditional mappings
    conditional_targets: set = set()
    for fn in node_functions:
        if fn.conditional_mapping:
            conditional_targets.update(fn.conditional_mapping.values())

    # Collect all nodes that have loop_back_to
    loop_back_sources = set()
    for fn in node_functions:
        if fn.loop_back_to:
            loop_back_sources.add(fn.node_name)

    # Second pass: Add edges
    for index, fn in enumerate(node_functions):
        node_name = fn.node_name

        # Add START edge to first node
        if index == 0:
            graph_constructor.add_edge(START, node_name)
            logger.info("Adding first edge for START node")
        # Handle directed edges
        if fn.edge_type == "directed":
            # Add edge from previous node only if:
            # 1. Previous node exists
            # 2. Previous node is not conditional
            # 3. Current node is not a conditional target (unless it's a loop back)
            if index > 0:
                prev_fn = node_functions[index - 1]
                prev_node_name = prev_fn.node_name

                # Add edge if previous is not conditional and current node is not a conditional target
                # OR if current node is a conditional target but also has loop_back_to (special case)
                should_add_edge = (
                        prev_fn.edge_type != "conditional" and
                        (node_name not in conditional_targets or fn.loop_back_to is not None)
                )

                if should_add_edge:
                    graph_constructor.add_edge(prev_node_name, node_name)
                    logger.info(f"Adding edge between {prev_node_name} and {node_name}")
            # Handle loop_back_to edges
            if fn.loop_back_to:
                graph_constructor.add_edge(node_name, fn.loop_back_to)
                logger.info(f"Adding  recursive edge between {node_name} and {fn.loop_back_to}")

        # Handle conditional edges
        elif fn.edge_type == "conditional":
            if not router_function:
                logger.error("router_function must be provided for conditional edges.")
                raise ValueError("router_function must be provided for conditional edges.")

            if not fn.conditional_mapping:
                logger.error("fn.conditional_mapping must be provided for conditional edges.")
                raise ValueError("conditional_mapping must be provided for conditional edges.")

            # Add edge from previous node to this conditional node
            if index > 0:
                prev_fn = node_functions[index - 1]
                graph_constructor.add_edge(prev_fn.node_name, node_name)
                logger.info(f"Adding conditional edge between {prev_fn.node_name} and {node_name}")
            # Add conditional edges from this node
            graph_constructor.add_conditional_edges(
                source=node_name,
                path=router_function,
                path_map=fn.conditional_mapping
            )

    # Find the final node (not a conditional target and doesn't loop back)
    final_node = None
    for fn in reversed(node_functions):  # Start from the end
        if (fn.node_name not in conditional_targets and
                fn.node_name not in loop_back_sources and
                fn.edge_type == "directed"):
            final_node = fn.node_name
            break

    # Add edge to END from the final node
    if final_node:
        graph_constructor.add_edge(final_node, END)
        logger.info(f"Adding final node {final_node}")
    logger.info("Graph constructed ready to compile")
    return graph_constructor
