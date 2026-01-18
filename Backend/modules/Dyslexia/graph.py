# backend/modules/Dyslexia/graph.py

from __future__ import annotations
from typing import Any, Dict
from langgraph.graph import StateGraph, END

from .schemas import DyslexiaState
from .nodes import (
    generate_expected_text_node,
    transcribe_node,
    score_node,
    router_node,
)


def build_dyslexia_graph():
    g = StateGraph(DyslexiaState)

    g.add_node("generate_expected_text", generate_expected_text_node)
    g.add_node("transcribe", transcribe_node)
    g.add_node("score", score_node)
    g.add_node("route", router_node)

    # flow
    g.set_entry_point("generate_expected_text")
    g.add_edge("generate_expected_text", "transcribe")
    g.add_edge("transcribe", "score")
    g.add_edge("score", "route")

    # routing decisions
    def route_decision(state: DyslexiaState) -> str:
        if state.status in ["PASS", "FAIL"]:
            return "end"
        return "continue"

    g.add_conditional_edges(
        "route",
        route_decision,
        {
            "continue": "generate_expected_text",
            "end": END,
        }
    )

    return g.compile()


GRAPH = build_dyslexia_graph()


def run_dyslexia_graph(audio_path: str, level: int = 1, user_id: str | None = None) -> DyslexiaState:
    init_state = DyslexiaState(user_id=user_id, current_level=level)
    final_state = GRAPH.invoke(
        {"user_id": user_id, "current_level": level},
        config={"configurable": {"audio_path": audio_path}}
    )
    return DyslexiaState(**final_state)