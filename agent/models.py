from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class ToolCall:
    tool_name: str
    input_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolResult:
    tool_name: str
    status: str  # "success" or "error"
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "data": self.data,
            "error_message": self.error_message
        }

@dataclass
class RouterDecision:
    intent: str  # "document_search", "web_search", "calculation", "document_metadata", "general"
    recommended_tools: List[str] = field(default_factory=list)
    reasoning: str = ""

@dataclass
class AgentResponse:
    answer: str
    citations: List[Dict[str, Any]] = field(default_factory=list)
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": self.citations,
            "tools_used": self.tools_used,
            "duration": self.duration
        }
