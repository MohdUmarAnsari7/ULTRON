"""
Web & Search Specialist Agent for Ultron
Responsible for browser-targeted URL navigation, DuckDuckGo real-time searches, and YouTube video playback.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent

class WebAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="WebAgent",
            role="Web Navigation & Search Specialist",
            supported_tools=["open_url", "web_search", "play_youtube"]
        )

    def format_direct_response(self, tool_name: str, args: Dict[str, Any], output: str, success: bool) -> str:
        if not success:
            return f"Web operation encountered an error: {output}"

        if tool_name == "open_url":
            url = args.get("url", "")
            browser = args.get("browser", "default")
            browser_display = "Google Chrome" if "chrome" in browser.lower() else ("Microsoft Edge" if "edge" in browser.lower() else "your default browser")
            return f"Opened {url} in {browser_display}."

        elif tool_name == "play_youtube":
            query = args.get("query", "")
            return f"Playing '{query}' on YouTube in your browser."

        elif tool_name == "web_search":
            # For web search, return formatted summary of top result or the output
            return output

        return output
