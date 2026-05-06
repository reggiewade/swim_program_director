from langgraph.graph import StateGraph, END
from lib.state import AgentState
from lib.agents import macro_agent, meso_agent, micro_agent

graph = StateGraph(AgentState)

graph.add_node("macro_agent", macro_agent)
graph.add_node("meso_agent", meso_agent)
graph.add_node("micro_agent", micro_agent)

graph.set_entry_point("macro_agent")
graph.add_edge("macro_agent", "meso_agent")
graph.add_edge("meso_agent", "micro_agent")
graph.add_edge("micro_agent", END)

app = graph.compile()