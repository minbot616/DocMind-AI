import logging
from typing import Dict, Any, List, Optional
from agent.tools.base import BaseTool
from agent.models import ToolResult
from agent.tools.document_search import DocumentSearchTool
from agent.tools.document_metadata import DocumentMetadataTool
from agent.tools.web_search import WebSearchTool

logger = logging.getLogger("DocMindBackend")

class ToolRegistry:
    """Centralized Tool Registry for registering, inspecting, and executing tools safely."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Register default tools (Document Search, Document Metadata, Web Search)
        self.register_tool(DocumentSearchTool())
        self.register_tool(DocumentMetadataTool())
        self.register_tool(WebSearchTool())

    def register_tool(self, tool: BaseTool) -> None:
        """Registers a tool instance into the registry."""
        if not isinstance(tool, BaseTool):
            raise TypeError("Only instances of BaseTool can be registered.")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}' in Agent ToolRegistry.")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieves a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns metadata for all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
                "permissions": tool.permissions
            }
            for tool in self._tools.values()
        ]

    def execute_tool(self, name: str, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Executes a tool by name with safety checks and error handling."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                status="error",
                error_message=f"Tool '{name}' is not registered in ToolRegistry."
            )

        try:
            logger.info(f"Executing tool '{name}' with inputs: {input_data}")
            result = tool.execute(input_data, context)
            logger.info(f"Tool '{name}' finished with status='{result.status}'.")
            return result
        except Exception as e:
            logger.exception(f"Unexpected exception while executing tool '{name}'.")
            return ToolResult(
                tool_name=name,
                status="error",
                error_message=f"Tool execution error: {str(e)}"
            )

# Global default instance
default_registry = ToolRegistry()
