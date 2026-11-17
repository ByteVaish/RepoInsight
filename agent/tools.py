"""Capability registry with task-aware tool selection and bounded retries."""
from agent.repository import clone_repository, collect_files, make_tree
from agent.analyzers import analyse_repository
from agent.quality import severity_counts

class ToolRegistry:
    def __init__(self):
        self.last_attempts = 0
        self.tools = {
            "clone_repository": {"function": clone_repository, "description": "Clone and validate a public GitHub repository.", "tags": {"repository", "network", "setup"}},
            "collect_files": {"function": collect_files, "description": "Collect supported source and configuration files.", "tags": {"files", "repository"}},
            "build_tree": {"function": make_tree, "description": "Build a readable repository directory tree.", "tags": {"tree", "structure"}},
            "analyse_repository": {"function": analyse_repository, "description": "Inspect languages, dependencies, Python quality and security indicators.", "tags": {"analysis", "security", "quality"}},
            "severity_summary": {"function": severity_counts, "description": "Summarize findings by severity.", "tags": {"summary", "severity"}},
        }

    def descriptions(self):
        return {name: {"description": item["description"], "tags": sorted(item["tags"])} for name, item in self.tools.items()}

    def select(self, task, preferred=None):
        """Resolve planner-selected tools against the live registry (no hard-coded calls elsewhere)."""
        requested = list(preferred or [])
        unknown = [name for name in requested if name not in self.tools]
        if unknown:
            raise ValueError(f"Planner selected unavailable tools: {', '.join(unknown)}")
        return requested

    def call(self, name, *args, retries=1, **kwargs):
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        last_error = None
        for attempt in range(retries + 1):
            self.last_attempts = attempt + 1
            try:
                return self.tools[name]["function"](*args, **kwargs)
            except (ValueError, TypeError):
                # Invalid input is deterministic; retrying cannot repair it.
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= retries:
                    break
        raise RuntimeError(f"Tool '{name}' failed after {retries + 1} attempt(s): {last_error}") from last_error
