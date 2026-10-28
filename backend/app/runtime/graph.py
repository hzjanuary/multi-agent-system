"""The sole orchestration path: a registered sequential LangGraph."""

from collections.abc import Awaitable, Callable
from typing import Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from app.definitions import NodeDefinition, WorkflowDefinition


class GraphState(TypedDict):
    halted: bool


def build_workflow_graph(
    definition: WorkflowDefinition,
    execute: Callable[[NodeDefinition], Awaitable[bool]],
    finalize: Callable[[], Awaitable[None]],
) -> Any:
    graph = StateGraph(GraphState)
    names = [node.id for node in definition.nodes]
    for index, node in enumerate(definition.nodes):

        def bind(
            current: NodeDefinition,
        ) -> Callable[[GraphState], Awaitable[GraphState]]:
            async def handler(state: GraphState) -> GraphState:
                return {"halted": not await execute(current)}

            return handler

        graph.add_node(node.id, cast(Any, bind(node)))
        target = names[index + 1] if index + 1 < len(names) else "__finalize"

        def route(state: GraphState, next_name: str = target) -> str:
            return END if state["halted"] else next_name

        graph.add_conditional_edges(node.id, route, [target, END])

    async def finish(state: GraphState) -> GraphState:
        await finalize()
        return state

    graph.add_node("__finalize", finish)
    graph.add_edge(START, names[0])
    graph.add_edge("__finalize", END)
    return graph.compile()
