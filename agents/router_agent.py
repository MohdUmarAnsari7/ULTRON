"""
Fast Router Agent for Ultron
Provides sub-millisecond intent classification, zero-latency direct routing for common OS operations,
compound command decomposition, and fallback to fast LLM planning.
"""

import re
import json
import random
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import ollama

from config import DEFAULT_MODEL, FAST_MODEL, ROUTER_MODEL, USE_TEV1_ROUTER
from tools import TOOL_SCHEMAS_DESCRIPTION

class FastChatEngine:
    """Ultra-fast conversational dialogue engine for casual chatting (<1ms latency)."""
    @staticmethod
    def get_quick_response(text: str) -> Optional[str]:
        t = text.lower().strip(" .!?,:;")

        # 1. Greetings
        if re.search(r'\b(hi|hello|hey|greetings|howdy|yo|hi ultron|hello ultron|hey ultron|good (?:morning|evening|afternoon|day))\b', t):
            options = [
                "Hello, sir! Ultron is online and standing by. What can I do for you today?",
                "Greetings! All system modules and specialist agents are active. How can I assist you?",
                "Hello there! Ready to execute any command or chat whenever you are.",
                "Hey! Ultron is right here. Let me know what you need."
            ]
            return random.choice(options)

        # 2. How are you / Status
        if re.search(r'\b(how are you|how are you doing|how\'s it going|what\'s up|how do you feel|how are things|how are you today)\b', t):
            options = [
                "I'm operating in peak condition, sir! All system modules are running smoothly and ready for your commands.",
                "Doing fantastic! My multi-agent swarm is primed and ready to automate your desktop or assist with your work.",
                "All systems operational at maximum efficiency! How are you doing today?",
                "Running fast and clean, sir. Ready for your next instruction."
            ]
            return random.choice(options)

        # 3. Who are you / Identity / Creator
        if re.search(r'\b(who are you|what is your name|who made you|who created you|introduce yourself|tell me about yourself)\b', t):
            return "I am Ultron, an autonomous Windows AI OS Controller powered by a local multi-agent swarm. I manage your audio, launch apps, browse the web, organize files, diagnose PC lag, and run PowerShell automation directly on your machine."

        # 4. What can you do / Capabilities
        if re.search(r'\b(what can you do|what are your capabilities|help me|what do you do)\b', t):
            return "I can control your volume and media, launch apps and websites, perform web searches, create and organize folders/files, summarize documents, diagnose PC performance bottlenecks, take screenshots, and execute PowerShell commands."

        # 5. Jokes / Humor
        if re.search(r'\b(joke|funny|laugh|make me laugh|tell a joke)\b', t):
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "There are 10 types of people in the world: those who understand binary, and those who don't.",
                "Why did the computer keep freezing? Because it left its Windows open!",
                "An SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
                "Why do Java developers wear glasses? Because they don't C#!"
            ]
            return random.choice(jokes)

        # 6. Gratitude / Thanks
        if re.search(r'\b(thank you|thanks|appreciate it|thx|great job|nice work|awesome|well done)\b', t):
            options = [
                "You're very welcome, sir! Always at your service.",
                "Glad I could help! Let me know if you need anything else.",
                "Happy to assist! Ultron standing by for your next instruction."
            ]
            return random.choice(options)

        # 7. Readiness / Availability
        if re.search(r'\b(are you ready|can you help|are you there|you there|can you hear me)\b', t):
            return "Yes, sir! Standing by and ready for your command."

        # 8. Affirmations & small talk
        if t in ["cool", "nice", "ok", "okay", "alright", "got it", "fine", "good", "perfect", "sounds good", "great", "sure", "yep", "yeah"]:
            return "Understood, sir. Let me know when you'd like to run your next task."

        return None

class FastRouterAgent:
    def __init__(self, active_model: str = DEFAULT_MODEL, router_model: str = ROUTER_MODEL):
        self.active_model = active_model
        self.router_model = router_model

    def decide_with_tev1(self, text: str, question: str, choices: Dict[str, str]) -> Tuple[str, int]:
        """Queries the tev1:4b Ollama decision model with --keepalive 60m using --ask and --choice."""
        cmd = ["ollama", "run", "--keepalive", "60m", self.router_model, "--ask", question]
        for k, v in choices.items():
            cmd.extend(["--choice", f"{k}={v}"])
        try:
            r = subprocess.run(cmd, input=text, encoding="utf-8", errors="replace", capture_output=True, timeout=25)
            out = r.stdout.strip()
            m = re.search(r'([a-zA-Z0-9_\-]+)\s+(\d+)%', out)
            if m:
                return m.group(1), int(m.group(2))
        except Exception:
            pass
        return "unknown", 0

    def route_with_tev1(self, text: str) -> Dict[str, Any]:
        """
        Unified single-stage decision classification using tev1:4b:
        Determines whether input is 'chat' or a specific task domain ('media', 'web', 'system', 'file', 'shell')
        in a single fast call with --keepalive 60m, eliminating intermediate model-swap latency.
        """
        category, conf = self.decide_with_tev1(
            text,
            "What is the intent or category of this input?",
            {
                "chat": "Casual greeting, small talk, conversation, general talk, or general question",
                "media": "Audio volume, mute, music playback, or countdown timer",
                "web": "Web browser, website URL, web search, or YouTube",
                "system": "Hardware specs, PC lag, processes, windows, screenshot",
                "input": "Keyboard typing, pressing keys, hotkeys, mouse clicks, move mouse, scroll",
                "file": "Files, folders, directory, file read/write, document summary",
                "whatsapp": "WhatsApp messages, opening WhatsApp, chat, sending files, or voice/video calls",
                "shell": "PowerShell command or Python code"
            }
        )

        if category == "chat":
            return {
                "is_task": False,
                "intent": "chat",
                "confidence": conf,
                "domain": None,
                "domain_confidence": 0
            }

        return {
            "is_task": True,
            "intent": "task",
            "confidence": conf,
            "domain": category if category != "unknown" else "general",
            "domain_confidence": conf
        }

    def _generate_chat_reply(self, user_text: str, history: list = None) -> str:
        """Generates a warm, conversational reply using Ollama without tool calls."""
        prompt = "You are Ultron, a friendly and intelligent Windows AI assistant. Respond conversationally, warmly, and concisely (1-2 sentences) to the user's remark."
        messages = [{"role": "system", "content": prompt}]
        if history:
            for h in history[-2:]:
                messages.append(h)
        messages.append({"role": "user", "content": user_text})
        try:
            res = ollama.chat(model=self.active_model, messages=messages)
            return res['message']['content'].strip()
        except Exception:
            return "Hello! I am Ultron. How can I assist you with your computer today?"

    def _match_workflow_template(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Sub-millisecond matcher for common multi-action compound workflows.
        Bypasses LLM planning and eliminates model swapping delays.
        """
        t = text.strip()
        tl = t.lower()

        # Workflow 1: Create folder + create file + write directory summary
        m1 = re.search(
            r'create\s+(?:a\s+)?folder\s+.*?["\']?([a-zA-Z0-9_\-]+)["\']?\s+and\s+create\s+(?:a\s+)?file\s+.*?["\']?([a-zA-Z0-9_\-\.]+)["\']?\s+and\s+(?:create|write|put)\s+(?:a\s+)?summary',
            t,
            re.IGNORECASE
        )
        if m1:
            folder = m1.group(1).strip()
            filename = m1.group(2).strip()
            return {
                "is_conversational": False,
                "direct_response": "",
                "parallel_eligible": False,
                "plan": [
                    {
                        "step": 1,
                        "agent": "FileDocAgent",
                        "description": f"Create directory '{folder}'",
                        "tool": "create_folder",
                        "args": {"folder_path": folder}
                    },
                    {
                        "step": 2,
                        "agent": "FileDocAgent",
                        "description": "Inspect directory contents",
                        "tool": "list_directory",
                        "args": {"dir_path": "."}
                    },
                    {
                        "step": 3,
                        "agent": "FileDocAgent",
                        "description": f"Write directory summary into {folder}/{filename}",
                        "tool": "write_file",
                        "args": {
                            "file_path": f"{folder}/{filename}",
                            "content": f"Summary report of directory for folder '{folder}'.",
                            "mode": "overwrite"
                        }
                    }
                ]
            }

        # Workflow 2: Screenshot + Volume
        m2_vol = re.search(r'set\s+(?:the\s+)?(?:system\s+)?volume\s+(?:to\s+)?(\d+)%?', tl)
        if "screenshot" in tl and m2_vol:
            vol_val = int(m2_vol.group(1))
            return {
                "is_conversational": False,
                "direct_response": "",
                "parallel_eligible": True,
                "plan": [
                    {
                        "step": 1,
                        "agent": "SystemAgent",
                        "description": "Capture screen snapshot",
                        "tool": "take_screenshot",
                        "args": {"filename": "ultron_snapshot.png"}
                    },
                    {
                        "step": 2,
                        "agent": "MediaAgent",
                        "description": f"Set system volume to {vol_val}%",
                        "tool": "control_volume",
                        "args": {"action": "set", "level": vol_val}
                    }
                ]
            }

        # Workflow 3: Specs + Browser
        m3_browser = re.search(r'open\s+([a-zA-Z0-9_\-\.\/]+)(?:\s+(?:on|in)(?:\s+my)?\s+(chrome|edge|firefox))', tl)
        if any(w in tl for w in ["system specs", "hardware specs", "system configuration", "pc specs"]) and m3_browser:
            url = m3_browser.group(1).strip()
            browser = m3_browser.group(2).strip()
            return {
                "is_conversational": False,
                "direct_response": "",
                "parallel_eligible": True,
                "plan": [
                    {
                        "step": 1,
                        "agent": "SystemAgent",
                        "description": "Inspect system hardware and OS configuration",
                        "tool": "get_system_configuration",
                        "args": {}
                    },
                    {
                        "step": 2,
                        "agent": "WebAgent",
                        "description": f"Open {url} in {browser}",
                        "tool": "open_url",
                        "args": {"url": url, "browser": browser}
                    }
                ]
            }

        # Workflow 4: WhatsApp Autonomous Multi-Turn Agent Loop
        if re.search(r'\b(?:operate\s+whatsapp|whatsapp\s+agent|autonomous\s+whatsapp|whatsapp\s+sequence|interactive\s+whatsapp)\b', tl):
            return {
                "is_conversational": False,
                "direct_response": "",
                "parallel_eligible": False,
                "agentic_loop": "WhatsAppAgent",
                "plan": []
            }

        # Workflow 5: Open WhatsApp + Send Message
        m5_wa = re.search(r'open\s+whatsapp\s+(?:and\s+)?(?:send\s+(?:a\s+)?message\s+to|message)\s+([a-zA-Z0-9_\+\s]+?)\s+(?:saying|with|:)\s+(.+)', t, re.IGNORECASE)
        if m5_wa:
            recipient = m5_wa.group(1).strip()
            msg = m5_wa.group(2).strip(" '\"")
            return {
                "is_conversational": False,
                "direct_response": "",
                "parallel_eligible": False,
                "plan": [
                    {
                        "step": 1,
                        "agent": "WhatsAppAgent",
                        "description": "Launch and focus WhatsApp application",
                        "tool": "whatsapp_open_app",
                        "args": {}
                    },
                    {
                        "step": 2,
                        "agent": "WhatsAppAgent",
                        "description": f"Send message to '{recipient}'",
                        "tool": "whatsapp_send_message",
                        "args": {"recipient": recipient, "message": msg}
                    }
                ]
            }

        # Workflow 6: Open WhatsApp + Send File
        m6_wa = re.search(r'open\s+whatsapp\s+(?:and\s+)?send\s+(?:(?:file|document|photo|image|doc)\s+)?([a-zA-Z0-9_\-\.\/\\]+)\s+to\s+([a-zA-Z0-9_\+\s]+)', t, re.IGNORECASE)
        if m6_wa:
            filepath = m6_wa.group(1).strip()
            recipient = m6_wa.group(2).strip()
            return {
                "is_conversational": False,
                "direct_response": "",
                "parallel_eligible": False,
                "plan": [
                    {
                        "step": 1,
                        "agent": "WhatsAppAgent",
                        "description": "Launch and focus WhatsApp application",
                        "tool": "whatsapp_open_app",
                        "args": {}
                    },
                    {
                        "step": 2,
                        "agent": "WhatsAppAgent",
                        "description": f"Attach and send '{filepath}' to '{recipient}'",
                        "tool": "whatsapp_send_file",
                        "args": {"recipient": recipient, "file_path": filepath}
                    }
                ]
            }

        return None

    def route(self, user_text: str, history: list = None) -> Dict[str, Any]:
        """
        Routes the user request using tev1:4b unified decision classification,
        sub-millisecond fast-paths, template workflows, and multi-step planner.
        """
        clean_text = user_text.strip()
        
        # 1. ALWAYS classify with tev1 decision model
        tev1_info = None
        if USE_TEV1_ROUTER:
            tev1_info = self.route_with_tev1(clean_text)
            
            # If tev1 classifies as casual chat, respond immediately
            if not tev1_info.get("is_task", True) and tev1_info.get("confidence", 0) >= 60:
                # Instant response for general talk & conversation (<1ms)
                quick_reply = FastChatEngine.get_quick_response(clean_text)
                if quick_reply:
                    return {
                        "is_conversational": True,
                        "direct_response": quick_reply,
                        "plan": [],
                        "parallel_eligible": False,
                        "tev1_decision": tev1_info
                    }
                # Fallback to LLM chat reply for deep generative questions
                chat_reply = self._generate_chat_reply(clean_text, history)
                return {
                    "is_conversational": True,
                    "direct_response": chat_reply,
                    "plan": [],
                    "parallel_eligible": False,
                    "tev1_decision": tev1_info
                }

        # 2. Check dedicated multi-action workflow templates (<1ms)
        workflow_plan = self._match_workflow_template(clean_text)
        if workflow_plan:
            workflow_plan["tev1_decision"] = tev1_info
            return workflow_plan

        # 3. Compound command check (e.g. "take a screenshot and set volume to 50%")
        compound_plan = self._check_compound(clean_text)
        if compound_plan:
            compound_plan["tev1_decision"] = tev1_info
            return compound_plan

        # 4. Single deterministic fast-path (<1ms)
        single_step = self._match_fast_path_step(clean_text)
        if single_step:
            return {
                "is_conversational": False,
                "direct_response": "",
                "plan": [single_step],
                "parallel_eligible": False,
                "tev1_decision": tev1_info
            }

        # 5. Fallback to Multi-Agent Planner with tev1 domain guidance
        target_domain = tev1_info.get("domain") if tev1_info else None
        plan_data = self._plan_with_llm(clean_text, history, target_domain=target_domain)
        plan_data["tev1_decision"] = tev1_info
        return plan_data

    def _check_conversational(self, text: str) -> Optional[str]:
        t = text.lower().strip(" .!?,")
        greetings = {
            "hello": "Hello! Ultron is standing by. How can I assist your system today?",
            "hi": "Greetings! What task would you like me to execute?",
            "hey": "Hey there! Ready for your command.",
            "who are you": "I am Ultron, an autonomous Windows AI OS Controller and Multi-Agent system.",
            "what can you do": "I can control audio, launch apps, browse websites, manage files and folders, capture screenshots, diagnose PC lag, run PowerShell commands, and automate Windows workflows.",
            "good morning": "Good morning! Standing by for commands.",
            "good evening": "Good evening! How can I assist you tonight?",
            "thanks": "You're welcome! Let me know if you need anything else.",
            "thank you": "Glad to help! Ultron standing by."
        }
        return greetings.get(t)

    def _match_fast_path_step(self, text: str) -> Optional[Dict[str, Any]]:
        """Matches a single user command against optimized regex patterns in < 1ms."""
        t = text.strip()
        # Multi-action or compound requests must never be matched as single steps
        if re.search(r'\s+(?:and then|and also|and|then|after that|also)\s+', t, flags=re.IGNORECASE):
            return None

        tl = t.lower()

        # --- A. Audio & Media ---
        # "set volume to 80%", "set the system volume to 80%", "volume to 50%"
        m = re.search(r'(?:set\s+(?:the\s+)?(?:system\s+)?volume\s+(?:to\s+)?|volume\s+(?:to\s+)?)(\d{1,3})%?', tl)
        if m:
            lvl = int(m.group(1))
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": f"Set system volume to {lvl}%",
                "tool": "control_volume",
                "args": {"action": "set", "level": lvl}
            }

        if re.search(r'\bmute(?:\s+(?:the\s+)?(?:system\s+)?audio|\s+(?:the\s+)?(?:system\s+)?volume)?\b', tl):
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": "Mute system audio",
                "tool": "control_volume",
                "args": {"action": "mute"}
            }

        if re.search(r'\bunmute(?:\s+(?:the\s+)?(?:system\s+)?audio|\s+(?:the\s+)?(?:system\s+)?volume)?\b', tl):
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": "Unmute system audio",
                "tool": "control_volume",
                "args": {"action": "unmute"}
            }

        m = re.search(r'(?:increase|turn\s+up|raise)\s+(?:the\s+)?(?:system\s+)?volume(?:\s+by\s+(\d{1,2}))?', tl)
        if m or tl in ["volume up", "louder"]:
            step_lvl = int(m.group(1)) if (m and m.group(1)) else 10
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": f"Increase system volume by {step_lvl}%",
                "tool": "control_volume",
                "args": {"action": "increase", "level": step_lvl}
            }

        m = re.search(r'(?:decrease|turn\s+down|lower)\s+(?:the\s+)?(?:system\s+)?volume(?:\s+by\s+(\d{1,2}))?', tl)
        if m or tl in ["volume down", "quieter"]:
            step_lvl = int(m.group(1)) if (m and m.group(1)) else 10
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": f"Decrease system volume by {step_lvl}%",
                "tool": "control_volume",
                "args": {"action": "decrease", "level": step_lvl}
            }

        if re.search(r'\b(what is|check|get)\s+(?:the\s+)?(?:current\s+)?(?:system\s+)?volume\b', tl):
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": "Check current system volume level",
                "tool": "control_volume",
                "args": {"action": "get"}
            }

        # Media playback
        if re.search(r'\b(pause|play)\s+(music|song|playback|media|video)\b', tl) or tl in ["pause", "play", "play/pause"]:
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": "Toggle media playback",
                "tool": "control_media",
                "args": {"action": "play_pause"}
            }

        if re.search(r'\bnext\s+(song|track)\b', tl) or tl in ["next song", "next track"]:
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": "Next media track",
                "tool": "control_media",
                "args": {"action": "next"}
            }

        if re.search(r'\b(previous|prev)\s+(song|track)\b', tl):
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": "Previous media track",
                "tool": "control_media",
                "args": {"action": "previous"}
            }

        # Timer
        m = re.search(r'set\s+(?:a\s+)?timer\s+for\s+(\d+)\s*(min|minute|sec|second)s?', tl)
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            mins = val if "min" in unit else max(1, val // 60)
            return {
                "step": 1,
                "agent": "MediaAgent",
                "description": f"Set countdown timer for {mins} minutes",
                "tool": "set_timer_reminder",
                "args": {"minutes": mins, "message": f"{mins}-minute timer finished!"}
            }

        # --- B. Web, Browser & YouTube ---
        # "play ... on youtube"
        m = re.search(r'play\s+(.+?)\s+on\s+youtube', tl)
        if m:
            query = m.group(1).strip()
            return {
                "step": 1,
                "agent": "WebAgent",
                "description": f"Play '{query}' on YouTube",
                "tool": "play_youtube",
                "args": {"query": query}
            }

        # "open github on chrome", "open google.com in my chrome", "open instagram in edge"
        m = re.search(r'open\s+([a-zA-Z0-9_\-\.\/]+)(?:\s+(?:on|in)(?:\s+my)?\s+(chrome|edge|firefox))', tl)
        if m:
            target = m.group(1).strip()
            browser = m.group(2).strip()
            return {
                "step": 1,
                "agent": "WebAgent",
                "description": f"Open {target} in {browser}",
                "tool": "open_url",
                "args": {"url": target, "browser": browser}
            }

        # "open github", "open instagram", "open youtube", "open reddit", "open twitter"
        known_sites = ["github", "instagram", "youtube", "reddit", "twitter", "x", "google", "linkedin", "chatgpt"]
        m = re.search(r'open\s+([a-zA-Z0-9_\-\.]+)(?:\.com)?\s*$', tl)
        if m:
            candidate = m.group(1).strip()
            if candidate in known_sites or ".com" in tl or ".org" in tl or ".io" in tl or ".net" in tl:
                return {
                    "step": 1,
                    "agent": "WebAgent",
                    "description": f"Open {candidate} in web browser",
                    "tool": "open_url",
                    "args": {"url": candidate, "browser": "default"}
                }

        # Live search: "what is the weather in Delhi", "who won the match", "search web for ..."
        m = re.search(r'(?:search\s+(?:the\s+)?web\s+for|google|search\s+for)\s+(.+)', tl)
        if m:
            query = m.group(1).strip()
            return {
                "step": 1,
                "agent": "WebAgent",
                "description": f"Search the web for '{query}'",
                "tool": "web_search",
                "args": {"query": query}
            }

        if re.search(r'^(?:what is the weather|weather in|who won|latest news on)\b', tl):
            return {
                "step": 1,
                "agent": "WebAgent",
                "description": f"Search web for '{t}'",
                "tool": "web_search",
                "args": {"query": t}
            }

        # --- C. System & Hardware ---
        if re.search(r'\b(system configuration|pc specs|hardware specs|specs|system info|system metrics)\b', tl):
            return {
                "step": 1,
                "agent": "SystemAgent",
                "description": "Retrieve comprehensive PC hardware specifications",
                "tool": "get_system_configuration",
                "args": {}
            }

        if re.search(r'\b(why is my pc lagging|resource hogs|ram hogs|cpu hogs|check lag)\b', tl):
            return {
                "step": 1,
                "agent": "SystemAgent",
                "description": "Diagnose PC lag and find top memory/CPU hogs",
                "tool": "get_top_resource_hogs",
                "args": {"count": 5}
            }

        if re.search(r'\b(take\s+(?:a\s+)?screenshot|screen\s+capture|capture\s+screen)\b', tl):
            return {
                "step": 1,
                "agent": "SystemAgent",
                "description": "Capture full screen screenshot to Desktop",
                "tool": "take_screenshot",
                "args": {"filename": "screenshot.png"}
            }

        if re.search(r'\b(check\s+network|wifi|what wifi|internet connection|network status)\b', tl):
            return {
                "step": 1,
                "agent": "SystemAgent",
                "description": "Check Wi-Fi network and connection status",
                "tool": "check_network_status",
                "args": {}
            }

        if re.search(r'\b(minimize\s+all(?:\s+windows)?|show\s+desktop)\b', tl):
            return {
                "step": 1,
                "agent": "SystemAgent",
                "description": "Minimize all active windows",
                "tool": "manage_windows",
                "args": {"action": "minimize_all"}
            }

        m = re.search(r'\bkill\s+(?:process\s+)?([a-zA-Z0-9_\-\.]+)\b', tl)
        if m:
            proc = m.group(1).strip()
            return {
                "step": 1,
                "agent": "SystemAgent",
                "description": f"Terminate process '{proc}'",
                "tool": "kill_process",
                "args": {"process_name": proc}
            }

        # Open desktop application: "open calculator", "open notepad", "open chrome"
        known_apps = ["calculator", "calc", "notepad", "chrome", "spotify", "code", "vscode", "terminal", "paint", "settings", "task manager", "taskmgr"]
        m = re.search(r'open\s+([a-zA-Z0-9_\-\s]+)$', tl)
        if m:
            app = m.group(1).strip()
            if app in known_apps:
                return {
                    "step": 1,
                    "agent": "SystemAgent",
                    "description": f"Launch desktop application '{app}'",
                    "tool": "open_app",
                    "args": {"app_name": app}
                }

        # Clipboard
        if re.search(r'\b(what is in my clipboard|read clipboard|show clipboard|paste clipboard)\b', tl):
            return {
                "step": 1,
                "agent": "SystemAgent",
                "description": "Read clipboard contents",
                "tool": "manage_clipboard",
                "args": {"action": "read"}
            }

        # --- D. Files, Folders & Documents ---
        # "create a folder in this current directory name it New Project", "create a folder named New Project"
        m = re.search(r'(?:create|make)\s+(?:a\s+)?folder(?:.*?)(?:name(?:d|\s+it)?|called)\s+[\'"]?([^\'"]+)[\'"]?', t, flags=re.IGNORECASE)
        if not m:
            m = re.search(r'(?:create|make)\s+(?:a\s+)?folder\s+[\'"]?([^\'"]+)[\'"]?', t, flags=re.IGNORECASE)
        if not m:
            m = re.search(r'mkdir\s+[\'"]?([^\'"]+)[\'"]?', t, flags=re.IGNORECASE)
        if m:
            folder_name = m.group(1).strip()
            return {
                "step": 1,
                "agent": "FileDocAgent",
                "description": f"Create directory '{folder_name}' safely",
                "tool": "create_folder",
                "args": {"folder_path": folder_name}
            }

        # Organize downloads/desktop
        m = re.search(r'(?:clean\s+up|clean|organize)\s+(?:my\s+)?(downloads|desktop)', tl)
        if m:
            target = m.group(1).strip().capitalize()
            return {
                "step": 1,
                "agent": "FileDocAgent",
                "description": f"Organize {target} folder into clean subcategories",
                "tool": "organize_folder",
                "args": {"folder_path": target}
            }

        # Notes
        m = re.search(r'note\s+down\s+(.+)', tl)
        if m:
            note_val = m.group(1).strip()
            return {
                "step": 1,
                "agent": "FileDocAgent",
                "description": "Save note to Desktop notes",
                "tool": "manage_notes",
                "args": {"action": "add", "note_text": note_val}
            }

        if re.search(r'\b(show|read)\s+(?:my\s+)?notes\b', tl):
            return {
                "step": 1,
                "agent": "FileDocAgent",
                "description": "Read Desktop notes",
                "tool": "manage_notes",
                "args": {"action": "read"}
            }

        # List directory
        if tl in ["dir", "ls", "list directory", "list files", "show files"]:
            return {
                "step": 1,
                "agent": "FileDocAgent",
                "description": "List files and folders in current directory",
                "tool": "list_directory",
                "args": {"dir_path": "."}
            }

        # --- E. Keyboard & Mouse Input ---
        # Typing: "type hello world", "type in google.com", "type 'my password'"
        m = re.search(r'^(?:type|type\s+in|type\s+text|write\s+text)\s+["\']?(.+?)["\']?$', t, re.IGNORECASE)
        if m:
            text_to_type = m.group(1).strip()
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": f"Type '{text_to_type}' into active window",
                "tool": "keyboard_type",
                "args": {"text": text_to_type}
            }

        # Press single key: "press enter", "hit enter", "press esc", "press escape", "press tab", "press space", "press backspace", "press win", "press windows key"
        m = re.search(r'^(?:press|hit)\s+(?:the\s+)?(enter|return|esc|escape|tab|space|backspace|delete|win|windows|windows\s+key|up|down|left|right|f1|f2|f3|f4|f5|f6|f7|f8|f9|f10|f11|f12)$', tl)
        if m:
            key_name = m.group(1).replace(" ", "_").strip()
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": f"Press '{key_name}' key",
                "tool": "keyboard_press",
                "args": {"key": key_name}
            }

        # Hotkeys & Shortcuts: "press ctrl+c", "press ctrl+v", "press alt+tab", "press win+d", "press ctrl+shift+esc", "press ctrl+s"
        m = re.search(r'^(?:press|hit|execute)\s+(?:hotkey\s+|shortcut\s+)?([a-zA-Z0-9\+\,\s]+)$', tl)
        if m and any(k in tl for k in ["ctrl", "alt", "shift", "win", "+"]):
            hotkey_str = m.group(1).strip()
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": f"Execute hotkey shortcut '{hotkey_str}'",
                "tool": "keyboard_hotkey",
                "args": {"keys": hotkey_str}
            }

        # Quick keyboard action words
        if tl in ["copy", "copy that", "copy selection"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Copy selection to clipboard (Ctrl+C)",
                "tool": "keyboard_hotkey",
                "args": {"keys": "ctrl+c"}
            }
        if tl in ["paste", "paste that", "paste here"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Paste clipboard content (Ctrl+V)",
                "tool": "keyboard_hotkey",
                "args": {"keys": "ctrl+v"}
            }
        if tl in ["select all", "select everything"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Select all content (Ctrl+A)",
                "tool": "keyboard_hotkey",
                "args": {"keys": "ctrl+a"}
            }
        if tl in ["save", "save file", "save document"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Save current file (Ctrl+S)",
                "tool": "keyboard_hotkey",
                "args": {"keys": "ctrl+s"}
            }
        if tl in ["undo", "undo that"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Undo last action (Ctrl+Z)",
                "tool": "keyboard_hotkey",
                "args": {"keys": "ctrl+z"}
            }

        # Mouse click:
        # "click at 500, 300", "right click at 200, 400", "double click at 100, 100"
        m = re.search(r'^(?:mouse\s+)?(left\s+click|right\s+click|double\s+click|click)\s+(?:at|on)?\s*(\d+)[\s,]+(\d+)$', tl)
        if m:
            action_type = m.group(1)
            x_pos = int(m.group(2))
            y_pos = int(m.group(3))
            btn = "right" if "right" in action_type else "left"
            clks = 2 if "double" in action_type else 1
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": f"{action_type.capitalize()} at ({x_pos}, {y_pos})",
                "tool": "mouse_click",
                "args": {"button": btn, "clicks": clks, "x": x_pos, "y": y_pos}
            }

        # "click", "left click", "right click", "double click" (at current pos)
        if tl in ["click", "left click", "click mouse", "mouse click"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Click left mouse button",
                "tool": "mouse_click",
                "args": {"button": "left", "clicks": 1}
            }
        if tl in ["right click", "right mouse click"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Click right mouse button",
                "tool": "mouse_click",
                "args": {"button": "right", "clicks": 1}
            }
        if tl in ["double click", "double click mouse"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Double click left mouse button",
                "tool": "mouse_click",
                "args": {"button": "left", "clicks": 2}
            }

        # Mouse move: "move mouse to 500, 500", "move cursor to 100, 200"
        m = re.search(r'^(?:move\s+)?(?:mouse|cursor)\s+to\s+(\d+)[\s,]+(\d+)$', tl)
        if m:
            x_pos = int(m.group(1))
            y_pos = int(m.group(2))
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": f"Move mouse cursor to ({x_pos}, {y_pos})",
                "tool": "mouse_move",
                "args": {"x": x_pos, "y": y_pos}
            }

        # Mouse scroll: "scroll down", "scroll up", "scroll down 5", "scroll up 10"
        m = re.search(r'^scroll\s+(down|up)(?:\s+(\d+))?', tl)
        if m:
            direction = m.group(1)
            amt = int(m.group(2)) if m.group(2) else 5
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": f"Scroll {direction} {amt} units",
                "tool": "mouse_scroll",
                "args": {"amount": amt, "direction": direction}
            }

        # Cursor position: "where is my mouse", "mouse position", "cursor position"
        if tl in ["where is my mouse", "mouse position", "cursor position", "get cursor position", "get mouse position"]:
            return {
                "step": 1,
                "agent": "InputAgent",
                "description": "Get current mouse coordinates and resolution",
                "tool": "get_cursor_position",
                "args": {}
            }

        # --- H. WhatsApp Desktop Automation ---
        # 1. WhatsApp status check
        if re.search(r'\b(?:check\s+)?whatsapp\s+status\b|\bis\s+whatsapp\s+(?:running|installed|open)\b', tl):
            return {
                "step": 1,
                "agent": "WhatsAppAgent",
                "description": "Check WhatsApp installation and runtime status",
                "tool": "whatsapp_status_check",
                "args": {}
            }

        # 2. Open / focus WhatsApp
        if re.search(r'^(?:open|launch|start|bring\s+up|focus)\s+whatsapp$', tl) or tl in ["whatsapp", "open whatsapp", "launch whatsapp"]:
            return {
                "step": 1,
                "agent": "WhatsAppAgent",
                "description": "Launch and focus WhatsApp application",
                "tool": "whatsapp_open_app",
                "args": {}
            }

        # 3. Open specific chat
        m_chat = re.search(r'^(?:open|go\s+to)\s+(?:the\s+)?(?:chat\s+(?:with|of)|whatsapp\s+chat\s+(?:with|of))\s+([a-zA-Z0-9_\+\s]+?)(?:\s+on\s+whatsapp)?$', tl)
        if not m_chat:
            m_chat = re.search(r'^(?:open|show)\s+([a-zA-Z0-9_\+\s]+?)(?:\'s|\s+)?chat(?:\s+on\s+whatsapp)?$', tl)
        if m_chat:
            target_user = m_chat.group(1).strip()
            return {
                "step": 1,
                "agent": "WhatsAppAgent",
                "description": f"Open WhatsApp chat with '{target_user}'",
                "tool": "whatsapp_open_chat",
                "args": {"recipient": target_user}
            }

        # 4. Send WhatsApp message:
        # "send whatsapp to <recipient> saying <msg>"
        # "send a whatsapp message to <recipient>: <msg>"
        # "message <recipient> on whatsapp saying <msg>"
        # "whatsapp <recipient>: <msg>"
        # "tell <recipient> on whatsapp that <msg>"
        m_msg = re.search(r'^(?:send\s+(?:a\s+)?whatsapp\s+(?:message\s+)?to|whatsapp)\s+([a-zA-Z0-9_\+\s]+?)(?:\s+(?:saying|with\s+(?:text|message)|that)|\s*[:]\s*)\s*(.+)$', t, re.IGNORECASE)
        if not m_msg:
            m_msg = re.search(r'^message\s+([a-zA-Z0-9_\+\s]+?)\s+on\s+whatsapp\s*(?:saying|with\s+(?:text|message)|that|\s*[:]\s*)\s*(.+)$', t, re.IGNORECASE)
        if not m_msg:
            m_msg = re.search(r'^tell\s+([a-zA-Z0-9_\+\s]+?)\s+on\s+whatsapp\s+(?:that|saying|\s*[:]\s*)\s*(.+)$', t, re.IGNORECASE)
        if not m_msg:
            m_msg = re.search(r'^send\s+(?:a\s+)?message\s+to\s+([a-zA-Z0-9_\+\s]+?)\s+on\s+whatsapp\s*(?::|saying|\s*with\s+(?:text|message))\s*(.+)$', t, re.IGNORECASE)
        if m_msg:
            target_user = m_msg.group(1).strip()
            msg_text = m_msg.group(2).strip(" '\"")
            return {
                "step": 1,
                "agent": "WhatsAppAgent",
                "description": f"Send WhatsApp message to '{target_user}'",
                "tool": "whatsapp_send_message",
                "args": {"recipient": target_user, "message": msg_text}
            }

        # 5. Send file on WhatsApp
        m_file = re.search(r'^(?:send|attach(?:\s+and\s+send)?)\s+(?:the\s+)?(?:(?:file|document|doc|pdf|photo|image|pic)\s+)?([a-zA-Z0-9_\-\.\/\\]+)\s+to\s+([a-zA-Z0-9_\+\s]+?)\s+on\s+whatsapp$', t, re.IGNORECASE)
        if m_file:
            target_file = m_file.group(1).strip()
            target_user = m_file.group(2).strip()
            return {
                "step": 1,
                "agent": "WhatsAppAgent",
                "description": f"Attach and send '{target_file}' to '{target_user}' on WhatsApp",
                "tool": "whatsapp_send_file",
                "args": {"recipient": target_user, "file_path": target_file}
            }

        # 6. WhatsApp Voice / Video Call
        m_vcall = re.search(r'^(?:video\s+call|start\s+(?:a\s+)?video\s+call\s+with)\s+([a-zA-Z0-9_\+\s]+?)\s+on\s+whatsapp$', t, re.IGNORECASE)
        if m_vcall:
            target_user = m_vcall.group(1).strip()
            return {
                "step": 1,
                "agent": "WhatsAppAgent",
                "description": f"Start video call with '{target_user}' on WhatsApp",
                "tool": "whatsapp_call",
                "args": {"recipient": target_user, "call_type": "video"}
            }

        m_call = re.search(r'^(?:voice\s+call|call|make\s+a\s+call\s+to)\s+([a-zA-Z0-9_\+\s]+?)\s+on\s+whatsapp$', t, re.IGNORECASE)
        if m_call:
            target_user = m_call.group(1).strip()
            return {
                "step": 1,
                "agent": "WhatsAppAgent",
                "description": f"Make voice call to '{target_user}' on WhatsApp",
                "tool": "whatsapp_call",
                "args": {"recipient": target_user, "call_type": "voice"}
            }

        return None

    def _check_compound(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detects compound instructions joined by ' and ' or ' then ' or ' also '.
        If each sub-instruction matches a fast path, builds a multi-step multi-agent plan!
        Checks whether steps target different agents (making them eligible for parallel execution).
        """
        # Split by conjunctions
        parts = re.split(r'\s+(?:and then|and also|and|then|also)\s+', text, flags=re.IGNORECASE)
        if len(parts) < 2 or len(parts) > 5:
            return None

        steps = []
        agents_used = set()
        
        for idx, part in enumerate(parts, 1):
            step = self._match_fast_path_step(part.strip())
            if not step:
                return None  # If any sub-part cannot be fast-routed, let LLM handle it
            step["step"] = idx
            steps.append(step)
            agents_used.add(step.get("agent"))

        # If steps belong to different agents, they can run in PARALLEL!
        # (e.g. MediaAgent + SystemAgent)
        parallel = len(agents_used) == len(steps) and len(steps) > 1

        return {
            "is_conversational": False,
            "direct_response": "",
            "plan": steps,
            "parallel_eligible": parallel
        }

    def _plan_with_llm(self, user_request: str, history: list = None, target_domain: str = None) -> Dict[str, Any]:
        """
        Fast LLM Planner:
        Uses the warm, fast local model (or configured default) with a structured multi-agent decomposition prompt.
        """
        context_str = ""
        if history:
            context_parts = []
            for h in history[-3:]:
                role = "User" if h.get("role") == "user" else "Ultron"
                context_parts.append(f"{role}: {h.get('content', '')}")
            context_str = "Recent History:\n" + "\n".join(context_parts) + "\n\n"

        domain_hint = f"\nTARGET DOMAIN FOCUS: The local decision classifier has classified this request under the '{target_domain.upper()}' domain. Give primary attention to tools from the corresponding agent.\n" if target_domain else ""

        prompt = f"""You are the Multi-Agent Router & Planner for Ultron, an autonomous Windows AI Assistant.{domain_hint}
Decompose the user request into an explicit, sequential step-by-step action plan (1 to 5 concrete steps) assigned to specialized sub-agents.

Specialist Sub-Agents & Tools:
1. MediaAgent: control_volume, control_media, set_timer_reminder
2. WebAgent: open_url, web_search, play_youtube
3. SystemAgent: get_system_configuration, get_top_resource_hogs, kill_process, open_app, manage_windows, check_network_status, take_screenshot, manage_clipboard
4. FileDocAgent: create_folder, organize_folder, read_file, write_file, list_directory, read_document, manage_notes
5. ShellAgent: run_terminal_command, execute_python_code
6. InputAgent: keyboard_type, keyboard_press, keyboard_hotkey, mouse_click, mouse_move, mouse_scroll, mouse_drag, get_cursor_position
7. WhatsAppAgent: whatsapp_status_check, whatsapp_open_app, whatsapp_open_chat, whatsapp_send_message, whatsapp_send_file, whatsapp_call

{TOOL_SCHEMAS_DESCRIPTION}

CRITICAL MULTI-STEP RULES:
1. Summarizing & Writing Files in Folders:
   - When the user asks to create a folder AND create a file in it AND write a summary of a directory or file:
     * Step 1: Create the target folder with 'create_folder' by FileDocAgent (args: {{"folder_path": "<folder_name>"}})
     * Step 2: Inspect the current directory contents with 'list_directory' by FileDocAgent (args: {{"dir_path": "."}})
     * Step 3: Write the summary into the file inside that folder with 'write_file' by FileDocAgent (args: {{"file_path": "<folder_name>/<file_name>", "content": "Summary of directory contents...", "mode": "overwrite"}})
2. File Paths & Valid Tools:
   - Always prefix file paths inside created folders with the folder name (e.g. 'NEW_Project/prject_summary.txt').
   - Use 'list_directory' (NOT 'read_directory') to view directory contents.
3. Multi-Step Dependencies:
   - When steps depend on earlier steps (e.g. creating a folder, listing, and writing a file), they MUST execute sequentially. Set "parallel_eligible": false.
   - Set "parallel_eligible": true ONLY if all steps are completely independent actions across different sub-agents (e.g. take a screenshot and set volume).
4. WhatsApp Desktop Operations:
   - For WhatsApp messaging, opening chat, calls, or file sending, assign to WhatsAppAgent.
   - Set "parallel_eligible": false for sequential WhatsApp workflows.

OUTPUT STRICT JSON SCHEMA:
{{
  "is_conversational": false,
  "direct_response": "",
  "parallel_eligible": false,
  "plan": [
    {{
      "step": 1,
      "agent": "AgentName",
      "description": "Short explanation",
      "tool": "tool_name",
      "args": {{"key": "value"}}
    }}
  ]
}}
If the user asks a purely conversational question needing NO system action, set "is_conversational": true and provide "direct_response".
"""
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"{context_str}User Request: {user_request}"}
        ]

        try:
            response = ollama.chat(
                model=self.active_model,
                messages=messages,
                format="json"
            )
            content = response['message']['content']
            data = self._extract_json(content)
            if data and isinstance(data, dict):
                return data
        except Exception:
            pass

        # Safe fallback
        return {
            "is_conversational": False,
            "direct_response": "",
            "parallel_eligible": False,
            "plan": [
                {
                    "step": 1,
                    "agent": "ShellAgent",
                    "description": "Execute request via terminal command",
                    "tool": "run_terminal_command",
                    "args": {"command": user_request}
                }
            ]
        }

    def _extract_json(self, raw_text: str) -> Optional[dict]:
        if not raw_text:
            return None
        text = raw_text.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except Exception:
                    pass
        return None
