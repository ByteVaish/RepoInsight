# GitHub Repository Analysis Agent — Final Enhanced Build

A local-first, multi-agent GitHub repository analysis app. The complete core workflow runs **without an LLM API key**. It uses a Python state-graph/agent-loop orchestrator, a task-aware tool registry, bounded retries, report reflection, short-term context, and a Streamlit live demo.

## Rubric coverage

### 1. Agent Workflow & Planning
- `PlannerAgent` decomposes repository analysis into ordered steps.
- `RepositoryAgent` executes the plan through explicit state transitions (`planning → clone → collect → tree → analyse → severity summary → reflection → complete`).
- The execution trace records each transition and tool result.

### 2. Tool Calling & Execution
- `ToolRegistry` registers tools with descriptions and capability tags.
- Planner-selected tools are validated against the live registry before execution.
- Tools execute Python functions for Git cloning, file collection, tree construction, AST/Pyflakes analysis and severity aggregation.
- Tool calls have a bounded retry policy (one retry by default); invalid input is surfaced immediately.

### 3. State Management & Self-Correction
- Workflow state stores current node, input, plan, context, errors, retry policy and completion status.
- Streamlit session state retains the agent, report and conversation between interactions.
- `ReflectionAgent` checks report consistency and completeness and provides recommended actions.
- Tool failures are captured in the trace and surfaced with fallback guidance. Transient tool errors are retried once. If the first scan returns zero files, reflection triggers one broader collection pass and reruns analysis.
- Q&A is grounded in the current report and short-term conversation history.

### 4. Live Working Demo
- Streamlit app includes repository analysis, question answering, execution trace, and Tools & History tabs.
- Suggested live test: `https://github.com/psf/requests` (public repo; internet and Git required).
- Try questions such as “How many Python functions?”, “How many high severity findings?”, “Which files have unused imports?”, and “Show potential security findings.”
- Invalid URL test: enter `https://example.com/not-a-github-repository` and show the validation error.

## Setup (Windows CMD)

Requirements: Python 3.11+ and Git installed and available on PATH.

```cmd
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

## Setup (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

## API key

**No LLM API key is required.** Planning, tool selection, code analysis, reflection, retries and report-grounded Q&A are implemented with local Python logic. This makes the demo reproducible without paid API access. An LLM can be added later as an optional enhancement, but it is not needed for the rubric workflow.

## Safety and limitations
- The app analyses public repositories only; private GitHub repositories are not supported.
- It clones source code but does not execute code from the target repository.
- Security checks are heuristic indicators for manual review, not proof of exploitable vulnerabilities.
- Detailed quality/security checks target Python files; language detection supports several source/config formats.
- Git and internet access are required for cloning a public repository.
- Large repositories are capped at 1,200 supported text files and 500 KB per file.

## Project structure

```text
GitHub_Repository_Analysis_Agent/
├── app.py
├── requirements.txt
├── README.md
└── agent/
    ├── agents.py
    ├── agents_qa.py
    ├── orchestrator.py
    ├── tools.py
    ├── repository.py
    ├── analyzers.py
    └── quality.py
```
