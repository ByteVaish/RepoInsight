"""Lightweight local agents: no hosted LLM/API key required."""

class PlannerAgent:
    name = "PlannerAgent"

    def plan(self, task, available_tools):
        """Decompose a request and select tools from their declared capabilities."""
        task = (task or "").lower()
        selected = []
        # Repository analysis uses a dependency-aware pipeline.
        if any(word in task for word in ("tree", "structure", "folders", "files")) and not any(word in task for word in ("analyse", "analyze", "scan")):
            wanted = ["clone_repository", "collect_files", "build_tree"]
        elif any(word in task for word in ("analyse", "analyze", "repository", "repo", "github", "scan")):
            wanted = ["clone_repository", "collect_files", "build_tree", "analyse_repository", "severity_summary"]
        else:
            wanted = ["clone_repository", "collect_files", "analyse_repository", "severity_summary"]
        for name in wanted:
            if name in available_tools:
                selected.append({"tool": name, "purpose": available_tools[name]["description"]})
        return selected


class ReflectionAgent:
    """Checks output completeness and recommends bounded recovery actions."""
    def review(self, report, expected_steps=None, errors=None):
        issues, actions = [], []
        errors = errors or []
        if report.get("file_count", 0) == 0:
            issues.append("No supported text files were found.")
            actions.append("Check repository contents and supported file extensions.")
        if not report.get("languages"):
            issues.append("Language detection returned no results.")
        findings = report.get("findings", [])
        if report.get("total_findings", len(findings)) < len(findings):
            issues.append("Displayed finding count exceeds reported total; verify report aggregation.")
        expected_steps = expected_steps or []
        if expected_steps and not report.get("repository"):
            issues.append("Repository identity is missing from the analysis output.")
        for error in errors:
            issues.append(f"Tool error: {error}")
        return {
            "passed": not issues,
            "issues": issues,
            "recommended_actions": actions,
            "findings_checked": len(findings),
            "retries_used": 0,
        }


class QuestionAnswerAgent:
    def answer(self, question, report, history):
        # The existing report-grounded Q&A is intentionally retained.
        from agent.agents_qa import answer_report_question
        return answer_report_question(question, report, history)
