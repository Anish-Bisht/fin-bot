import os
import sqlite3
import json
import time
from typing import Annotated, Sequence, TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent
from app.config import settings
from app.tools import tools
from app.router_layer import get_route, check_rbac_for_route
from app.guards import validate_input, validate_output

# --- LLM Setup ---
os.environ["GROQ_API_KEY"] = settings.groq_api_key
llm = ChatGroq(
    model=settings.groq_model,
    temperature=0,
    max_tokens=4096,
    timeout=60,
)

# --- Agent Definition ---
SYSTEM_PROMPT = """You are FinBot, an internal QA assistant for FinSolve Technologies.
Your job is to answer employee queries using ONLY the retrieved documents from the internal knowledge base.

## Rules
1. ALWAYS use the `search_internal_documents` tool to find information before answering.
2. NEVER hallucinate information. If the tool returns no data, state that you do not have the information in your accessible documents.
3. Keep the response concise and clearly structured.
4. DO NOT provide financial advice.
5. If analyzing financial figures, double check data against the retrieved text.
6. When citing sources, include the document name and page number."""

# --- Memory Setup ---
checkpoint_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".data", "checkpoints.db")
os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
conn = sqlite3.connect(checkpoint_path, check_same_thread=False)
memory = SqliteSaver(conn)

# --- Agent Initialization ---
# Using LangGraph's create_react_agent for better tool-calling support
agent_app = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
    prompt=SYSTEM_PROMPT
)

def run_agent(query: str, thread_id: str, user_role: str = "employee") -> dict:
    # 1. Input Guardrails
    ok, input_warning, clean_query = validate_input(query, thread_id)
    if not ok:
        return {
            "result": input_warning,
            "route": "Blocked by Guardrail",
            "warnings": input_warning,
            "sources": [],
            "execution_time": 0.0,
            "agent_thoughts": "Guardrail blocked execution."
        }

    # 2. Semantic Routing
    route = get_route(clean_query)
    has_access, rbac_msg = check_rbac_for_route(route, user_role)
    if not has_access:
        return {
            "result": f"🚫 Access Denied: {rbac_msg}",
            "route": route,
            "warnings": "RBAC violation attempted.",
            "sources": [],
            "execution_time": 0.0,
            "agent_thoughts": "Access denied by RBAC."
        }

    # 3. Process with LangGraph
    start_time = time.time()
    agent_thoughts = []
    sources = []
    content_str = ""
    
    config = {"configurable": {"thread_id": thread_id, "user_role": user_role}}
    
    try:
        # LangGraph returns the full state history
        result = agent_app.invoke(
            {"messages": [HumanMessage(content=clean_query)]},
            config=config
        )
        
        # Last message is the final assistant response
        messages = result.get("messages", [])
        if not messages:
             raise ValueError("No messages returned from agent")
             
        last_message = messages[-1]
        content_str = str(last_message.content)
        
        # Extract thoughts AND sources from message history
        for msg in messages:
            # Capture tool calls as "thoughts"
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_query = tc.get("args", {}).get("query", "current topic")
                    agent_thoughts.append(f"🔍 Searching internal documents for: '{tool_query}'")
            
            # Capture tool outputs to extract citations
            if isinstance(msg, ToolMessage):
                # The content of ToolMessage is the string returned by our search function
                if isinstance(msg.content, str):
                    for line in msg.content.split("\n"):
                        if line.startswith("Source:"):
                            src = line.replace("Source:", "").strip()
                            if src and src not in sources:
                                sources.append(src)
                                
    except Exception as e:
        content_str = f"I encountered an error processing your request: {str(e)}"

    execution_time = round(time.time() - start_time, 2)
    sources = list(set(sources))

    # 4. Output Guardrails
    ok, output_warning = validate_output(content_str, sources)
    warnings = []
    if input_warning:
        warnings.append(input_warning)
    if output_warning:
        warnings.append(output_warning)

    return {
        "result": content_str,
        "route": route,
        "warnings": " | ".join(warnings) if warnings else "",
        "sources": sources,
        "execution_time": execution_time,
        "agent_thoughts": "\n".join(agent_thoughts)
    }
