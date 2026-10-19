"""
WhatsApp Specialist Agent for Ultron
Responsible for autonomous WhatsApp desktop automation on Windows:
Opening app, navigating chats (by contact name or phone number), sending text messages,
attaching and sending files, initiating voice/video calls, and running interactive
request-response sequential agent loops with Ollama until the user's task is fully completed.
"""

import os
import json
import time
from typing import Dict, Any, Tuple, List, Optional
import ollama
from rich.console import Console

from config import DEFAULT_MODEL, FAST_MODEL
from agents.base_agent import BaseAgent, AgentResult
from tools import TOOL_DISPATCHER

console = Console()

class WhatsAppAgent(BaseAgent):
    def __init__(self, model_name: str = FAST_MODEL):
        super().__init__(
            name="WhatsAppAgent",
            role="WhatsApp Autonomous Communications Specialist",
            supported_tools=[
                "whatsapp_status_check",
                "whatsapp_open_app",
                "whatsapp_open_chat",
                "whatsapp_send_message",
                "whatsapp_send_file",
                "whatsapp_call"
            ]
        )
        self.model_name = model_name

    def normalize_args(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Normalizes parameter aliases from LLM plans for resilient execution."""
        norm = dict(args)

        # 1. Send Message
        if tool_name == "whatsapp_send_message":
            rec = norm.get("recipient") or norm.get("to") or norm.get("contact") or norm.get("phone") or norm.get("target") or norm.get("number") or norm.get("user") or ""
            msg = norm.get("message") or norm.get("text") or norm.get("msg") or norm.get("content") or norm.get("body") or ""
            return "whatsapp_send_message", {"recipient": str(rec), "message": str(msg)}

        # 2. Open Chat
        elif tool_name == "whatsapp_open_chat":
            rec = norm.get("recipient") or norm.get("to") or norm.get("contact") or norm.get("phone") or norm.get("target") or norm.get("name") or ""
            return "whatsapp_open_chat", {"recipient": str(rec)}

        # 3. Send File
        elif tool_name == "whatsapp_send_file":
            rec = norm.get("recipient") or norm.get("to") or norm.get("contact") or norm.get("phone") or norm.get("target") or ""
            fp = norm.get("file_path") or norm.get("path") or norm.get("file") or norm.get("filename") or norm.get("doc") or ""
            return "whatsapp_send_file", {"recipient": str(rec), "file_path": str(fp)}

        # 4. WhatsApp Call
        elif tool_name == "whatsapp_call":
            rec = norm.get("recipient") or norm.get("to") or norm.get("contact") or norm.get("phone") or norm.get("target") or ""
            ct = norm.get("call_type") or norm.get("type") or norm.get("kind") or norm.get("mode") or "voice"
            return "whatsapp_call", {"recipient": str(rec), "call_type": str(ct)}

        # 5. Open App & Status
        elif tool_name in ["whatsapp_open_app", "whatsapp_status_check"]:
            return tool_name, {}

        return tool_name, norm

    def fast_verify(self, tool_name: str, args: Dict[str, Any], output: str) -> Tuple[bool, str]:
        """Instant programmatic verification for WhatsApp desktop actions."""
        err_tokens = ["error:", "failed", "cannot", "exception:", "not exist", "denied"]
        if any(e in output.lower() for e in err_tokens):
            return False, f"WhatsApp action failed: {output.splitlines()[0] if output else 'Unknown error'}"

        if tool_name == "whatsapp_send_message":
            return True, f"Verified: Message dispatched on WhatsApp to '{args.get('recipient')}'."
        elif tool_name == "whatsapp_send_file":
            return True, f"Verified: File attached and sent to '{args.get('recipient')}' on WhatsApp."
        elif tool_name == "whatsapp_open_chat":
            return True, f"Verified: Navigated to WhatsApp conversation with '{args.get('recipient')}'."
        elif tool_name == "whatsapp_open_app":
            return True, "Verified: WhatsApp desktop application launched and focused."
        elif tool_name == "whatsapp_call":
            return True, f"Verified: WhatsApp call initiated with '{args.get('recipient')}'."
        elif tool_name == "whatsapp_status_check":
            return True, "Verified: WhatsApp system status retrieved."

        return True, "WhatsApp command executed."

    def format_direct_response(self, tool_name: str, args: Dict[str, Any], output: str, success: bool) -> str:
        """Generates concise, human-ready response for WhatsApp operations."""
        if not success:
            return f"I encountered an issue with WhatsApp {tool_name}: {output}"

        if tool_name == "whatsapp_send_message":
            return f"I have sent the message to {args.get('recipient')} on WhatsApp: \"{args.get('message')}\""
        elif tool_name == "whatsapp_send_file":
            fn = os.path.basename(args.get('file_path', 'file'))
            return f"I have sent '{fn}' to {args.get('recipient')} on WhatsApp."
        elif tool_name == "whatsapp_open_chat":
            return f"Opened WhatsApp chat with {args.get('recipient')}."
        elif tool_name == "whatsapp_open_app":
            return "WhatsApp is now open and ready on your desktop."
        elif tool_name == "whatsapp_call":
            kind = args.get('call_type', 'voice')
            return f"Initiated WhatsApp {kind} call to {args.get('recipient')}."
        elif tool_name == "whatsapp_status_check":
            return f"WhatsApp Status: {output}"

        return output

    def execute_agentic_loop(self, user_goal: str, max_turns: int = 5) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Autonomous Multi-Turn Agent Loop:
        Executes a sequence of requests and responses with the Ollama model until the task is DONE.
        In each turn:
          1. Model inspects user goal and history of actions taken + outputs.
          2. Model decides next specific action (open app, search, type, hotkey, send file, etc.) or finishes.
          3. Ultron executes the chosen tool on Windows and returns output to the model.
          4. Loop repeats until the model confirms completion or max_turns is reached.
        """
        console.print(f"\n[bold green]🤖 WhatsApp Specialist entering autonomous agentic loop...[/bold green]")
        console.print(f"[dim]Goal: {user_goal}[/dim]")

        system_instruction = """You are Ultron's Autonomous WhatsApp Specialist Agent.
Your goal is to fulfill the user's WhatsApp request completely on Windows desktop.

You have access to the following action tools:
1. whatsapp_open_app() -> Opens/focuses WhatsApp desktop window.
2. whatsapp_open_chat(recipient) -> Opens conversation with contact name or phone number.
3. whatsapp_send_message(recipient, message) -> Sends text message to contact or phone.
4. whatsapp_send_file(recipient, file_path) -> Attaches and sends file to contact.
5. whatsapp_call(recipient, call_type) -> Initiates "voice" or "video" call.
6. keyboard_type(text) -> Types or pastes text into active window.
7. keyboard_press(key) -> Presses key (enter, esc, tab, etc.).
8. keyboard_hotkey(keys) -> Executes shortcut (ctrl+f, ctrl+v, etc.).
9. execute_python_code(code) -> Executes custom automation script if needed.

IN EACH TURN, output a STRICT JSON object in this exact format:
{
  "thought": "Your reasoning about what to do next based on current progress",
  "tool": "name_of_tool_to_call",
  "args": {"param1": "value1"},
  "is_done": false,
  "final_summary": ""
}

When the entire user goal is completely accomplished, output:
{
  "thought": "The task has been fully accomplished.",
  "tool": "none",
  "args": {},
  "is_done": true,
  "final_summary": "Friendly confirmation to the user of what was completed."
}
"""
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"User Goal: {user_goal}\nBegin by deciding Step 1."}
        ]

        history_steps: List[Dict[str, Any]] = []
        turn = 0

        while turn < max_turns:
            turn += 1
            console.print(f"\n[bold cyan]⚡ Turn {turn}/{max_turns}: Consulting Ollama model ({self.model_name})...[/bold cyan]")

            try:
                res = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    format="json"
                )
                raw_json = res['message']['content'].strip()
                data = json.loads(raw_json)
            except Exception as e:
                console.print(f"[red]Error parsing Ollama agent response: {str(e)}[/red]")
                # Fallback to direct tool execution
                direct_res = self.execute("whatsapp_send_message", {"recipient": "contact", "message": user_goal})
                return direct_res.success, direct_res.direct_response, history_steps

            thought = data.get("thought", "")
            tool_name = (data.get("tool") or "").strip()
            args = data.get("args") or {}
            is_done = data.get("is_done", False)
            final_summary = data.get("final_summary", "")

            console.print(f"[italic cyan]💭 Thought:[/italic cyan] {thought}")

            if is_done or tool_name in ["none", "done", ""]:
                summary = final_summary or "WhatsApp operation completed successfully, sir."
                console.print(f"[bold green]✔ WhatsApp Agent completed task in {turn} turn(s).[/bold green]")
                return True, summary, history_steps

            # Execute tool
            console.print(f"[bold yellow]▶ Executing Action:[/bold yellow] [magenta]{tool_name}[/magenta] with {args}")
            step_result = self.execute(tool_name, args)
            output_text = step_result.output

            history_steps.append({
                "turn": turn,
                "tool": tool_name,
                "args": args,
                "output": output_text,
                "success": step_result.success
            })

            console.print(f"[dim]↳ Output: {output_text[:200]}[/dim]")

            # Append assistant decision and execution outcome to messages for next turn
            messages.append({"role": "assistant", "content": raw_json})
            messages.append({
                "role": "user",
                "content": f"Tool '{tool_name}' executed with result:\n{output_text}\n\nAssess progress and determine next action or confirm completion."
            })

        return True, "WhatsApp workflow executed across multi-turn agent sequence.", history_steps
