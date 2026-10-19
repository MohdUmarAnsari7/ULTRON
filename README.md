# Ultron: High-Speed Multi-Agent Autonomous Windows OS Controller

Ultron is a high-performance, autonomous Windows multi-agent assistant powered by local **Ollama** models:
- **`tev1:4b`**: Ultra-fast Perplexity Decider model for sub-second intent and domain classification with `--keepalive 60m`.
- **`llama3.1:8b`**: Multi-step reasoning, plan decomposition, document summarization, and deep conversational synthesis.

---

## ⚡ Multi-Agent Swarm & Input Actuators

Ultron divides system automation and physical desktop interactions across dedicated domain specialist sub-agents, coordinated by an intelligent Master Supervisor:

```
                            ┌────────────────────────────────┐
                            │        User Prompt / OS        │
                            └───────────────┬────────────────┘
                                            │
                                            ▼
                            ┌────────────────────────────────┐
                            │     ⚡ tev1:4b Router Agent    │
                            │  Unified Intent & Category     │
                            │  (Chat, Media, Web, Sys, Input)│
                            └───────┬────────────────┬───────┘
                                    │                │
                    Deterministic   │                │ Multi-Action Plan /
                    Fast-Path (<1ms)│                │ Sequential Context
                                    ▼                ▼
                            ┌────────────────────────────────┐
                            │        UltronSupervisor        │
                            │  (Parallel Thread Orchestrator)│
                            └───────┬────────────────┬───────┘
                                    │                │
    ┌───────────────────┬───────────┴────────┬───────────────────┬───────────────────┬───────────────────┐
    ▼                   ▼                    ▼                   ▼                   ▼                   ▼
┌──────────────┐ ┌──────────────┐   ┌────────────────┐   ┌──────────────┐   ┌─────────────────┐ ┌───────────────────┐
│  MediaAgent  │ │   WebAgent   │   │  SystemAgent   │   │ FileDocAgent │   │   InputAgent    │ │   WhatsAppAgent   │
│• Volume/Mute │ │• Browser URL │   │• Hardware Specs│   │• Safe Folders│   │• Keyboard Typing│ │• Contact / Phone  │
│• Media Keys  │ │• Live DDG    │   │• RAM/CPU Hogs  │   │• Multi-Dir   │   │• Shortcuts/Keys │ │• Send Text & Emojis│
│• Timers      │ │• YouTube     │   │• Screenshot    │   │• Read/Write  │   │• Mouse Actuation│ │• Attach Any File  │
└──────────────┘ └──────────────┘   └────────────────┘   └──────────────┘   └─────────────────┘ │• Voice/Video Calls│
                                                                                                └───────────────────┘
```

### Specialist Sub-Agents & Decision Classifiers
1. **`tev1:4b` Decision Router (`FastRouterAgent`)**:
   - Single-pass intent and domain classifier (`chat`, `media`, `web`, `system`, `input`, `file`, `whatsapp`, `shell`) (91–100% confidence).
   - Zero-latency pattern matcher and compound workflow dispatcher (< 1ms).
2. **`WhatsAppAgent` (Dedicated WhatsApp Desktop Autonomous Specialist)**:
   - **Contact & Phone Number Support**: Automatically identifies phone numbers (cleans formats, formats protocol URIs) vs. contact names (desktop UI search & navigation).
   - **Message Dispatch**: Handles multiline text, emojis, and special characters cleanly via instant clipboard paste + Enter (`whatsapp_send_message`).
   - **File Attachments**: Attaches and sends images, PDFs, Word documents, text files, and videos via Windows shell clipboard drop list (`whatsapp_send_file`).
   - **Voice & Video Calling**: Initiates voice calls or video calls directly to contacts (`whatsapp_call`).
   - **Autonomous Request-Response Agent Loop**: Interactively sequences with the Ollama model turn-by-turn until the user's task is confirmed DONE (`execute_agentic_loop`).
3. **`InputAgent` (Keyboard & Mouse Control)**:
   - **Keyboard Typing**: Direct keystrokes or instant clipboard paste for Unicode/multiline text (`keyboard_type`).
   - **Key Presses**: Single key strikes (`enter`, `esc`, `tab`, `space`, `win`, `backspace`, `f1`-`f12`).
   - **Hotkeys & Shortcuts**: Simultaneous combinations (`ctrl+c`, `ctrl+v`, `ctrl+s`, `ctrl+a`, `alt+tab`, `win+d`, `win+r`, `ctrl+shift+esc`).
   - **Mouse Actuation**: Left, right, and double clicks at current or absolute (x, y) coordinates (`mouse_click`), smooth movement (`mouse_move`), wheel scrolling (`mouse_scroll`), click-and-drag (`mouse_drag`), and cursor coordinate inspection (`get_cursor_position`).
4. **`MediaAgent`**:
   - Master volume (`pycaw`), audio mute/unmute, media playback (`play_pause`, `next`, `stop`), and alert countdown timers.
5. **`WebAgent`**:
   - Target browser launcher (Chrome/Edge), DuckDuckGo live search, and YouTube player.
6. **`SystemAgent`**:
   - PC specifications, CPU/RAM resource hogs diagnostics, process killer, window snapping, network check, and thread-safe screenshot capture.
7. **`FileDocAgent`**:
   - Safe directory creation (escapes spaces), Downloads/Desktop category organizer, multi-step directory inspection, file read/prepend/append, and PDF/DOCX extractors.
8. **`ShellAgent`**:
   - Custom PowerShell commands and Python execution with intelligent security interception (`safety.py`).
9. **`UltronSupervisor`**:
   - Master orchestrator managing step-by-step sequential plans, concurrent thread-pool parallelization for independent steps, context enrichment between sequential steps, and self-healing error recovery.

---

## 🚀 Performance Benchmarks

| Task | Legacy Monolithic LLM | Ultron Multi-Agent Fast-Path | Speedup |
|---|---|---|---|
| **Chat / Greeting** | ~75.0s | **Instant via FastChat** | **Immediate** |
| **Keyboard Typing** (*"type hello world"*) | ~35.0s | **0.05s** | **~700x faster** |
| **Hotkey Shortcut** (*"press ctrl+c"*) | ~32.0s | **0.04s** | **~800x faster** |
| **Mouse Click at (500, 300)** | ~34.0s | **0.06s** | **~566x faster** |
| **Mouse Scroll Down** | ~33.0s | **0.05s** | **~660x faster** |
| **Send WhatsApp Message** | ~40.0s | **0.59s** | **~68x faster** |
| **Send File on WhatsApp** | ~45.0s | **1.57s** | **~29x faster** |
| **Set Volume to 80%** | 35.4s | **0.12s** | **~295x faster** |
| **Multi-Step Folder + Summary File** | 138.3s | **15.2s** | **~9x faster** |

---

## 🛠️ Complete Command Capabilities

### 1. Dedicated WhatsApp Autonomous Automation (`WhatsAppAgent`)
- **Check Status**:
  - *"Check WhatsApp status"* / *"Is WhatsApp running?"*
- **Open / Focus App**:
  - *"Open WhatsApp"* / *"Launch WhatsApp"* / *"Bring WhatsApp to front"*
- **Open Specific Chat**:
  - *"Open chat with Alex on WhatsApp"*
  - *"Open Priya's chat on WhatsApp"*
- **Send Text Messages (Contact Name or Phone Number)**:
  - *"Send WhatsApp to Mom saying I will be home soon"*
  - *"Send a WhatsApp message to +919876543210: Hello Ultron"*
  - *"Message Rahul on WhatsApp saying Are we still meeting today?"*
  - *"Tell Dad on WhatsApp that I reached safely"*
  - *"WhatsApp Sarah: Check your email"*
- **Send Files, Documents & Media**:
  - *"Send document.pdf to Alice on WhatsApp"*
  - *"Send photo snapshot.png to John on WhatsApp"*
  - *"Attach project_summary.txt to Boss on WhatsApp"*
- **Voice & Video Calling**:
  - *"Call Dad on WhatsApp"* / *"Voice call Mom on WhatsApp"*
  - *"Video call Priya on WhatsApp"* / *"Start a video call with Rohit on WhatsApp"*
- **Compound Multi-Step Workflows**:
  - *"Open WhatsApp and send message to John saying Hello how are you"*
  - *"Open WhatsApp and send file report.pdf to Sarah"*
- **Autonomous Multi-Turn Ollama Agent Sequence**:
  - *"Operate WhatsApp autonomously to send birthday wishes"* $\rightarrow$ Enters interactive multi-turn loop where Ollama plans, executes, and verifies each turn until `DONE`.

### 2. Keyboard & Mouse Control (`InputAgent`)
- *"Type 'git status' and press enter"*
- *"Type 'Welcome to Ultron' into active window"*
- *"Press enter"* / *"Hit escape"* / *"Press space"*
- *"Press ctrl+c"* / *"Copy that"*
- *"Press ctrl+v"* / *"Paste here"*
- *"Press alt+tab"* / *"Press win+d"* / *"Press ctrl+s"*
- *"Click at 500, 300"* / *"Right click"* / *"Double click"*
- *"Move mouse to 960, 540"*
- *"Scroll down 5"* / *"Scroll up"*
- *"Where is my mouse?"*

### 3. Casual Chat & Intent Routing
- *"Hi how are you?"* $\rightarrow$ `⚡ tev1 Router: Intent=CHAT (100%)`
- *"Tell me a joke"* $\rightarrow$ `⚡ tev1 Router: Intent=CHAT (99%)`
- *"Who are you?"* / *"What can you do?"*

### 4. Multi-Action Step-by-Step Planning
- *"Create a folder in this directory name it as 'NEW_Project' and create a file that folder name it as 'prject_summary.txt' and create a summary about this directory and write it in that file"*
- *"Take a screenshot and set volume to 75%"*

### 5. Audio & Media Controls
- *"Set system volume to 80%"*
- *"Mute volume"* / *"Unmute"*
- *"Volume up"* / *"Volume down"*
- *"Pause music"* / *"Next song"*
- *"Set a timer for 10 minutes"*

### 6. Web & Live Search
- *"Open github on chrome"*
- *"Open instagram"*
- *"Play lofi hip hop on youtube"*
- *"What is the weather in Delhi today?"*

### 7. Filesystem & Document Assistant
- *"Create a folder in this current directory name it New Project"*
- *"Clean up my Downloads folder"*
- *"Read tools.py and tell me the summary"*
- *"Note down call doctor at 5pm"* / *"Show my notes"*

### 8. Diagnostics & System Specs
- *"What is my system configuration"*
- *"Why is my pc lagging?"*
- *"Take a screenshot"*
- *"What wifi am I connected to?"*
- *"Kill notepad"*

---

## 💻 How to Run

```powershell
cd C:\Users\User\Desktop\ultron
python ultron.py
```
