"""
Tool-related utilities for managing LangChain Arcade tools.
"""
import logging
from typing import List, Optional

from langchain_arcade import ArcadeToolManager

from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def create_tool_change_system_message(
    changes: dict,
    tool_manager: Optional[ArcadeToolManager] = None
) -> str:
    """
    Create a system message explaining tool configuration changes.

    Args:
        changes: Dictionary containing tool changes (added_tools, removed_tools, new_toolkits)
        tool_manager: Optional ArcadeToolManager for authorization checking

    Returns:
        Formatted system message string
    """
    added_tools = changes.get("added_tools", [])
    removed_tools = changes.get("removed_tools", [])
    new_toolkits = changes.get("new_toolkits", [])

    if not added_tools and not removed_tools:
        return ""

    message_parts = ["[SYSTEM] Your tool configuration has been updated:"]

    if added_tools:
        message_parts.append(f"Added tools: {', '.join(added_tools)}")
        # Add capabilities for new tools
        for tool in added_tools:
            capability = settings.tool_capabilities.get(tool, "General purpose tool")
            message_parts.append(f"   {tool}: {capability}")

    if removed_tools:
        message_parts.append(f"Removed tools: {', '.join(removed_tools)}")

    if new_toolkits:
        message_parts.append(f"Current available tools: {', '.join(new_toolkits)}")

        # Add authorization status for new tools
        if tool_manager and new_toolkits:
            auth_required = []
            for toolkit in new_toolkits:
                try:
                    if hasattr(tool_manager, 'requires_auth') and tool_manager.requires_auth(toolkit):
                        auth_required.append(toolkit)
                except Exception as e:
                    logger.debug(f"Could not check auth requirements for {toolkit}: {e}")

            if auth_required:
                message_parts.append(f"Tools requiring authorization: {', '.join(auth_required)}")

        # Check for tool conflicts
        conflicts = detect_tool_conflicts(new_toolkits)
        if conflicts:
            message_parts.append("Potential tool conflicts detected:")
            for conflict in conflicts:
                message_parts.append(f"   {conflict}")
    else:
        message_parts.append("No tools are currently available")

    message_parts.append("You can now use your updated tool configuration to assist with requests.")
    return "\n".join(message_parts)


def detect_tool_conflicts(toolkits: List[str]) -> List[str]:
    """
    Detect potential conflicts between tools.

    Args:
        toolkits: List of toolkit names to check for conflicts

    Returns:
        List of conflict description strings
    """
    conflicts = []

    for tool in toolkits:
        tool_config = settings.tool_conflicts.get(tool, {})
        conflicts_with = tool_config.get("conflicts_with", [])

        for other_tool in toolkits:
            if other_tool != tool and other_tool in conflicts_with:
                note = tool_config.get("note", "")
                conflict_msg = f"{tool} may conflict with {other_tool}"
                if note:
                    conflict_msg += f" ({note})"
                conflicts.append(conflict_msg)

    return list(set(conflicts))  # Remove duplicates
