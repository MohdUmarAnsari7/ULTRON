"""
Ultron: High-Speed Multi-Agent OS Controller for Windows
Powered by Ollama with Sub-Millisecond Routing, Parallel Execution & Domain Specialist Sub-Agents.

Agents Architecture:
- UltronSupervisor: Master multi-agent orchestrator & parallel thread dispatcher
- FastRouterAgent: Sub-millisecond pattern classifier & compound planner (<1ms)
- MediaAgent: System volume, mute/unmute, media playback, audio alerts
- WebAgent: Browser URL routing (Chrome/Edge), DuckDuckGo live search, YouTube
- SystemAgent: PC hardware configuration, lag diagnostics, process manager, screenshot
- FileDocAgent: Safe directory creation, organization, file read/write, PDF/Docx
- ShellAgent: PowerShell and Python script execution with safety interceptor
"""

import sys
import ollama
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from config import DEFAULT_MODEL, FAST_MODEL, ROUTER_MODEL, USE_TEV1_ROUTER
from agents import UltronSupervisor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

console = Console()

def check_ollama_environment() -> tuple[str, str]:
    """Validates Ollama connection and selects optimal primary and fast models."""
    try:
        models_response = ollama.list()
        available_models = [m.model for m in models_response.models]
    except Exception as e:
        console.print(Panel(
            f"[bold red]Cannot connect to Ollama service![/bold red]\n\n"
            f"Details: {str(e)}\n\n"
            f"[yellow]Make sure Ollama is running:[/yellow] ollama serve",
            title="⚠️ Ollama Connection Error",
            border_style="red"
        ))
        sys.exit(1)

    if not available_models:
        console.print(Panel(
            "[bold red]No models found in Ollama![/bold red]\n\n"
            "Run: [bold green]ollama pull llama3.1:8b[/bold green]",
            title="📦 Missing Model",
            border_style="red"
        ))
        sys.exit(1)

    # Filter models to ensure chat support (avoids embedding-only models)
    def supports_chat(m_name: str) -> bool:
        try:
            ollama.chat(model=m_name, messages=[{"role": "user", "content": "hi"}])
            return True
        except Exception:
            return False

    chat_models = [m for m in available_models if supports_chat(m)]
    if not chat_models:
        console.print(Panel(
            "[bold red]No chat-capable models found in Ollama![/bold red]\n\n"
            "Run: [bold green]ollama pull llama3.1:8b[/bold green]",
            title="📦 Missing Chat Model",
            border_style="red"
        ))
        sys.exit(1)

    # Determine primary model
    primary = DEFAULT_MODEL if any(DEFAULT_MODEL in m for m in chat_models) else chat_models[0]

    # Determine fast model (prefer fast chat models, else primary)
    fast = primary
    if any(FAST_MODEL in m for m in chat_models):
        fast = FAST_MODEL

    return primary, fast

def main():
    console.clear()
    banner = Text(
        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║                ULTRON MULTI-AGENT OS CONTROLLER                  ║\n"
        "║         High-Speed Autonomous Windows Multi-Agent Swarm          ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n",
        style="bold cyan"
    )
    console.print(banner)

    primary_model, fast_model = check_ollama_environment()
    
    # Initialize Supervisor
    supervisor = UltronSupervisor(primary_model=primary_model, fast_model=fast_model)

    console.print("[bold green]✔ Specialist Agents Online:[/bold green]")
    console.print("  [cyan]•[/cyan] [bold magenta]MediaAgent[/bold magenta]     [dim]- Audio endpoints, volume, playback, alerts[/dim]")
    console.print("  [cyan]•[/cyan] [bold magenta]WebAgent[/bold magenta]       [dim]- Browser navigation (Chrome/Edge), DDG search, YouTube[/dim]")
    console.print("  [cyan]•[/cyan] [bold magenta]SystemAgent[/bold magenta]    [dim]- PC specs, RAM/CPU lag diagnostics, screenshot, windows[/dim]")
    console.print("  [cyan]•[/cyan] [bold magenta]FileDocAgent[/bold magenta]   [dim]- Folder creation, file read/write, PDF/DOCX extractor[/dim]")
    console.print("  [cyan]•[/cyan] [bold magenta]ShellAgent[/bold magenta]     [dim]- PowerShell terminal, Python automation engine[/dim]")
    console.print("  [cyan]•[/cyan] [bold magenta]InputAgent[/bold magenta]     [dim]- Physical keyboard typing, hotkeys, mouse clicks & movement[/dim]")
    console.print("  [cyan]•[/cyan] [bold magenta]WhatsAppAgent[/bold magenta]  [dim]- WhatsApp automation, chat, messaging, media transfer & calling[/dim]")
    console.print("  [cyan]•[/cyan] [bold magenta]FastRouter[/bold magenta]     [dim]- Sub-millisecond zero-latency pattern dispatcher[/dim]")
    if USE_TEV1_ROUTER:
        console.print(f"  [cyan]•[/cyan] [bold magenta]tev1 Router[/bold magenta]    [dim]- Two-stage local decision classification ([/dim][bold white]{ROUTER_MODEL}[/bold white][dim])[/dim]")
        # Pre-warm tev1 in background to eliminate cold-start latency
        import subprocess
        try:
            subprocess.Popen(
                ["ollama", "run", "--keepalive", "60m", ROUTER_MODEL, "--ask", "ping", "--choice", "a=1", "--choice", "b=2"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    router_info = f" | Router=[bold white]{ROUTER_MODEL}[/bold white]" if USE_TEV1_ROUTER else ""
    console.print(f"[green]✔ Models Connected:[/green] Primary=[bold white]{primary_model}[/bold white] | Fast=[bold white]{fast_model}[/bold white]{router_info}")
    console.print("[dim]Type your command in natural language, or 'exit' to quit.\n[/dim]")

    history = []

    while True:
        try:
            user_input = console.input("[bold green]You > [/bold green]").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("\n[bold cyan]Ultron:[/bold cyan] Standing down. Systems offline. Goodbye.\n")
                break
            if user_input.lower() in ["clear", "cls"]:
                console.clear()
                continue

            reply = supervisor.execute_request(user_input, history)
            console.print(f"\n[bold cyan]Ultron > [/bold cyan]{reply}\n")

            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": reply})

        except KeyboardInterrupt:
            console.print("\n[yellow]Ultron paused by user interrupt.[/yellow]")
            break
        except Exception as err:
            console.print(f"\n[red]Unexpected error in Ultron pipeline: {err}[/red]\n")

if __name__ == "__main__":
    main()
