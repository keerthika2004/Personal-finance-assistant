from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from backend.app.services.llm_factory import LLMFactory

def build_chat_agent(tools, system_prompt: str):
    """Tool-calling ReAct-style loop in LangGraph: agent -> (tools -> agent)* -> END.
    The LLM emit tool calls; ToolNode runs them; the loop repeats until it answers."""
    llm = LLMFactory.get_llm(temperature=0.1).bind_tools(tools)

    tool_names = ", ".join(t.name for t in tools)
    sys_msg = SystemMessage(content=system_prompt + f"\n\nYou may ONLY call these tools: {tool_names}\n\nNever call any tool not in that list. As soon as a tool gives you the answer, reply to user in plain text - do NOT keep calling tools.")

    def agent_node(state: MessagesState):
        return {"messages": [llm.invoke([sys_msg] + state["messages"])]}
    
    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition) # -> "tools" if tool calls, else END
    graph.add_edge("tools", "agent")
    return graph.compile()  