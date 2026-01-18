from langgraph.graph import StateGraph, END
from modules.Dyslexia.Langgraph.graph_state import DyslexiaGraphState
from modules.Dyslexia.Langgraph.graph_nodes import (
    node_compare_and_score,
    node_decide_route,
    node_advance_level,
    node_final_verifier,
)

def route_condition(state: DyslexiaGraphState) -> str:
    status = state.get("status", "")
    if status == "PASS":
        return "ADVANCE"
    if status == "RETEST":
        return "END"  # stop and ask frontend to retest
    if status == "COMPLETED":
        # if completed after level4 or fail -> verify
        return "VERIFY"
    return "END"

def build_dyslexia_graph():
    graph = StateGraph(DyslexiaGraphState)

    graph.add_node("compare_score", node_compare_and_score)
    graph.add_node("router", node_decide_route)
    graph.add_node("advance", node_advance_level)
    graph.add_node("verify", node_final_verifier)

    graph.set_entry_point("compare_score")

    graph.add_edge("compare_score", "router")

    graph.add_conditional_edges(
        "router",
        route_condition,
        {
            "ADVANCE": "advance",
            "VERIFY": "verify",
            "END": END
        }
    )

    graph.add_edge("advance", "compare_score")
    graph.add_edge("verify", END)

    return graph.compile()