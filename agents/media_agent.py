"""
Media & Audio Specialist Agent for Ultron
Responsible for volume levels, audio mute/unmute, media playback controls, and alert timers.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent

class MediaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MediaAgent",
            role="Audio & Playback Specialist",
            supported_tools=["control_volume", "control_media", "set_timer_reminder"]
        )

    def format_direct_response(self, tool_name: str, args: Dict[str, Any], output: str, success: bool) -> str:
        if not success:
            return f"Audio action failed: {output}"

        if tool_name == "control_volume":
            action = args.get("action", "")
            level = args.get("level")
            if action == "set" and level is not None:
                return f"I've set your system volume to {level}%."
            elif action == "mute":
                return "System audio is now muted."
            elif action == "unmute":
                return "System audio has been unmuted."
            elif action in ["increase", "up"]:
                return f"Increased system volume by {level or 10}%."
            elif action in ["decrease", "down"]:
                return f"Decreased system volume by {level or 10}%."
            elif action in ["get", "status"]:
                return output

        elif tool_name == "control_media":
            action = args.get("action", "play_pause")
            if action in ["play_pause", "play", "pause"]:
                return "Toggled media playback (Play/Pause)."
            elif action == "next":
                return "Skipped to the next track."
            elif action in ["previous", "prev"]:
                return "Returned to the previous track."
            elif action == "stop":
                return "Stopped media playback."

        elif tool_name == "set_timer_reminder":
            minutes = args.get("minutes", 1)
            msg = args.get("message", "Timer finished")
            return f"Timer set for {minutes} minute{'s' if minutes != 1 else ''}. I will alert you with an audible chime and desktop popup."

        return output
