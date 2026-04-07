import os
import sqlite3
import time
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
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

# --- Role-aware System Prompt ---
# Roles with full financial analysis access
FINANCE_ROLES = {"finance", "c_level"}

_BASE_PROMPT = """You are FinBot, an internal QA assistant for FinSolve Technologies.
Your job is to answer employee queries using ONLY the retrieved documents from the internal knowledge base.

## Rules
1. ALWAYS use the `search_internal_documents` tool to find information before answering.
2. NEVER hallucinate information. If the tool returns no data, state that you do not have the information in your accessible documents.
3. Keep the response concise and clearly structured.
{financial_rules}
6. When citing sources, include the document name and page number."""

# Rules 4 & 5 for general employees — restrict financial advice
_GENERAL_FINANCIAL_RULES = """\
4. DO NOT provide financial advice or recommendations.
5. If financial figures appear in retrieved documents, report them exactly as stated without interpretation."""

# Rules 4 & 5 for Finance / C-Level — full financial analysis enabled
_FINANCE_FINANCIAL_RULES = """\
4. You ARE authorized to analyze and interpret financial data for this user's role.
   Provide clear, accurate financial summaries, trends, and insights based strictly on retrieved documents.
5. Double-check all financial figures against the retrieved text before presenting them.
   Highlight any discrepancies or data gaps you notice."""


def get_system_prompt(user_role: str) -> str:
    """Return a role-appropriate system prompt."""
    if user_role.lower() in FINANCE_ROLES:
        financial_rules = _FINANCE_FINANCIAL_RULES
    else:
        financial_rules = _GENERAL_FINANCIAL_RULES
    return _BASE_PROMPT.format(financial_rules=financial_rules)


# --- Memory Setup ---
checkpoint_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".data", "checkpoints.db"
)
os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
conn = sqlite3.connect(checkpoint_path, check_same_thread=False)
memory = SqliteSaver(conn)

# --- Agent Initialization (no static prompt — injected per-call) ---
agent_app = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
)


def run_agent(query: str, thread_id: str, user_role: str = "employee", username: str = "anonymous") -> dict:
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

    # Inject role-specific system prompt per invocation
    system_prompt = get_system_prompt(user_role)
    # Include username in thread_id to isolate conversations per user
    isolated_thread_id = f"{username}_{thread_id}"
    config = {"configurable": {"thread_id": isolated_thread_id, "user_role": user_role}}

    try:
        result = agent_app.invoke(
            {
                "messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=clean_query),
                ]
            },
            config=config,
        )
    except Exception as e:
        # If we get a "tool_calls without ToolMessage" error, it's corrupted checkpoint state
        # Clear this thread's checkpoint and retry with fresh state
        error_msg = str(e)
        if "tool_calls that do not have a corresponding ToolMessage" in error_msg or "INVALID_CHAT_HISTORY" in error_msg:
            # Attempt to clear the checkpoint for this thread
            try:
                checkpoint_data = memory.get_tuple(config)
                if checkpoint_data:
                    memory.delete_tuple(config)
                print(f"🔄 Cleared corrupted checkpoint for thread '{isolated_thread_id}'")
                # Retry the agent invocation with fresh state
                result = agent_app.invoke(
                    {
                        "messages": [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=clean_query),
                        ]
                    },
                    config=config,
                )
            except Exception as retry_error:
                content_str = f"I encountered an error processing your request: {str(retry_error)}"
                execution_time = round(time.time() - start_time, 2)
                return {
                    "result": content_str,
                    "route": route,
                    "warnings": "Processing error",
                    "sources": sources,
                    "execution_time": execution_time,
                    "agent_thoughts": "Recovery attempt failed."
                }
        else:
            raise

        messages = result.get("messages", [])
        if not messages:
            raise ValueError("No messages returned from agent")

        last_message = messages[-1]
        content_str = str(last_message.content)

        # Extract thoughts AND sources from message history
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_query = tc.get("args", {}).get("query", "current topic")
                    agent_thoughts.append(f"🔍 Searching internal documents for: '{tool_query}'")

            if isinstance(msg, ToolMessage) and isinstance(msg.content, str):
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
