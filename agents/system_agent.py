"""
System & Hardware Specialist Agent for Ultron
Responsible for PC specifications, resource hog diagnostics, process management, window snapping/minimizing, network checks, screenshots, and clipboard.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent

class SystemAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SystemAgent",
            role="System, Hardware & Diagnostic Specialist",
            supported_tools=[
                "get_system_configuration",
                "get_top_resource_hogs",
                "kill_process",
                "open_app",
                "manage_windows",
                "check_network_status",
                "take_screenshot",
                "manage_clipboard"
            ]
        )

    def format_direct_response(self, tool_name: str, args: Dict[str, Any], output: str, success: bool) -> str:
        if not success:
            return f"System action error: {output}"

        if tool_name == "take_screenshot":
            filename = args.get("filename", "screenshot.png")
            return f"Screenshot successfully captured and saved to your Desktop ({filename})."

        elif tool_name == "open_app":
            app = args.get("app_name", "")
            return f"Launched {app}."

        elif tool_name == "manage_windows":
            action = args.get("action", "")
            if action in ["minimize_all", "show_desktop"]:
                return "Minimized all active windows to show the desktop."
            elif action == "maximize":
                return "Maximized current window."
            elif action == "snap_left":
                return "Snapped current window to the left half."
            elif action == "snap_right":
                return "Snapped current window to the right half."
            return output

        elif tool_name == "kill_process":
            proc = args.get("process_name", "")
            return f"Terminated process '{proc}'."

        elif tool_name == "manage_clipboard":
            action = args.get("action", "")
            if action == "set":
                return "Copied text to clipboard."
            return output

        elif tool_name in ["get_system_configuration", "get_top_resource_hogs", "check_network_status"]:
            return output

        return output
