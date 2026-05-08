from langgraph.graph import StateGraph, END
from lib.state import AgentState
from lib.agents import orchestrator_agent

graph = StateGraph(AgentState)

graph.add_node("orchestrator_agent", orchestrator_agent)
graph.set_entry_point("orchestrator_agent")
graph.add_edge("orchestrator_agent", END)

app = graph.compile()