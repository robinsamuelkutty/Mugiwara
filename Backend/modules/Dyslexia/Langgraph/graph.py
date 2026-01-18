from langgraph.graph import StateGraph, END
from modules.Dyslexia.Langgraph.graph_state import DyslexiaGraphState
from modules.Dyslexia.Langgraph.graph_nodes import (
    node_compare_and_score,
    node_decide_route,
    node_error_reasoner,
    node_advance_level,
    node_final_verifier,
)


def route_after_decision(state: DyslexiaGraphState) -> str:
    status = state.get("status", "")

    if status == "PASS":
        return "ADVANCE"
    if status == "NEED_REASONING":
        return "REASON"
    if status == "RETEST":
        return "END"        # stop here -> frontend will ask user and call again
    if status == "COMPLETED":
        return "VERIFY"

    return "END"


def build_dyslexia_langgraph():
    graph = StateGraph(DyslexiaGraphState)

    # nodes
    graph.add_node("compare_score", node_compare_and_score)
    graph.add_node("decide", node_decide_route)
    graph.add_node("reason", node_error_reasoner)
    graph.add_node("advance", node_advance_level)
    graph.add_node("verify", node_final_verifier)

    # entry
    graph.set_entry_point("compare_score")

    # edges
    graph.add_edge("compare_score", "decide")

    graph.add_conditional_edges(
        "decide",
        route_after_decision,
        {
            "ADVANCE": "advance",
            "REASON": "reason",
            "VERIFY": "verify",
            "END": END,
        },
    )

    # after advance -> compare again (next level)
    graph.add_edge("advance", "compare_score")

    # after reason -> either RETEST end or verify
    graph.add_conditional_edges(
        "reason",
        lambda s: "END" if s.get("status") == "RETEST" else "VERIFY",
        {
            "END": END,
            "VERIFY": "verify",
        },
    )

    graph.add_edge("verify", END)

    return graph.compile()