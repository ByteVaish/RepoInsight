def answer_report_question(question, report, history):

    q = question.lower().strip()
    findings = report.get("findings", report.get("python_findings", []))
    counts = report.get("severity_counts", {})
    security = report.get("security_findings", [f for f in findings if f.get("category") == "Security"])
    # Exact, state-backed answers take precedence over generic keyword matches.
    if any(x in q for x in ["how many", "count", "total", "number of"]) and any(x in q for x in ["function", "method"]):
        return f"The repository contains **{report.get('python_function_count', 0)} Python functions/methods** (including async functions)."
    if any(x in q for x in ["class count", "how many classes", "number of classes"]):
        return f"The repository contains **{report.get('python_class_count', 0)} Python classes**."
    if "language" in q or "programming" in q:
        return "Detected languages (file counts): " + ", ".join(f"{k}: {v}" for k, v in report.get("languages", {}).items())
    if any(x in q for x in ["critical", "high", "medium", "low"]) and any(x in q for x in ["how many", "count", "number", "finding", "issue"]):
        level = next((x.title() for x in ["critical", "high", "medium", "low"] if x in q), None)
        if level: return f"There are **{counts.get(level, 0)} {level} severity findings**."
    if "security" in q or "vulnerab" in q or "eval" in q or "pickle" in q or "shell=true" in q or "secret" in q:
        if "how many" in q or "count" in q or "number" in q:
            return f"Detected **{len(security)} potential security findings**. These are static-analysis indicators, not confirmed vulnerabilities."
        if not security: return "No potential security patterns were detected by the configured checks. This does not prove the repository is vulnerability-free."
        return "Potential security findings (review manually):\n" + "\n".join(f"- **{x['severity']}** `{x['file']}:{x['line']}` — {x['issue']} Suggested fix: {x['suggested_fix']}" for x in security[:15])
    if "undefined" in q or "unused import" in q or "unused imports" in q:
        term = "undefined name" if "undefined" in q else "imported but unused"
        matches = [f for f in findings if term in f["issue"].lower()]
        if not matches and any("Pyflakes is not installed" in f["issue"] for f in findings):
            return f"I could not verify {term} because Pyflakes is not installed in the current environment. Install the project requirements and rerun the scan."
        if not matches: return f"No findings matching **{term}** were reported by Pyflakes."
        return f"Found **{len(matches)} {term} finding(s)**:\n" + "\n".join(f"- `{x['file']}:{x['line']}` — {x['issue']}" for x in matches[:20])
    if any(x in q for x in ["docstring", "quality", "finding", "issue"]):
        return f"The analysis found **{report.get('total_findings', len(findings))} total findings**: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + ". These include documentation, correctness, syntax and security indicators."
    if any(x in q for x in ["depend", "package", "library"]):
        deps = report.get("dependencies", [])
        return "Dependencies found: " + (", ".join(deps) if deps else "No common dependency manifest was found.")
    if any(x in q for x in ["file", "folder", "structure", "tree"]):
        return "Repository structure:\n" + report.get("tree", "")
    return (report.get("summary", "") + "\n\nYou can ask for exact function/class counts, languages, dependencies, severity totals, undefined names, unused imports or potential security findings.")
