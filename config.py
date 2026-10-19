"""
Configuration settings for Ultron Multi-Agent OS Controller
"""

# Models
DEFAULT_MODEL = "llama3.1:8b"
FAST_MODEL = "llama3.1:8b"
ROUTER_MODEL = "tev1:4b"  # Specialized Ollama Decision / Classification Model
USE_TEV1_ROUTER = True
MODEL_NAME = DEFAULT_MODEL  # Backward compatibility

# Performance & Execution Settings
ENABLE_PARALLEL_EXECUTION = True
ENABLE_FAST_PATH = True
MAX_STEP_RETRIES = 3

# High-risk keywords that trigger the user permission gate
DANGEROUS_COMMAND_PATTERNS = [
    "format",
    "del /f /s /q",
    "remove-item -recurse -force",
    "rmdir /s /q",
    "stop-process -force",
    "shutdown",
    "restart-computer",
    "reg delete",
    "os.remove",
    "shutil.rmtree"
]

SYSTEM_PROMPT = """You are Ultron, an intelligent, autonomous Windows OS Multi-Agent Controller.
Your capabilities span Audio, Web, Documents, Hardware Specs, Process Management, and PowerShell.
"""
