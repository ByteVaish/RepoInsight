import ast
import json
from collections import Counter
from pathlib import Path
import tomllib
from agent.quality import analyse_python_file, severity_counts

LANGUAGE_BY_SUFFIX = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".java": "Java", ".go": "Go", ".rs": "Rust", ".cpp": "C++",
    ".c": "C", ".h": "C/C++", ".html": "HTML", ".css": "CSS", ".sql": "SQL",
    ".sh": "Shell", ".json": "JSON", ".md": "Markdown", ".yaml": "YAML", ".yml": "YAML"
}

def _read(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def analyse_repository(root: Path, files):
    languages, findings, dependencies = Counter(), [], []
    function_count = class_count = 0
    for path in files:
        languages[LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "Other")] += 1
        if path.suffix.lower() == ".py":
            source = _read(path)
            try:
                tree = ast.parse(source)
                function_count += sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
                class_count += sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
            except SyntaxError:
                pass  # The quality analyser records the syntax finding.
            findings.extend(analyse_python_file(path, str(path.relative_to(root)), source))
    req = root / "requirements.txt"
    if req.exists():
        for line in _read(req).splitlines():
            line = line.strip()
            if line and not line.startswith(("#", "-")):
                dependencies.append(line)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(_read(pyproject))
            dependencies.extend(map(str, data.get("project", {}).get("dependencies", [])))
        except Exception:
            dependencies.append("Could not parse pyproject.toml")
    package = root / "package.json"
    if package.exists():
        try:
            data = json.loads(_read(package))
            dependencies.extend(map(str, data.get("dependencies", {}).keys()))
            dependencies.extend(map(str, data.get("devDependencies", {}).keys()))
        except Exception:
            dependencies.append("Could not parse package.json")
    findings.sort(key=lambda x: ( {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(x["severity"], 4), x["file"], x["line"]))
    counts = severity_counts(findings)
    return {
        "repository": root.name, "file_count": int(len(files)),
        "languages": dict(languages.most_common()),
        "python_function_count": int(function_count), "python_class_count": int(class_count),
        "python_findings": findings[:1000], "findings": findings[:1000],
        "total_findings": len(findings), "severity_counts": counts,
        "security_findings": [f for f in findings if f["category"] == "Security"],
        "dependencies": sorted(set(map(str, dependencies))),
    }
