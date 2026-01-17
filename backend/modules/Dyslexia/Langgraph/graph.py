from langgraph.graph import StateGraph, END
from typing import Dict, Any
from modules.Dyslexia.Langgraph.graph_nodes import (
    node_compare_and_score,
    node_decide_route,
    node_error_reasoner,
    node_advance_level,
    node_final_verifier,

    # NEW dysgraphia nodes
    node_dysgraphia_preprocess,
    node_dysgraphia_segmentation,
    node_dysgraphia_features,
    node_dysgraphia_ocr,
    node_dysgraphia_accuracy,
    node_dysgraphia_clip,
    node_dysgraphia_scoring,
)


print("✅ USING graph.py (build_dyslexia_langgraph)")

def route_after_decision(state: Dict[str, Any]) -> str:
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

def after_dyslexia_verifier(state: Dict[str, Any]) -> str:
    result = state.get("final_result")
    if result in ["NORMAL", "INCONCLUSIVE"]:
        return "DYSGRAPHIA"
    return "END"


def build_dyslexia_langgraph():
    graph = StateGraph(dict)

    # nodes
    graph.add_node("compare_score", node_compare_and_score)
    graph.add_node("decide", node_decide_route)
    graph.add_node("reason", node_error_reasoner)
    graph.add_node("advance", node_advance_level)
    graph.add_node("verify", node_final_verifier)
    graph.add_node("dysgraphia_preprocess", node_dysgraphia_preprocess)
    graph.add_node("dysgraphia_segmentation", node_dysgraphia_segmentation)
    graph.add_node("dysgraphia_features", node_dysgraphia_features)
    graph.add_node("dysgraphia_ocr", node_dysgraphia_ocr)
    graph.add_node("dysgraphia_accuracy", node_dysgraphia_accuracy)
    graph.add_node("dysgraphia_clip", node_dysgraphia_clip)
    graph.add_node("dysgraphia_scoring", node_dysgraphia_scoring)

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
    graph.add_conditional_edges(
        "verify",
        after_dyslexia_verifier,
        {
            "DYSGRAPHIA": "dysgraphia_preprocess",
            "END": END
        }
    )

    # after advance -> compare again (next level

    # after reason -> either RETEST end or verify
    graph.add_conditional_edges(
        "reason",
        lambda s: "END" if s.get("status") == "RETEST" else "VERIFY",
        {
            "END": END,
            "VERIFY": "verify",
        },
    )
    graph.add_edge("advance", "compare_score")
    graph.add_edge("dysgraphia_preprocess", "dysgraphia_segmentation")
    graph.add_edge("dysgraphia_segmentation", "dysgraphia_features")
    graph.add_edge("dysgraphia_features", "dysgraphia_ocr")
    graph.add_edge("dysgraphia_ocr", "dysgraphia_accuracy")
    graph.add_edge("dysgraphia_accuracy", "dysgraphia_clip")
    graph.add_edge("dysgraphia_clip", "dysgraphia_scoring")
    graph.add_edge("dysgraphia_scoring", END)
    return graph.compile()
