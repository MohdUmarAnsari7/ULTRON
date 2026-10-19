"""
Base Agent Interface for Ultron Multi-Agent OS Controller
Defines the structure, execution lifecycle, fast verification, and response formatting for specialist agents.
"""

import time
from typing import Dict, Any, Tuple, Optional
from safety import verify_permission
from tools import TOOL_DISPATCHER

class AgentResult:
    def __init__(self, agent_name: str, tool_name: str, success: bool, output: str, note: str = "", direct_response: str = "", latency_ms: float = 0.0):
        self.agent_name = agent_name
        self.tool_name = tool_name
        self.success = success
        self.output = output
        self.note = note
        self.direct_response = direct_response
        self.latency_ms = latency_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "tool": self.tool_name,
            "success": self.success,
            "output": self.output,
            "note": self.note,
            "direct_response": self.direct_response,
            "latency_ms": self.latency_ms
        }

class BaseAgent:
    """Abstract base class for all specialist sub-agents."""
    
    def __init__(self, name: str, role: str, supported_tools: list[str]):
        self.name = name
        self.role = role
        self.supported_tools = set(supported_tools)

    def can_handle(self, tool_name: str) -> bool:
        return tool_name in self.supported_tools

    def normalize_args(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Normalizes parameter aliases from LLM plans to ensure strict signature compatibility."""
        norm = dict(args)
        
        # Folder creation: if path ends with extension, reroute to write_file
        if tool_name == "create_folder":
            p = norm.get("folder_path") or norm.get("folder_name") or norm.get("path") or norm.get("name") or norm.get("dir")
            if p and any(p.lower().endswith(ext) for ext in [".txt", ".md", ".json", ".py", ".csv", ".log", ".html"]):
                return "write_file", {"file_path": p, "content": norm.get("content", ""), "mode": "overwrite"}
            return "create_folder", {"folder_path": p or "New Folder"}

        # Write file
        elif tool_name == "write_file":
            fp = norm.get("file_path") or norm.get("file_name") or norm.get("filename") or norm.get("path") or "output.txt"
            content = norm.get("content") or norm.get("text") or norm.get("data") or norm.get("body") or ""
            mode = norm.get("mode") or "overwrite"
            return "write_file", {"file_path": fp, "content": content, "mode": mode}

        # Read file / read document
        elif tool_name in ["read_file", "read_document"]:
            fp = norm.get("file_path") or norm.get("file_name") or norm.get("filename") or norm.get("path") or ""
            return tool_name, {"file_path": fp}

        # List directory
        elif tool_name == "list_directory":
            dp = norm.get("dir_path") or norm.get("directory_path") or norm.get("path") or norm.get("folder_path") or norm.get("dir") or "."
            return "list_directory", {"dir_path": dp}

        # Open app
        elif tool_name == "open_app":
            app = norm.get("app_name") or norm.get("name") or norm.get("app") or norm.get("application") or ""
            return "open_app", {"app_name": app}

        # Open url
        elif tool_name == "open_url":
            url = norm.get("url") or norm.get("link") or norm.get("site") or norm.get("target") or ""
            browser = norm.get("browser") or "default"
            return "open_url", {"url": url, "browser": browser}

        # Web search
        elif tool_name == "web_search":
            q = norm.get("query") or norm.get("search") or norm.get("q") or ""
            return "web_search", {"query": q}

        # YouTube
        elif tool_name == "play_youtube":
            q = norm.get("query") or norm.get("song") or norm.get("video") or ""
            return "play_youtube", {"query": q}

        # Control volume
        elif tool_name == "control_volume":
            act = norm.get("action") or "set"
            lvl = norm.get("level") if "level" in norm else (norm.get("volume") or norm.get("val") or norm.get("percentage"))
            return "control_volume", {"action": act, "level": lvl}

        return tool_name, norm

    def execute(self, tool_name: str, args: Dict[str, Any]) -> AgentResult:
        """Executes a tool within this agent's domain with timing, permission checks, and fast verification."""
        start_time = time.time()
        
        # Normalize tool arguments for signature resilience
        tool_name, args = self.normalize_args(tool_name, args)
        
        # 1. Safety check
        if not verify_permission(tool_name, args):
            elapsed = (time.time() - start_time) * 1000.0
            return AgentResult(
                agent_name=self.name,
                tool_name=tool_name,
                success=False,
                output="Action authorization denied by user.",
                note="Permission denied by user safety gate.",
                direct_response="Operation was cancelled as user permission was denied.",
                latency_ms=elapsed
            )

        # 2. Lookup tool executor
        executor = TOOL_DISPATCHER.get(tool_name)
        if not executor:
            elapsed = (time.time() - start_time) * 1000.0
            return AgentResult(
                agent_name=self.name,
                tool_name=tool_name,
                success=False,
                output=f"ERROR: Tool '{tool_name}' is not recognized in system dispatcher.",
                note="Tool not found.",
                direct_response=f"I couldn't find the tool '{tool_name}' on this system.",
                latency_ms=elapsed
            )

        # 3. Execute
        try:
            raw_output = executor(**args)
            output_str = str(raw_output)
        except Exception as e:
            output_str = f"Execution exception in {tool_name}: {str(e)}"

        elapsed = (time.time() - start_time) * 1000.0

        # 4. Fast Deterministic Verification (Instant < 1ms)
        success, note = self.fast_verify(tool_name, args, output_str)

        # 5. Domain-specific direct response
        direct_resp = self.format_direct_response(tool_name, args, output_str, success)

        return AgentResult(
            agent_name=self.name,
            tool_name=tool_name,
            success=success,
            output=output_str,
            note=note,
            direct_response=direct_resp,
            latency_ms=elapsed
        )

    def fast_verify(self, tool_name: str, args: Dict[str, Any], output: str) -> Tuple[bool, str]:
        """
        Fast programmatic verification heuristic.
        Checks for obvious success indicators and common failure signals without needing an 8B LLM round-trip.
        """
        out_lower = output.lower()

        # Hard error tokens
        error_signals = [
            "error:", "exception:", "exit_code: 1", "exit_code: 2", "not recognized",
            "parameterbindingexception", "failed to", "permission denied", "access is denied",
            "timed out", "unrecognized"
        ]
        has_error = any(sig in out_lower for sig in error_signals)

        if has_error:
            # Extract first error line for concise note
            lines = [l.strip() for l in output.splitlines() if l.strip()]
            err_line = next((l for l in lines if any(s in l.lower() for s in error_signals)), lines[0] if lines else "Error occurred")
            return False, f"Failed: {err_line[:100]}"

        # Clear success tokens
        success_signals = [
            "successfully", "completed with exit_code: 0", "volume set to", "master volume",
            "created folder", "written to", "prepended to", "appended to", "screenshot saved",
            "notes saved", "timer set for", "triggered media key", "active wi-fi", "pc specifications"
        ]
        if any(sig in out_lower for sig in success_signals):
            return True, "Verified successfully by operating system."

        # Default fallback: if no error was reported and output is non-empty
        if output.strip():
            return True, "Executed without detected OS errors."

        return True, "Executed successfully."

    def format_direct_response(self, tool_name: str, args: Dict[str, Any], output: str, success: bool) -> str:
        """Generates a concise natural language response without needing an LLM call."""
        if not success:
            return f"I ran into an issue with {tool_name}: {output.splitlines()[0] if output else 'Unknown error'}"
        return output
