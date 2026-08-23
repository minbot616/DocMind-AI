from typing import Dict, Any, Optional
from agent.tools.base import BaseTool
from agent.models import ToolResult
from database import DatabaseManager

class DocumentMetadataTool(BaseTool):
    """Tool that inspects user's document library metadata, inventory, and statistics."""

    @property
    def name(self) -> str:
        return "document_metadata"

    @property
    def description(self) -> str:
        return "Retrieves document inventory, file names, page counts, chunk stats, and upload details from database."

    @property
    def permissions(self) -> Dict[str, bool]:
        return {
            "read_documents": False,
            "internet_access": False,
            "calculation": False,
            "database_access": True
        }

    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        ctx = context or {}
        user_id = ctx.get("user_id", 1)

        try:
            docs = DatabaseManager.get_documents(user_id)
            formatted_docs = []
            total_pages = 0
            total_chunks = 0

            for d in docs:
                p_count = d.get("pages_count", 0)
                c_count = d.get("chunks_count", 0)
                total_pages += p_count
                total_chunks += c_count

                formatted_docs.append({
                    "document_id": d.get("id"),
                    "filename": d.get("filename"),
                    "file_type": d.get("file_type"),
                    "pages": p_count,
                    "chunks": c_count,
                    "file_size_kb": round(d.get("file_size", 0) / 1024.0, 1),
                    "upload_date": d.get("created_at")
                })

            return ToolResult(
                tool_name=self.name,
                status="success",
                data={
                    "total_documents": len(docs),
                    "total_pages": total_pages,
                    "total_chunks": total_chunks,
                    "documents": formatted_docs
                }
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, status="error", error_message=f"Metadata lookup error: {str(e)}")
