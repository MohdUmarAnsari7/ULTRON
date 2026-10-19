"""
Ultron Dynamic Safety Interceptor
Evaluates terminal commands and python scripts before execution.
"""

from rich.console import Console
from rich.panel import Panel
from config import DANGEROUS_COMMAND_PATTERNS

console = Console()

def verify_permission(tool_name: str, arguments: dict) -> bool:
    """
    Evaluates whether the command contains high-risk patterns.
    Safe actions run seamlessly. Destructive actions trigger the security gate.
    """
    command_text = ""
    if tool_name == "run_terminal_command":
        command_text = arguments.get("command", "")
    elif tool_name == "execute_python_code":
        command_text = arguments.get("code", "")
    else:
        return True  # Read-only helper

    # Check for dangerous patterns
    lower_cmd = command_text.lower()
    is_dangerous = any(pat in lower_cmd for pat in DANGEROUS_COMMAND_PATTERNS)
    
    if not is_dangerous:
        return True  # Auto-approve non-destructive commands

    # Display confirmation prompt for high-risk commands
    warning_panel = Panel(
        f"[bold red]POTENTIALLY DESTRUCTIVE ACTION DETECTED[/bold red]\n\n"
        f"Tool: [yellow]{tool_name}[/yellow]\n"
        f"Code/Command:\n[bold white]{command_text}[/bold white]\n\n"
        f"[dim]This operation matches a sensitive system modification rule.[/dim]",
        title="🔒 ULTRON SECURITY GATE",
        border_style="red"
    )
    console.print(warning_panel)
    
    try:
        choice = console.input("[bold yellow]Authorize execution? [y/N]: [/bold yellow]").strip().lower()
        if choice in ['y', 'yes']:
            console.print("[green]✔ Authorization granted by user.[/green]\n")
            return True
        else:
            console.print("[red]✖ Action denied by user.[/red]\n")
            return False
    except KeyboardInterrupt:
        console.print("\n[red]Action cancelled.[/red]")
        return False
