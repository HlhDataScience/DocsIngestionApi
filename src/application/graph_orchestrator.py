
from typing import Any, Coroutine, Callable

from .graph_constructor import StateDictionary, NodeFunctionsTuple, stategraph_factory_constructor

async def stategraph_run(input_docs_path: str, factory_fn: Callable, debug:bool = False)-> Coroutine[Any, Any, StateDictionary]:

    factory_workflow = factory_fn()

    compiled_graph = factory_workflow.compile(debug=debug)

    result = compiled_graph.ainvoke(input_docs_path)

    if result["error"] is not None:
        return result
    return result


