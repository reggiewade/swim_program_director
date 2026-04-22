from langgraph.graph import StateGraph, END
from backend.lib.state import AgentState

def orchestrator(state: AgentState):
    if not state.get("macro_plan"):
        return {**state, "next_agent": "macro_agent"}
    if not state.get("meso_plane"):
        return {**state, "next_agent": "meso_agent"}
    if not state.get("micro_plan"):
        return {**state, "next_agent": "micro_agent"}
    return {**state, "next_agent": "done"}

def route(state: AgentState):
    return state["next_agent"]

graph = StateGraph(AgentState)

graph.add_node("orchestrator", orchestrator)
