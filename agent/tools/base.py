from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from agent.models import ToolResult

class BaseTool(ABC):
    """Abstract Base Class for all agent tools enforcing explicit contracts & permissions."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name for the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Clear human-readable description of what the tool does."""
        pass

    @property
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema definition of expected tool inputs."""
        return {}

    @property
    def output_schema(self) -> Dict[str, Any]:
        """JSON schema definition of expected tool outputs."""
        return {}

    @property
    def permissions(self) -> Dict[str, bool]:
        """Explicit permission flags governing tool capabilities."""
        return {
            "read_documents": False,
            "internet_access": False,
            "calculation": False,
            "database_access": False
        }

    @abstractmethod
    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Executes the tool with given input parameters and execution context."""
        pass
