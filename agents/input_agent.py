"""
Input Specialist Agent for Ultron
Responsible for keyboard typing, pressing keys, shortcuts/hotkeys, mouse clicks, movement, and scrolling.
"""

from typing import Dict, Any, Tuple
from agents.base_agent import BaseAgent

class InputAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="InputAgent",
            role="Keyboard & Mouse Actuator",
            supported_tools=[
                "keyboard_type",
                "keyboard_press",
                "keyboard_hotkey",
                "mouse_click",
                "mouse_move",
                "mouse_scroll",
                "mouse_drag",
                "get_cursor_position"
            ]
        )

    def normalize_args(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        norm = dict(args)

        # Normalize keyboard typing
        if tool_name == "keyboard_type":
            t = norm.get("text") or norm.get("content") or norm.get("string") or norm.get("message") or norm.get("input") or ""
            paste = bool(norm.get("paste_mode") or norm.get("paste") or False)
            return "keyboard_type", {"text": str(t), "paste_mode": paste}

        # Normalize keyboard press
        elif tool_name == "keyboard_press":
            k = norm.get("key") or norm.get("key_name") or norm.get("button") or norm.get("k") or "enter"
            return "keyboard_press", {"key": str(k)}

        # Normalize keyboard hotkey
        elif tool_name == "keyboard_hotkey":
            hk = norm.get("keys") or norm.get("hotkey") or norm.get("combination") or norm.get("shortcut") or norm.get("key") or "ctrl+c"
            return "keyboard_hotkey", {"keys": str(hk)}

        # Normalize mouse click
        elif tool_name == "mouse_click":
            btn = norm.get("button") or norm.get("btn") or "left"
            clks = int(norm.get("clicks") or 1)
            x_val = norm.get("x")
            y_val = norm.get("y")
            clean_args = {"button": btn, "clicks": clks}
            if x_val is not None and y_val is not None:
                clean_args["x"] = int(x_val)
                clean_args["y"] = int(y_val)
            return "mouse_click", clean_args

        # Normalize mouse move
        elif tool_name == "mouse_move":
            x_val = norm.get("x") if "x" in norm else norm.get("pos_x", 0)
            y_val = norm.get("y") if "y" in norm else norm.get("pos_y", 0)
            dur = float(norm.get("duration") or 0.2)
            return "mouse_move", {"x": int(x_val), "y": int(y_val), "duration": dur}

        # Normalize mouse scroll
        elif tool_name == "mouse_scroll":
            amt = int(norm.get("amount") or norm.get("clicks") or 5)
            direction = norm.get("direction") or "down"
            return "mouse_scroll", {"amount": amt, "direction": direction}

        # Normalize mouse drag
        elif tool_name == "mouse_drag":
            sx = int(norm.get("start_x") or 0)
            sy = int(norm.get("start_y") or 0)
            ex = int(norm.get("end_x") or 0)
            ey = int(norm.get("end_y") or 0)
            dur = float(norm.get("duration") or 0.5)
            return "mouse_drag", {"start_x": sx, "start_y": sy, "end_x": ex, "end_y": ey, "duration": dur}

        return tool_name, norm

    def fast_verify(self, tool_name: str, args: Dict[str, Any], output: str) -> Tuple[bool, str]:
        """Instant programmatic verification for keyboard and mouse actuators."""
        err_keywords = ["error:", "failed", "exception", "cannot"]
        if any(w in output.lower() for w in err_keywords):
            return False, f"Input action failed: {output}"

        if tool_name == "keyboard_type":
            return True, "Text was successfully dispatched to active window."
        elif tool_name in ["keyboard_press", "keyboard_hotkey"]:
            return True, "Key event was successfully triggered."
        elif tool_name in ["mouse_click", "mouse_move", "mouse_scroll", "mouse_drag"]:
            return True, "Mouse actuation verified."
        elif tool_name == "get_cursor_position":
            return True, "Cursor position retrieved."

        return True, "Input command executed successfully."

    def format_direct_response(self, tool_name: str, args: Dict[str, Any], output: str, success: bool) -> str:
        """Domain-specific direct response generator."""
        if not success:
            return f"Input action failed: {output}"

        if tool_name == "keyboard_type":
            t = args.get("text", "")
            snippet = f"'{t}'" if len(t) <= 30 else f"'{t[:30]}...'"
            return f"I've typed {snippet} into the active window."

        elif tool_name == "keyboard_press":
            key = args.get("key", "").upper()
            return f"I've pressed the '{key}' key."

        elif tool_name == "keyboard_hotkey":
            keys = args.get("keys", "").upper()
            return f"I've executed the '{keys}' shortcut for you."

        elif tool_name == "mouse_click":
            btn = args.get("button", "left").capitalize()
            clicks = args.get("clicks", 1)
            coord_str = f" at ({args['x']}, {args['y']})" if ("x" in args and "y" in args) else ""
            action_type = "Double clicked" if clicks == 2 else f"Clicked {btn}"
            return f"{action_type}{coord_str}."

        elif tool_name == "mouse_move":
            return f"I've moved the cursor to ({args.get('x')}, {args.get('y')})."

        elif tool_name == "mouse_scroll":
            direction = args.get("direction", "down")
            return f"I've scrolled {direction}."

        elif tool_name == "mouse_drag":
            return f"I've dragged from ({args.get('start_x')}, {args.get('start_y')}) to ({args.get('end_x')}, {args.get('end_y')})."

        elif tool_name == "get_cursor_position":
            return output

        return output
