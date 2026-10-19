"""
Shell & Automation Script Specialist Agent for Ultron
Responsible for custom PowerShell terminal commands and custom Python automation scripts.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent

class ShellAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ShellAgent",
            role="PowerShell & Python Script Specialist",
            supported_tools=["run_terminal_command", "execute_python_code"]
        )

    def format_direct_response(self, tool_name: str, args: Dict[str, Any], output: str, success: bool) -> str:
        if not success:
            return f"Terminal execution failed:\n{output}"
        return output
