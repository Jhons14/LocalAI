"""
Workflow management and building utilities for LangGraph workflows.
"""
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from langchain_arcade import ArcadeToolManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.base import BaseStore

from config.settings import get_settings
from core.models import ModelProvider, ModelFactory
from core.serialization import serialize_message
from core.routing import create_routing_function
from prompts import prompt_loader

settings = get_settings()
logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages workflow instances and configurations."""

    def __init__(self):
        self.workflows: Dict[str, StateGraph] = {}
        self.configurations: Dict[str, Dict] = {}
        self.tool_managers: Dict[str, ArcadeToolManager] = {}
        self.usage_stats: Dict[str, Dict] = {}  # Simple usage tracking

    def get_workflow(self, thread_id: str) -> Optional[StateGraph]:
        """Get workflow for a thread."""
        return self.workflows.get(thread_id)

    def set_workflow(self, thread_id: str, workflow: StateGraph, config: Dict):
        """Store workflow and configuration for a thread."""
        self.workflows[thread_id] = workflow
        self.configurations[thread_id] = config

    def get_config(self, thread_id: str) -> Optional[Dict]:
        """Get configuration for a thread."""
        return self.configurations.get(thread_id)

    def get_tool_manager(self, thread_id: str) -> Optional[ArcadeToolManager]:
        """Get tool manager for a thread."""
        return self.tool_managers.get(thread_id)

    def set_tool_manager(self, thread_id: str, manager: ArcadeToolManager):
        """Store tool manager for a thread."""
        self.tool_managers[thread_id] = manager

    def exists(self, thread_id: str) -> bool:
        """Check if a thread exists."""
        return thread_id in self.workflows

    def delete(self, thread_id: str):
        """Delete a thread and all associated resources."""
        self.workflows.pop(thread_id, None)
        self.configurations.pop(thread_id, None)
        self.tool_managers.pop(thread_id, None)
        self.usage_stats.pop(thread_id, None)

    def track_usage(
        self,
        thread_id: str,
        tool_name: Optional[str] = None,
        execution_time: Optional[float] = None
    ):
        """Track simple usage statistics and performance."""
        if thread_id not in self.usage_stats:
            self.usage_stats[thread_id] = {
                "chat_count": 0,
                "tool_usage": {},
                "tool_performance": {},  # Track execution times
                "last_used": datetime.now().isoformat()
            }

        self.usage_stats[thread_id]["chat_count"] += 1
        self.usage_stats[thread_id]["last_used"] = datetime.now().isoformat()

        if tool_name:
            # Usage count
            if tool_name not in self.usage_stats[thread_id]["tool_usage"]:
                self.usage_stats[thread_id]["tool_usage"][tool_name] = 0
            self.usage_stats[thread_id]["tool_usage"][tool_name] += 1

            # Performance tracking
            if execution_time is not None:
                if tool_name not in self.usage_stats[thread_id]["tool_performance"]:
                    self.usage_stats[thread_id]["tool_performance"][tool_name] = {
                        "total_time": 0.0,
                        "call_count": 0,
                        "avg_time": 0.0
                    }

                perf = self.usage_stats[thread_id]["tool_performance"][tool_name]
                perf["total_time"] += execution_time
                perf["call_count"] += 1
                perf["avg_time"] = perf["total_time"] / perf["call_count"]

    def get_usage_stats(self, thread_id: str) -> Dict:
        """Get usage statistics for a thread."""
        return self.usage_stats.get(thread_id, {})

    def get_current_toolkits(self, thread_id: str) -> List[str]:
        """Get current toolkits from workflow configuration."""
        config = self.configurations.get(thread_id, {})
        return config.get("toolkits", [])

    def reconfigure_workflow_tools(
        self,
        thread_id: str,
        new_toolkits: List[str],
        api_key: Optional[str] = None
    ):
        """Reconfigure existing workflow with new tools while preserving model configuration."""
        if not self.exists(thread_id):
            raise ValueError(f"Thread {thread_id} does not exist")

        # Get existing configuration and current toolkits
        current_config = self.configurations[thread_id].copy()
        old_toolkits = current_config.get("toolkits", [])

        # Determine changes for system message
        added_tools = set(new_toolkits or []) - set(old_toolkits)
        removed_tools = set(old_toolkits) - set(new_toolkits or [])

        # Update toolkits in configuration
        current_config["toolkits"] = new_toolkits or []

        # Get current model configuration from existing config
        provider = current_config.get("provider", ModelProvider.OLLAMA)
        model = current_config.get("model", "llama3.2")

        # Create model instance with existing configuration
        model_instance = ModelFactory.create_model(
            provider=provider,
            model_name=model,
            api_key=api_key,
            temperature=settings.default_temperature,
            max_tokens=settings.default_max_tokens
        )

        # Initialize tool manager if toolkits specified
        tool_manager = None
        tools = []
        if new_toolkits:
            tool_manager = ArcadeToolManager(api_key=settings.arcade_api_key)
            tool_manager.init_tools(toolkits=new_toolkits)
            tools = tool_manager.to_langchain(use_interrupts=True)
            self.set_tool_manager(thread_id, tool_manager)

            # Bind tools to model
            model_instance = model_instance.bind_tools(tools)
        else:
            # Remove tool manager if no toolkits
            self.tool_managers.pop(thread_id, None)

        # Build new workflow
        workflow = StateGraph(state_schema=MessagesState)

        # Add agent node
        agent_node = WorkflowBuilder.create_agent_node(model_instance, tool_manager)
        workflow.add_node("agent", agent_node)

        # Add tool nodes if tools are configured
        if tools:
            tool_node = WorkflowBuilder.create_tool_node(tools)
            workflow.add_node("tools", tool_node)

            if tool_manager:
                auth_node = WorkflowBuilder.create_authorization_node(tool_manager)
                workflow.add_node("authorization", auth_node)

            # Add routing
            routing_func = create_routing_function(
                tool_manager,
                settings.max_tool_calls_per_turn
            )
            workflow.add_conditional_edges("agent", routing_func, ["authorization", "tools", END])
            workflow.add_edge("authorization", "tools")
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)

        workflow.add_edge(START, "agent")

        # Update stored workflow and configuration
        self.workflows[thread_id] = workflow
        self.configurations[thread_id] = current_config

        # Return workflow and change information
        return {
            "workflow": workflow,
            "changes": {
                "added_tools": list(added_tools),
                "removed_tools": list(removed_tools),
                "old_toolkits": old_toolkits,
                "new_toolkits": new_toolkits or []
            }
        }


class WorkflowBuilder:
    """Builder for creating workflow graph components."""

    @staticmethod
    def create_agent_node(model, tool_manager: Optional[ArcadeToolManager] = None):
        """Create an agent node with streaming support."""

        async def call_agent(state: MessagesState, writer, config: RunnableConfig, *, store: BaseStore):
            messages = state["messages"]
            user_id = config.get("configurable", {}).get("user_id", "").replace(".", "")
            namespace = ("memories", user_id)

            # Retrieve relevant memories
            memories_str = ""
            last_user_message = None
            for msg in reversed(messages):
                if isinstance(msg, (HumanMessage, dict)) and (
                    isinstance(msg, HumanMessage) or msg.get('type') == 'human'
                ):
                    last_user_message = msg
                    break

            if last_user_message and store:
                content = (
                    last_user_message.content
                    if hasattr(last_user_message, 'content')
                    else last_user_message.get('content', '')
                )
                try:
                    memories = await store.asearch(namespace, query=str(content))
                    if memories:
                        memories_str = "\n".join([f"- {d.value['data']}" for d in memories])
                except Exception as e:
                    logger.warning(f"Error retrieving memories: {e}")

            # Build system message
            system_content = WorkflowBuilder._build_system_message(memories_str, tool_manager)
            logger.info(f"System message length: {len(system_content)}")
            logger.debug(f"System message content: {system_content[:500]}...")
            messages_with_system = WorkflowBuilder._ensure_system_message(messages, system_content)

            # Check for memory storage request
            if last_user_message and store:
                content_str = str(
                    last_user_message.content
                    if hasattr(last_user_message, 'content')
                    else last_user_message.get('content', '')
                )
                if "remember" in content_str.lower():
                    try:
                        await store.aput(namespace, str(uuid.uuid4()), {"data": content_str})
                    except Exception as e:
                        logger.warning(f"Error storing memory: {e}")

            # Stream response
            full_content = ""
            tool_calls = []

            try:
                async for chunk in model.astream(messages_with_system):
                    if chunk.content:
                        writer(chunk.content)
                        full_content += chunk.content

                    if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                        valid_calls = [
                            tc for tc in chunk.tool_calls
                            if tc.get("name", "").strip()
                        ]
                        tool_calls.extend(valid_calls)

                response = AIMessage(content=full_content, tool_calls=tool_calls)
                return {"messages": [serialize_message(response)]}

            except Exception as e:
                logger.error(f"Error in agent node: {e}")
                error_msg = AIMessage(content=f"I encountered an error: {str(e)}")
                return {"messages": [serialize_message(error_msg)]}

        return call_agent

    @staticmethod
    def _extract_tool_schemas(tool_manager: ArcadeToolManager) -> str:
        """Extract tool schemas and parameter requirements from tool manager."""
        try:
            # Get the tools from the manager
            tools = tool_manager.to_langchain(use_interrupts=True)
            logger.info(f"Found {len(tools)} tools from tool manager")

            if not tools:
                logger.warning("No tools found from tool manager")
                return ""

            tool_schemas = []
            for i, tool in enumerate(tools):
                tool_name = getattr(tool, 'name', 'Unknown')
                tool_description = getattr(tool, 'description', 'No description available')
                logger.info(f"Processing tool {i+1}/{len(tools)}: {tool_name}")

                # Try to get tool arguments schema
                args_schema = getattr(tool, 'args_schema', None)
                if args_schema:
                    try:
                        # Extract field information from pydantic schema
                        schema_info = args_schema.model_json_schema()
                        properties = schema_info.get('properties', {})
                        required = schema_info.get('required', [])
                        logger.info(f"Tool {tool_name} has {len(properties)} parameters, {len(required)} required")

                        tool_info = f"\n{tool_name}:"
                        tool_info += f"\n- Description: {tool_description}"

                        if properties:
                            tool_info += "\n- Parameters:"
                            for field_name, field_info in properties.items():
                                param_type = field_info.get('type', 'unknown')
                                param_desc = field_info.get('description', 'No description')
                                is_required = field_name in required
                                status = "(REQUIRED)" if is_required else "(optional)"
                                tool_info += f"\n  * {field_name} {status}: {param_desc} (type: {param_type})"

                        tool_schemas.append(tool_info)
                    except Exception as e:
                        logger.warning(f"Failed to extract schema for {tool_name}: {e}")
                        # Fallback for tools without proper schema
                        tool_schemas.append(
                            f"\n{tool_name}:\n- Description: {tool_description}\n- Parameters: Could not extract schema"
                        )
                else:
                    logger.warning(f"Tool {tool_name} has no args_schema")
                    tool_schemas.append(
                        f"\n{tool_name}:\n- Description: {tool_description}\n- Parameters: No schema available"
                    )

            result = "\n".join(tool_schemas) if tool_schemas else ""
            logger.info(f"Generated schema string length: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Could not extract tool schemas: {e}", exc_info=True)
            return ""

    @staticmethod
    def _build_system_message(memories_str: str, tool_manager: Optional[ArcadeToolManager]) -> str:
        """Build system message with memories and detailed tool instructions."""
        return prompt_loader.build_system_message(
            memories_str=memories_str,
            tool_manager=tool_manager,
            extract_schemas_func=WorkflowBuilder._extract_tool_schemas
        )

    @staticmethod
    def _ensure_system_message(messages: list, system_content: str) -> list:
        """Ensure system message is present at the beginning."""
        messages_copy = messages[:]

        if not messages or not (
            isinstance(messages[0], SystemMessage) or
            (isinstance(messages[0], dict) and messages[0].get('type') == 'system')
        ):
            system_dict = {"type": "system", "content": system_content}
            messages_copy = [system_dict] + messages_copy

        return messages_copy

    @staticmethod
    def create_tool_node(tools: list) -> ToolNode:
        """Create a tool node with proper error handling."""
        tool_node = ToolNode(tools)

        async def wrapped_tool_node(state: MessagesState):
            # Track tool execution time
            start_time = time.time()
            tool_names = []

            # Extract tool names from the last message
            try:
                last_message = state["messages"][-1]
                tool_calls = (
                    last_message.get("tool_calls", [])
                    if isinstance(last_message, dict)
                    else getattr(last_message, 'tool_calls', [])
                )
                tool_names = [tc.get("name", "unknown") for tc in tool_calls]
            except:
                pass

            try:
                # Log tool execution details
                logger.info(f"Executing tools: {', '.join(tool_names) if tool_names else 'unknown'}")
                logger.debug(f"Tool execution state: {state}")

                result = await tool_node.ainvoke(state)

                # Enhanced logging of tool results with status information
                execution_time = time.time() - start_time
                logger.info(f"Tool execution completed in {execution_time:.2f}s")

                # Process and log tool responses with status information
                if "messages" in result:
                    serialized_messages = []
                    for i, msg in enumerate(result["messages"]):
                        serialized_msg = serialize_message(msg)
                        serialized_messages.append(serialized_msg)

                        # Log detailed tool response information
                        tool_name = serialized_msg.get("name", "unknown")
                        status = serialized_msg.get("status", "unknown")
                        content_preview = str(serialized_msg.get("content", ""))[:100]

                        logger.info(f"Tool '{tool_name}' response {i+1}: status={status}, content_preview='{content_preview}'")

                        # Log additional diagnostic information for tool responses
                        if serialized_msg.get("type") == "tool":
                            if "error_details" in serialized_msg:
                                logger.warning(f"Tool '{tool_name}' error details: {serialized_msg['error_details']}")

                            # Log artifacts if present
                            if serialized_msg.get("artifact"):
                                logger.debug(f"Tool '{tool_name}' has artifact data")

                            # Log additional metadata
                            additional_kwargs = serialized_msg.get("additional_kwargs", {})
                            response_metadata = serialized_msg.get("response_metadata", {})
                            if additional_kwargs:
                                logger.debug(f"Tool '{tool_name}' additional_kwargs: {additional_kwargs}")
                            if response_metadata:
                                logger.debug(f"Tool '{tool_name}' response_metadata: {response_metadata}")

                    result["messages"] = serialized_messages
                    logger.info(f"Processed {len(serialized_messages)} tool response messages")
                else:
                    logger.warning("Tool execution result contains no 'messages' field")
                    logger.debug(f"Raw tool result: {result}")

                return result

            except Exception as e:
                # Track failed execution time
                execution_time = time.time() - start_time
                logger.error(f"Error in tool node after {execution_time:.2f}s: {e}")

                error_messages = []

                last_message = state["messages"][-1]
                tool_calls = (
                    last_message.get("tool_calls", [])
                    if isinstance(last_message, dict)
                    else getattr(last_message, 'tool_calls', [])
                )

                for tool_call in tool_calls:
                    error_msg = {
                        "type": "tool",
                        "content": f"Error executing tool: {str(e)}",
                        "tool_call_id": tool_call.get("id", ""),
                        "name": tool_call.get("name", "unknown"),
                    }
                    error_messages.append(error_msg)

                return {"messages": error_messages}

        return wrapped_tool_node

    @staticmethod
    def create_authorization_node(tool_manager: ArcadeToolManager):
        """Create an authorization node for tools requiring auth."""

        async def authorize(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
            user_id = config["configurable"].get("user_id")
            last_message = state["messages"][-1]

            tool_calls = (
                last_message.get("tool_calls", [])
                if isinstance(last_message, dict)
                else getattr(last_message, 'tool_calls', [])
            )

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                if not tool_manager.requires_auth(tool_name):
                    continue

                try:
                    auth_response = tool_manager.authorize(tool_name, user_id)
                    if auth_response.status != "completed":
                        logger.info(f"Authorization required for {tool_name}")
                        logger.info(f"Auth URL: {auth_response.url}")
                        tool_manager.wait_for_auth(auth_response.id)

                        if not tool_manager.is_authorized(auth_response.id):
                            raise ValueError(f"Authorization failed for {tool_name}")

                except Exception as e:
                    logger.error(f"Authorization error for {tool_name}: {e}")
                    raise e

            return {"messages": []}

        return authorize
