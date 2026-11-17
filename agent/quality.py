"""Conservative static code-quality and security checks for Python files.

Findings are indicators for human review, not proof of exploitable vulnerabilities.
"""
import ast
import io
import re
from pathlib import Path

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
SECRET_PATTERNS = [
    ("Possible hardcoded credential", re.compile(r'''(?i)\b(api[_-]?key|secret|password|passwd|token|access[_-]?key)\b\s*[:=]\s*['\"]([^'\"]{8,})['\"]''')),
]


def _finding(file, line, issue, severity, category, suggested_fix, item=""):
    return {
        "file": str(file), "line": int(line or 0), "item": str(item),
        "issue": str(issue), "severity": severity, "category": category,
        "suggested_fix": str(suggested_fix),
    }


class _PyflakesReporter:
    def __init__(self, filename):
        self.filename = filename
        self.findings = []

    def unexpectedError(self, filename, message):
        self.findings.append(_finding(self.filename, 0, f"Pyflakes could not analyse file: {message}", "Medium", "Analysis", "Check the file encoding and Python syntax."))

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.findings.append(_finding(self.filename, lineno, f"Syntax error: {msg}", "High", "Syntax", "Correct the syntax at this line before running the module."))

    def flake(self, message):
        description = str(message)
        lowered = description.lower()
        if "undefined name" in lowered:
            severity, category, fix = "High", "Correctness", "Define the name, correct its spelling, or import it from the intended module."
        elif "imported but unused" in lowered or "assigned to but never used" in lowered:
            severity, category, fix = "Low", "Code quality", "Remove the unused import/assignment or use it if it is required."
        else:
            severity, category, fix = "Medium", "Code quality", "Review the Pyflakes message and correct the reported issue."
        self.findings.append(_finding(self.filename, getattr(message, "lineno", 0), description, severity, category, fix))


def analyse_python_file(path: Path, relative_path: str, source: str):
    findings = []
    try:
        tree = ast.parse(source, filename=relative_path)
    except SyntaxError as exc:
        return [_finding(relative_path, exc.lineno, f"Syntax error: {exc.msg}", "High", "Syntax", "Fix the syntax error and rerun the analysis.")]

    # Pyflakes: undefined names, unused imports and related static diagnostics.
    try:
        from pyflakes.api import check
        reporter = _PyflakesReporter(relative_path)
        check(source, relative_path, reporter)
        findings.extend(reporter.findings)
    except ImportError:
        findings.append(_finding(relative_path, 0, "Pyflakes is not installed; name analysis was skipped.", "Low", "Tooling", "Install dependencies with: python -m pip install -r requirements.txt"))
    except Exception as exc:
        findings.append(_finding(relative_path, 0, f"Pyflakes analysis error: {type(exc).__name__}", "Low", "Tooling", "Check the Pyflakes installation and rerun."))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(node) is None:
            findings.append(_finding(relative_path, node.lineno, f"Missing docstring in function '{node.name}'.", "Low", "Documentation", "Add a concise docstring describing purpose, arguments and return value.", node.name))
        elif isinstance(node, ast.ClassDef) and ast.get_docstring(node) is None:
            findings.append(_finding(relative_path, node.lineno, f"Missing docstring in class '{node.name}'.", "Low", "Documentation", "Add a class docstring describing its responsibility.", node.name))
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            if name == "eval":
                findings.append(_finding(relative_path, node.lineno, "Use of eval() can execute attacker-controlled expressions.", "High", "Security", "Avoid eval(); use a safe parser or an explicit allowlist."))
            elif name == "exec":
                findings.append(_finding(relative_path, node.lineno, "Use of exec() dynamically executes code.", "High", "Security", "Avoid exec(); replace it with explicit functions or a constrained interpreter."))
            elif name == "loads" and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "pickle":
                findings.append(_finding(relative_path, node.lineno, "pickle.loads() may execute code when loading untrusted data.", "Critical", "Security", "Never unpickle untrusted input; prefer JSON or another non-executable format."))
            elif name == "run" and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                if any(k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords):
                    findings.append(_finding(relative_path, node.lineno, "subprocess.run(..., shell=True) can enable command injection if input is untrusted.", "High", "Security", "Prefer an argument list with shell=False; validate any externally supplied arguments."))

    for lineno, line in enumerate(source.splitlines(), 1):
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match and match.group(2).lower() not in {"changeme", "your_api_key", "example", "xxxxxxxx"}:
                findings.append(_finding(relative_path, lineno, f"{label} in source code (possible secret; verify manually).", "High", "Security", "Move credentials to environment variables or a secrets manager, then rotate exposed credentials."))
    return findings


def severity_counts(findings):
    return {level: sum(1 for item in findings if item.get("severity") == level)
            for level in ("Critical", "High", "Medium", "Low")}
