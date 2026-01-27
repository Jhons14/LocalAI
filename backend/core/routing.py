"""
Routing logic for LangGraph workflow conditional edges.
"""
import logging
from typing import Optional

from langchain_arcade import ArcadeToolManager
from langgraph.graph import END, MessagesState

logger = logging.getLogger(__name__)


def create_routing_function(
    tool_manager: Optional[ArcadeToolManager],
    max_tool_calls: int = 5
):
    """
    Create a routing function with anti-infinite loop protection.

    Args:
        tool_manager: Optional ArcadeToolManager for authorization checking
        max_tool_calls: Maximum number of tool calls allowed in recent messages

    Returns:
        A routing function for LangGraph conditional edges
    """

    def should_continue(state: MessagesState):
        last_message = state["messages"][-1]

        # Extract tool calls
        tool_calls = (
            last_message.get("tool_calls", [])
            if isinstance(last_message, dict)
            else getattr(last_message, 'tool_calls', [])
        )

        # Count recent tool calls for loop protection
        recent_tool_calls = 0
        for msg in state["messages"][-10:]:
            if isinstance(msg, dict):
                recent_tool_calls += len(msg.get("tool_calls", []))
            else:
                recent_tool_calls += len(getattr(msg, 'tool_calls', []))

        # Prevent infinite loops
        if recent_tool_calls > max_tool_calls:
            logger.warning("Max tool calls reached, forcing end")
            return END

        if not tool_calls:
            return END

        # Check for authorization requirements
        if tool_manager:
            for tool_call in tool_calls:
                if tool_manager.requires_auth(tool_call["name"]):
                    return "authorization"

        return "tools"

    return should_continue
