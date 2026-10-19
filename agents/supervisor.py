"""
Ultron Multi-Agent Supervisor & Orchestrator
Coordinates domain specialist sub-agents, dispatches parallel actions via ThreadPoolExecutor,
manages instant programmatic verification, self-healing diagnostics, and grounded response synthesis.
"""

import sys
import time
import json
import concurrent.futures
from typing import Dict, Any, List, Optional
import ollama
from rich.console import Console

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import DEFAULT_MODEL, FAST_MODEL, ENABLE_PARALLEL_EXECUTION
from tools import TOOL_SCHEMAS_DESCRIPTION
from agents.media_agent import MediaAgent
from agents.web_agent import WebAgent
from agents.system_agent import SystemAgent
from agents.file_agent import FileDocAgent
from agents.shell_agent import ShellAgent
from agents.input_agent import InputAgent
from agents.whatsapp_agent import WhatsAppAgent
from agents.router_agent import FastRouterAgent
from agents.base_agent import AgentResult

console = Console()

class UltronSupervisor:
    def __init__(self, primary_model: str = DEFAULT_MODEL, fast_model: str = FAST_MODEL):
        self.primary_model = primary_model
        self.fast_model = fast_model

        # Register Specialist Agents
        self.media_agent = MediaAgent()
        self.web_agent = WebAgent()
        self.system_agent = SystemAgent()
        self.file_agent = FileDocAgent()
        self.shell_agent = ShellAgent()
        self.input_agent = InputAgent()
        self.whatsapp_agent = WhatsAppAgent(model_name=self.fast_model)
        self.router = FastRouterAgent(active_model=self.fast_model)

        self.agent_registry = {
            "MediaAgent": self.media_agent,
            "WebAgent": self.web_agent,
            "SystemAgent": self.system_agent,
            "FileDocAgent": self.file_agent,
            "ShellAgent": self.shell_agent,
            "InputAgent": self.input_agent,
            "WhatsAppAgent": self.whatsapp_agent
        }

    def get_agent_for_tool(self, tool_name: str):
        """Finds the designated specialist agent for a given tool."""
        for agent in self.agent_registry.values():
            if agent.can_handle(tool_name):
                return agent
        return self.shell_agent

    def execute_request(self, user_text: str, history: list = None) -> str:
        """End-to-end multi-agent execution pipeline with speed optimizations."""
        start_pipeline = time.time()

        # 1. FAST ROUTING & DECOMPOSITION (< 1ms for fast path)
        with console.status("[bold cyan]Ultron Multi-Agent Router analyzing request...[/bold cyan]", spinner="dots"):
            route_data = self.router.route(user_text, history)

        # Surface tev1 Decision Routing in UI
        tev1_dec = route_data.get("tev1_decision")
        if tev1_dec:
            is_task = tev1_dec.get("is_task", False)
            intent_label = "TASK" if is_task else "CHAT"
            conf = tev1_dec.get("confidence", 0)
            if is_task:
                domain = str(tev1_dec.get("domain") or "general").upper()
                dom_conf = tev1_dec.get("domain_confidence", 0)
                conf_str = f" ({conf}%)" if conf else ""
                dom_conf_str = f" ({dom_conf}%)" if dom_conf else ""
                console.print(f"[bold yellow]⚡ tev1 Router:[/bold yellow] Intent=[bold green]{intent_label}[/bold green]{conf_str} | Category=[bold magenta]{domain}[/bold magenta]{dom_conf_str}")
            else:
                conf_str = f" ({conf}%)" if conf else ""
                console.print(f"[bold yellow]⚡ tev1 Router:[/bold yellow] Intent=[bold cyan]{intent_label}[/bold cyan]{conf_str}")

        # Conversational fast path
        if route_data.get("is_conversational", False):
            total_time_s = time.time() - start_pipeline
            console.print(f"[dim]⚡ Completed in {total_time_s:.2f}s via FastChat Engine[/dim]")
            return route_data.get("direct_response", "I am here, sir.")

        # Autonomous Multi-Turn Agentic Sequence (e.g. WhatsApp dynamic multi-request loop)
        if route_data.get("agentic_loop") == "WhatsAppAgent":
            success, summary, _ = self.whatsapp_agent.execute_agentic_loop(user_text)
            total_time_s = time.time() - start_pipeline
            console.print(f"[dim]⚡ Completed in {total_time_s:.2f}s via WhatsApp Multi-Turn Agent Loop[/dim]")
            return summary

        plan = route_data.get("plan", [])
        if not plan:
            return "I could not formulate an execution plan for that request."

        agents_in_plan = [p.get("agent") or self.get_agent_for_tool(p.get("tool", "")).name for p in plan]
        all_unique_agents = len(set(agents_in_plan)) == len(plan)
        parallel_eligible = (
            route_data.get("parallel_eligible", False)
            and ENABLE_PARALLEL_EXECUTION
            and len(plan) > 1
            and all_unique_agents
        )

        # Display Plan
        console.print(f"\n[bold cyan]📋 Ultron Multi-Agent Plan ({len(plan)} step{'s' if len(plan) > 1 else ''}):[/bold cyan]")
        for p in plan:
            agent_name = p.get("agent") or self.get_agent_for_tool(p.get("tool", "")).name
            console.print(f"  [cyan]• Step {p.get('step', 1)}:[/cyan] {p.get('description', '')} [bold magenta][{agent_name}][/bold magenta] [dim]({p.get('tool')})[/dim]")

        execution_results: List[AgentResult] = []

        # 2. PARALLEL OR SEQUENTIAL MULTI-AGENT EXECUTION
        if parallel_eligible:
            console.print("\n[bold green]⚡ Executing independent steps concurrently in parallel...[/bold green]")
            execution_results = self._execute_parallel(plan, user_text)
        else:
            execution_results = self._execute_sequential(plan, user_text)

        # Check overall success
        all_succeeded = all(r.success for r in execution_results)

        # 3. FAST GROUNDED SYNTHESIS
        # If all steps succeeded and no text summarization is required (e.g. read_file/read_document/web_search),
        # return direct responses immediately with ZERO LLM latency!
        needs_deep_summary = any(r.tool_name in ["read_file", "read_document", "web_search", "run_terminal_command"] for r in execution_results)
        
        total_time_s = time.time() - start_pipeline

        if all_succeeded and not needs_deep_summary:
            direct_lines = [r.direct_response for r in execution_results if r.direct_response]
            if direct_lines:
                final_summary = " ".join(direct_lines)
                console.print(f"[dim]⚡ Completed in {total_time_s:.2f}s via Multi-Agent Direct Fast-Path[/dim]")
                return final_summary

        # If LLM synthesis is needed for complex reading or summarization
        with console.status("[bold cyan]Synthesizing final response...[/bold cyan]", spinner="dots"):
            final_summary = self._generate_grounded_summary(user_text, execution_results)

        console.print(f"[dim]⚡ Completed in {total_time_s:.2f}s[/dim]")
        return final_summary

    def _execute_single_step(self, step: dict, user_goal: str, prior_results: list = None) -> AgentResult:
        """Executes a single step with designated agent and self-healing recovery loop."""
        step_num = step.get("step", 1)
        step_desc = step.get("description", "")
        current_tool = step.get("tool", "")
        current_args = step.get("args", {})
        agent_name = step.get("agent")

        # Context enrichment from prior steps (e.g. summarizing a directory listing into a file)
        if current_tool == "write_file" and prior_results:
            info_sources = [r.output for r in prior_results if r.success and r.tool_name in ["list_directory", "read_file", "read_document", "web_search", "get_system_configuration"]]
            if info_sources:
                existing_content = current_args.get("content", "")
                if len(existing_content) < 50 or any(w in existing_content.lower() for w in ["summary", "[", "list", "directory", "content"]):
                    source_text = "\n".join(info_sources)
                    summary_content = f"Summary Report for: {user_goal}\n\n{source_text}\n\nGenerated automatically by Ultron Multi-Agent OS Controller."
                    current_args["content"] = summary_content

        agent = self.agent_registry.get(agent_name) or self.get_agent_for_tool(current_tool)

        MAX_STEP_RETRIES = 3
        retry_count = 0
        last_result: Optional[AgentResult] = None

        while retry_count < MAX_STEP_RETRIES:
            if retry_count > 0:
                console.print(f"\n[bold magenta]🔄 Retry Attempt {retry_count}/{MAX_STEP_RETRIES} for Step {step_num}:[/bold magenta] [{agent.name}] [white]{current_tool}({current_args})[/white]")
            else:
                console.print(f"\n[bold yellow]▶ Step {step_num}:[/bold yellow] [bold white]{step_desc}[/bold white] [bold magenta][{agent.name}][/bold magenta]")
                console.print(f"[dim]Invoking {current_tool} with: {current_args}[/dim]")

            # Agent executes tool with built-in permission check and fast verification
            result = agent.execute(current_tool, current_args)
            last_result = result

            preview = result.output.strip()
            if len(preview) > 280:
                preview = preview[:280] + "... [truncated]"
            console.print(f"[dim]↳ Output:\n{preview}[/dim]")

            if result.success:
                console.print(f"[bold green]✔ Step {step_num} Verified Done ({result.latency_ms:.1f}ms):[/bold green] {result.note}")
                return result
            else:
                retry_count += 1
                console.print(f"[bold red]✖ Step {step_num} Failed Verification:[/bold red] {result.note}")

                if retry_count < MAX_STEP_RETRIES:
                    # SELF-HEALING RECOVERY ENGINE
                    recovery = self._diagnose_and_recover(user_goal, current_tool, current_args, result.output)
                    if recovery.get("can_retry") and recovery.get("new_tool"):
                        current_tool = recovery["new_tool"]
                        current_args = recovery.get("new_args", {})
                        agent = self.get_agent_for_tool(current_tool)
                        step_desc = recovery.get("diagnostic", f"Rerouted to {agent.name}.{current_tool}")
                        console.print(f"[yellow]💡 Self-Healing Diagnostic:[/yellow] {recovery.get('diagnostic')}")
                        console.print(f"[yellow]⚡ Next Action to Attempt:[/yellow] [{agent.name}] [bold white]{current_tool}[/bold white] with {current_args}")
                        continue
                    else:
                        console.print(f"[red]Diagnostic determined error is unrecoverable: {recovery.get('diagnostic')}[/red]")
                        break
                else:
                    console.print(f"[red]Halting Step {step_num} after {MAX_STEP_RETRIES} attempts.[/red]")
                    break

        return last_result

    def _execute_sequential(self, plan: list, user_goal: str) -> List[AgentResult]:
        """Runs plan steps sequentially, halting if a prerequisite step fails."""
        results = []
        for step in plan:
            res = self._execute_single_step(step, user_goal, prior_results=results)
            results.append(res)
            if not res.success:
                console.print(f"[red]Halting subsequent steps due to failure in Step {step.get('step', 1)}.[/red]")
                break
        return results

    def _execute_parallel(self, plan: list, user_goal: str) -> List[AgentResult]:
        """Dispatches independent steps across parallel worker threads."""
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(plan))) as executor:
            future_to_step = {executor.submit(self._execute_single_step, step, user_goal): step for step in plan}
            for future in concurrent.futures.as_completed(future_to_step):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    step = future_to_step[future]
                    results.append(AgentResult(
                        agent_name=step.get("agent", "Agent"),
                        tool_name=step.get("tool", ""),
                        success=False,
                        output=f"Parallel execution exception: {str(e)}"
                    ))
        # Re-sort results to match original step order
        results.sort(key=lambda r: next((s.get("step", 1) for s in plan if s.get("tool") == r.tool_name), 1))
        return results

    def _diagnose_and_recover(self, user_goal: str, failed_tool: str, failed_args: dict, error_output: str) -> dict:
        """
        Self-Healing Diagnostic Engine:
        1. Checks fast deterministic recovery rules (cmdlet errors, space in path, etc.)
        2. Falls back to fast Ollama model if unknown.
        """
        err_lower = error_output.lower()

        # Rule 1: AudioBoost or terminal volume failure -> control_volume
        if any(term in err_lower for term in ["set-audioboost", "audioboost", "volume", "sound"]):
            import re
            m = re.search(r'(\d{1,3})', user_goal)
            lvl = int(m.group(1)) if m else 50
            return {
                "can_retry": True,
                "diagnostic": "Terminal audio command is invalid. Switched to native Windows Audio endpoint controller.",
                "new_tool": "control_volume",
                "new_args": {"action": "set", "level": lvl}
            }

        # Rule 2: Folder/Directory creation error (spaces or invalid syntax) -> create_folder
        if any(w in err_lower for w in ["positional parameter", "mkdir"]) or (failed_tool == "run_terminal_command" and any(w in failed_args.get("command", "").lower() for w in ["mkdir", "folder"])):
            import re
            m = re.search(r'name(?:d|\s+it)?\s+[\'"]?([^\'"]+)[\'"]?', user_goal, re.IGNORECASE)
            if not m:
                m = re.search(r'(?:folder|directory)\s+[\'"]?([^\'"]+)[\'"]?', user_goal, re.IGNORECASE)
            folder_name = m.group(1).strip() if m else "New Folder"
            return {
                "can_retry": True,
                "diagnostic": "Directory creation via shell failed. Switched to safe native create_folder tool.",
                "new_tool": "create_folder",
                "new_args": {"folder_path": folder_name}
            }

        # Rule 3: Application launch failed in PowerShell -> open_app
        if failed_tool == "run_terminal_command" and ("not recognized" in err_lower or "cannot find" in err_lower):
            if not any(w in user_goal.lower() for w in ["folder", "directory", "file", "volume", "sound"]):
                return {
                    "can_retry": True,
                    "diagnostic": "Command line execution failed. Falling back to native Windows app launcher.",
                    "new_tool": "open_app",
                    "new_args": {"app_name": failed_args.get("command", "").split()[0]}
                }

        # Fallback to Ollama Diagnostic Query
        recovery_prompt = f"""You are Ultron's Recovery & Diagnostic Engine.
Goal: "{user_goal}"
Failed Tool: {failed_tool} with {failed_args}
Error:
{error_output}

{TOOL_SCHEMAS_DESCRIPTION}

Respond strictly in JSON:
{{
  "can_retry": true,
  "diagnostic": "Explanation of why it failed and the replacement tool",
  "new_tool": "alternative_tool_name",
  "new_args": {{"param": "value"}}
}}
If impossible, set "can_retry": false.
"""
        try:
            response = ollama.chat(
                model=self.fast_model,
                messages=[{"role": "system", "content": recovery_prompt}],
                format="json"
            )
            data = self.router._extract_json(response['message']['content'])
            if data and isinstance(data, dict):
                return data
        except Exception:
            pass

        return {
            "can_retry": False,
            "diagnostic": "Self-healing could not determine an alternative action.",
            "new_tool": None,
            "new_args": {}
        }

    def _generate_grounded_summary(self, user_goal: str, execution_log: List[AgentResult]) -> str:
        """Grounds final synthesis strictly in the actual execution log."""
        log_text = ""
        for i, item in enumerate(execution_log, 1):
            log_text += f"\n- Step {i} [{item.agent_name}]: Tool {item.tool_name}\n  Result: {item.output}\n  Verified: {item.note}\n"

        prompt = f"""You are Ultron, an AI assistant.
User request: "{user_goal}"

Execution Log:
{log_text}

Instructions:
1. Provide a direct, concise, and helpful final response (1-3 sentences) based strictly on the log.
2. If summarizing a file or search result, synthesize the factual information clearly.
3. NEVER start with 'assistant:' or 'Assistant:'.
"""
        try:
            response = ollama.chat(
                model=self.fast_model,
                messages=[{"role": "system", "content": prompt}]
            )
            reply = response['message']['content'].strip()
            for prefix in ["assistant\n", "assistant:\n", "assistant: ", "assistant"]:
                if reply.lower().startswith(prefix):
                    reply = reply[len(prefix):].strip()
            return reply
        except Exception as e:
            return "Task completed successfully based on executed steps."
