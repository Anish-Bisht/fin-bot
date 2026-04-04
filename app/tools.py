from typing import Annotated
from langchain.tools import tool
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import InjectedToolArg
from app.db import search_documents




@tool
def search_internal_documents(
    query: str, 
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Search secure internal company documents based on the user's role and RBAC permissions.
    Use this tool to answer any question about company policies, HR, finance, engineering, or marketing.
    Returns relevant document chunks with source citations."""
    # Extract user role from config if available (injected by LangChain at runtime)
    user_role = "employee"
    if config and hasattr(config, "get"):
        user_role = config.get("configurable", {}).get("user_role", "employee")
    chunks, error_msg = search_documents(query, user_role)

    if error_msg and not chunks:
        return f"No relevant internal documents found.\n{error_msg}"

    if not chunks:
        return "No relevant documents found in the internal knowledge base for your query."

    # Format chunks as readable text for the LLM with source citations
    formatted_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "Unknown Document")
        page = chunk.get("page", 1)
        text = chunk.get("text", "")
        formatted_parts.append(
            f"[Chunk {i}]\n"
            f"Source: {source} (page {page})\n"
            f"{text}\n"
            f"---"
        )

    return "\n".join(formatted_parts)




tools = [
 
    search_internal_documents,
]