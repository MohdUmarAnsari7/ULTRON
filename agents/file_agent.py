"""
File & Document Specialist Agent for Ultron
Responsible for folder creation, desktop/downloads organization, file reading/writing, PDF/Docx text extraction, and desktop notes.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent

class FileDocAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="FileDocAgent",
            role="File, Folder & Document Specialist",
            supported_tools=[
                "create_folder",
                "organize_folder",
                "read_file",
                "write_file",
                "list_directory",
                "read_directory",
                "read_document",
                "manage_notes"
            ]
        )

    def format_direct_response(self, tool_name: str, args: Dict[str, Any], output: str, success: bool) -> str:
        if not success:
            return f"File operation failed: {output}"

        if tool_name == "create_folder":
            path = args.get("folder_path", "")
            return f"Folder '{path}' created successfully."

        elif tool_name == "organize_folder":
            path = args.get("folder_path", "")
            return f"Successfully organized files in '{path}' into clean categories."

        elif tool_name == "write_file":
            path = args.get("file_path", "")
            mode = args.get("mode", "overwrite")
            if mode == "prepend":
                return f"Successfully prepended content to the top of '{path}'."
            elif mode == "append":
                return f"Successfully appended content to '{path}'."
            return f"Successfully saved file '{path}'."

        elif tool_name == "manage_notes":
            action = args.get("action", "")
            if action == "add":
                return "Saved note to your Desktop notes file."
            return output

        elif tool_name in ["read_file", "read_document", "list_directory"]:
            return output

        return output
