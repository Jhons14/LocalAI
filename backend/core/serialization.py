"""
Message serialization utilities for LangChain messages.
"""
from langchain_core.messages import BaseMessage


def serialize_message(message) -> dict:
    """
    Serialize any type of LangChain message with enhanced status and metadata handling.

    Args:
        message: A LangChain message object or dict

    Returns:
        Serialized message as a dictionary
    """
    if hasattr(message, 'type') or isinstance(message, BaseMessage):
        serialized = {
            "type": getattr(message, 'type', 'unknown'),
            "content": getattr(message, 'content', ''),
            "additional_kwargs": getattr(message, 'additional_kwargs', {}),
            "response_metadata": getattr(message, 'response_metadata', {}),
            "id": getattr(message, 'id', None),
            "tool_calls": getattr(message, 'tool_calls', []),
            "usage_metadata": getattr(message, 'usage_metadata', {}),
            "tool_call_id": getattr(message, 'tool_call_id', None),
            "name": getattr(message, 'name', None),
        }

        # Capture artifact field for tool messages
        if hasattr(message, 'artifact'):
            serialized["artifact"] = getattr(message, 'artifact', None)

        # Extract status information from various possible locations
        if serialized["type"] == "tool":
            # Priority order for status determination:
            # 1. Explicit non-default status attribute on message
            # 2. Status in additional_kwargs
            # 3. Success flag in additional_kwargs
            # 4. Status in response_metadata
            # 5. Error in response_metadata
            # 6. Content pattern analysis
            # 7. Default to success

            status_found = False

            # Enhanced status handling for ToolMessages - check explicit status first
            # BUT only if it's not the default 'success' value, because tools might
            # have meaningful error information in other fields that overrides the default
            if hasattr(message, 'status'):
                explicit_status = getattr(message, 'status', 'success')
                if explicit_status != 'success':
                    # Only trust non-default status values
                    serialized["status"] = explicit_status
                    status_found = True
                # If status is 'success' (default), continue checking other fields for error indicators

            # Check for status in additional_kwargs
            if not status_found:
                additional_kwargs = serialized.get("additional_kwargs", {})
                if "status" in additional_kwargs:
                    serialized["status"] = additional_kwargs["status"]
                    status_found = True
                elif "success" in additional_kwargs:
                    serialized["status"] = "success" if additional_kwargs["success"] else "error"
                    status_found = True

            # Check response_metadata for status indicators
            if not status_found:
                response_metadata = serialized.get("response_metadata", {})
                if "status" in response_metadata:
                    serialized["status"] = response_metadata["status"]
                    status_found = True
                elif "error" in response_metadata:
                    serialized["status"] = "error"
                    serialized["error_details"] = response_metadata["error"]
                    status_found = True

            # Analyze content for error patterns if no explicit status found
            if not status_found and serialized["content"]:
                content_str = str(serialized["content"]).lower()
                if any(error_pattern in content_str for error_pattern in
                       ["error:", "failed", "exception", "could not", "unable to"]):
                    serialized["status"] = "error"
                    status_found = True

            # Default to success if no status indicators found
            if not status_found:
                serialized["status"] = "success"

        return serialized
    return message
