from typing import TypedDict, List, Dict, Callable, NamedTuple, Union, Coroutine, Tuple, Optional, Any

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

class StateDictionary(TypedDict):
    """
    This class represents the status of the information at any give pass in the graph flow.

    arguments:
    :arg status (str): the string that informs the name of the node in which the status is being StateDictionary is processed.
    :arg original_document: The list of docs that have been chunked and processed for the first llm worker
    :arg worker1_generated_qa: The first generation made by the llm.
    :arg evaluator_response: The json format specific response of the evaluation of the first sytnhethic qa and its score-
    arg worker2_generated_qa: The second generation made by the llm.
    :arg error: A json format error that informs if anything has failed in the status flow of the graph.
    """
    status: str
    original_document: List[Document] | str
    worker1_generated_qa: Optional[Dict[str, str] | Coroutine[Any, Any, Dict[str, str]]] | None
    evaluator_response: Optional[Dict[str, str] | Coroutine[Any, Any, Dict[str, str]]] | None
    worker2_generated_qa: Optional[Dict[str, str] | Coroutine[Any, Any, Dict[str, str]]] | None
    error: Optional[Dict[str, str]]





class NodeFunctionsTuple(NamedTuple):
    """
    This class represents a tuple that includes the function to be executed on the StateGraph as node,
    and the specific name.

    :arg function(Union [Callable, Coroutine]): The function type for the node.
    :arg node_name (str): The name of the node.
    """
    function: Union[Callable, Coroutine]
    node_name: str

def stategraph_factory_constructor(state_dict: StateDictionary,
                                   node_functions: Tuple[NodeFunctionsTuple]) -> StateGraph:
    """
    This function creates a StateGraph from a status dictionary and a node function tuple. It uses a Factory pattern
    to construct the StateGraph from a status dictionary and a node function tuple.
    :param state_dict: The status dictionary that represents the flow of information at any time give within the StateGraph.
    :param node_functions: A tuple of NodeFunctions representing the node functions.
    :return: the StateGraph with all the nodes added
    """
    graph_constructor = StateGraph(state_dict)
    prev_node_name = None
    for index, fn in enumerate(node_functions):

        function = fn.function
        node_name = fn.node_name
        graph_constructor.add_node(node_name, function)

        if index == 0:
            graph_constructor.add_edge(START, node_name)
        else:
            graph_constructor.add_edge(prev_node_name, node_name)
        prev_node_name = node_name

    graph_constructor.add_edge(prev_node_name, END)




    return graph_constructor