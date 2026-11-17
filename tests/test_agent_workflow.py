import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.agents import PlannerAgent, ReflectionAgent
from agent.orchestrator import RepositoryAgent
from agent.tools import ToolRegistry

class WorkflowTests(unittest.TestCase):
    def test_planner_selects_tools_by_task(self):
        registry = ToolRegistry()
        planner = PlannerAgent()
        tree_plan = planner.plan("show repository tree", registry.descriptions())
        self.assertEqual([x["tool"] for x in tree_plan], ["clone_repository", "collect_files", "build_tree"])
        analysis_plan = planner.plan("analyse github repository", registry.descriptions())
        self.assertIn("severity_summary", [x["tool"] for x in analysis_plan])

    def test_registry_rejects_unknown_tool(self):
        with self.assertRaises(ValueError):
            ToolRegistry().call("not_a_real_tool")

    def test_reflection_flags_empty_report(self):
        result = ReflectionAgent().review({"file_count": 0, "languages": {}, "findings": []})
        self.assertFalse(result["passed"])
        self.assertTrue(result["issues"])

    def test_invalid_url_fails_gracefully_and_updates_state(self):
        agent = RepositoryAgent()
        result = agent.analyse("https://example.com/not-github")
        self.assertFalse(result["ok"])
        self.assertEqual(agent.state["node"], "failed")
        self.assertTrue(any(x["agent"] == "ReflectionAgent" for x in agent.trace))

    def test_end_to_end_state_flow_with_local_fixture(self):
        agent = RepositoryAgent()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace" / "sample"
            root.mkdir(parents=True)
            (root / "main.py").write_text('def hello():\n    return "hello"\n', encoding="utf-8")
            (root / "requirements.txt").write_text("requests>=2\n", encoding="utf-8")
            # Replace only the clone tool with a deterministic local fixture.
            agent.tools.tools["clone_repository"]["function"] = lambda url: root
            result = agent.analyse("https://github.com/example/sample")
            self.assertTrue(result["ok"], result)
            self.assertEqual(agent.state["node"], "complete")
            self.assertEqual(result["report"]["python_function_count"], 1)
            self.assertTrue(result["report"]["reflection"]["passed"])
            self.assertTrue(agent.trace)

    def test_reflection_fallback_recovers_extensionless_text_file(self):
        agent = RepositoryAgent()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace" / "sample"
            root.mkdir(parents=True)
            (root / "README").write_text("A simple repository readme", encoding="utf-8")
            agent.tools.tools["clone_repository"]["function"] = lambda url: root
            result = agent.analyse("https://github.com/example/sample")
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["report"]["file_count"], 1)
            self.assertTrue(any("Fallback collection recovered" in x["message"] for x in agent.trace))

if __name__ == "__main__":
    unittest.main()
