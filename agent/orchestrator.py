"""State-graph style multi-agent orchestration with dynamic tools and recovery."""
import shutil
from agent.agents import PlannerAgent, ReflectionAgent, QuestionAnswerAgent
from agent.tools import ToolRegistry

class RepositoryAgent:
    def __init__(self, max_tool_retries=1):
        self.tools = ToolRegistry()
        self.planner = PlannerAgent()
        self.reflector = ReflectionAgent()
        self.qa = QuestionAnswerAgent()
        self.max_tool_retries = max_tool_retries
        self.trace, self.report, self.history = [], None, []
        self.state = {"node": "idle", "status": "ready", "context": {}, "errors": []}

    def _log(self, agent, status, message, details=None):
        self.trace.append({"agent": str(agent), "status": str(status), "message": str(message), "details": details or {}})

    def _transition(self, node, **updates):
        self.state.update(updates)
        self.state["node"] = node
        self._log("StateGraph", "info", f"Transitioned to {node}.", {"state_keys": sorted(self.state.keys())})

    def reset(self):
        self.trace, self.report, self.history = [], None, []
        self.state = {"node": "idle", "status": "ready", "context": {}, "errors": []}

    def analyse(self, url):
        self.trace, self.report = [], None
        workspace = None
        self.state = {"node": "planning", "status": "running", "input": url, "context": {}, "errors": [], "retry_count": 0}
        try:
            self._transition("planning")
            plan = self.planner.plan("analyse repository", self.tools.descriptions())
            selected = self.tools.select("analyse repository", [step["tool"] for step in plan])
            self.state["plan"] = plan
            self._log("PlannerAgent", "success", "Decomposed the request into an ordered tool plan.", {"steps": plan, "selected_tools": selected})

            context = {}
            for tool_name in selected:
                self._transition(tool_name)
                self._log("ToolSelector", "success", f"Selected {tool_name} based on the current plan.", {"tool": tool_name})
                try:
                    if tool_name == "clone_repository":
                        result = self.tools.call(tool_name, url, retries=self.max_tool_retries)
                        workspace = result.parent
                        context["root"] = result
                    elif tool_name == "collect_files":
                        result = self.tools.call(tool_name, context["root"], retries=self.max_tool_retries)
                        context["files"] = result
                    elif tool_name == "build_tree":
                        result = self.tools.call(tool_name, context["root"], retries=self.max_tool_retries)
                        context["tree"] = result
                    elif tool_name == "analyse_repository":
                        result = self.tools.call(tool_name, context["root"], context["files"], retries=self.max_tool_retries)
                        context["report"] = result
                        # Reflection-triggered fallback: broaden collection once if the first pass is empty.
                        if result.get("file_count", 0) == 0:
                            self._log("ReflectionAgent", "warning", "Analysis output is incomplete (zero files); trying a broader text-file collection.", {"fallback": "collect_files(include_unknown=True)"})
                            fallback_files = self.tools.call("collect_files", context["root"], include_unknown=True, retries=self.max_tool_retries)
                            if fallback_files:
                                context["files"] = fallback_files
                                context["report"] = self.tools.call("analyse_repository", context["root"], fallback_files, retries=self.max_tool_retries)
                                self._log("ReflectionAgent", "success", "Fallback collection recovered files and analysis was rerun.", {"recovered_file_count": len(fallback_files)})
                            else:
                                self._log("ReflectionAgent", "warning", "Fallback collection found no additional readable files.", {})
                    elif tool_name == "severity_summary":
                        result = self.tools.call(tool_name, context["report"].get("findings", []), retries=self.max_tool_retries)
                        context["report"]["severity_counts"] = result
                    else:
                        raise ValueError(f"No execution adapter for selected tool: {tool_name}")
                    attempts = self.tools.last_attempts
                    self.state["retry_count"] += max(0, attempts - 1)
                    self._log("ToolExecutor", "success", f"Executed {tool_name}.", {"tool": tool_name, "result_type": type(result).__name__, "attempts": attempts, "retries_used": max(0, attempts - 1)})
                except Exception as exc:
                    self.state["errors"].append(f"{tool_name}: {exc}")
                    self._log("ToolExecutor", "error", f"{tool_name} failed; recovery policy exhausted.", {"error": str(exc), "retries": self.max_tool_retries})
                    raise

            report = context["report"]
            report["tree"] = context.get("tree", "")
            report["summary"] = (
                f"Scanned {report['file_count']} supported files in {report['repository']}. "
                f"Detected {len(report['languages'])} language categories and "
                f"{report['python_function_count']} Python functions. "
                f"Found {report.get('total_findings', len(report['findings']))} total code-quality/security findings."
            )
            self._transition("reflection", context={"repository": report.get("repository"), "file_count": report.get("file_count")})
            review = self.reflector.review(report, expected_steps=selected, errors=self.state["errors"])
            self._log("ReflectionAgent", "success" if review["passed"] else "warning", "Validated report completeness and consistency.", {"review": review})
            report["reflection"] = review
            self.report = report
            self.history.append({"role": "system", "content": report["summary"]})
            self.state.update({"node": "complete", "status": "success", "report_ready": True})
            self._log("StateGraph", "success", "Workflow completed.", {"final_state": "complete", "history_items": len(self.history)})
            return {"ok": True, "report": report}
        except Exception as exc:
            self.state.update({"node": "failed", "status": "error", "report_ready": False})
            self._log("ReflectionAgent", "error", "Workflow stopped after fallback/retry handling.", {"error": str(exc), "recovery": "Input and tool errors are surfaced with actionable feedback."})
            return {"ok": False, "error": f"Analysis failed: {exc}"}
        finally:
            if workspace is not None:
                shutil.rmtree(workspace, ignore_errors=True)

    def ask(self, question):
        if not self.report:
            return "Please analyse a GitHub repository first."
        answer = self.qa.answer(question, self.report, self.history)
        self.history.extend([{"role": "user", "content": str(question)}, {"role": "assistant", "content": str(answer)}])
        self._log("QuestionAnswerAgent", "success", "Answered using the current repository report and short-term conversation history.", {"question": str(question), "history_items": len(self.history)})
        return answer
