"""
Ultron Multi-Agent OS Controller Package
Exports Specialist Agents and UltronSupervisor.
"""

from agents.base_agent import BaseAgent, AgentResult
from agents.media_agent import MediaAgent
from agents.web_agent import WebAgent
from agents.system_agent import SystemAgent
from agents.file_agent import FileDocAgent
from agents.shell_agent import ShellAgent
from agents.input_agent import InputAgent
from agents.whatsapp_agent import WhatsAppAgent
from agents.router_agent import FastRouterAgent
from agents.supervisor import UltronSupervisor

__all__ = [
    "BaseAgent",
    "AgentResult",
    "MediaAgent",
    "WebAgent",
    "SystemAgent",
    "FileDocAgent",
    "ShellAgent",
    "InputAgent",
    "WhatsAppAgent",
    "FastRouterAgent",
    "UltronSupervisor"
]
