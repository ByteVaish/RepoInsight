import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}
TEXT_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".cpp", ".c", ".h",
                 ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".md", ".txt", ".sql", ".sh"}

def validate_github_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"https", "http"} or parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Please enter a valid public GitHub URL, e.g. https://github.com/psf/requests")
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ValueError("GitHub URL must include both owner and repository name.")
    owner, repo = parts[0], re.sub(r"\.git$", "", parts[1])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise ValueError("The owner or repository name contains unsupported characters.")
    return f"https://github.com/{owner}/{repo}.git"

def clone_repository(url: str) -> Path:
    clean_url = validate_github_url(url)
    repo_name = clean_url.rstrip("/").split("/")[-1].removesuffix(".git")
    # Every run gets a unique directory: retries cannot collide with an old clone.
    parent = Path(tempfile.gettempdir()) / "github_repo_agent"
    parent.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix=f"{repo_name}_", dir=str(parent))) / repo_name
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--", clean_url, str(destination)],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "Git clone failed").strip())
        return destination
    except Exception:
        shutil.rmtree(destination.parent, ignore_errors=True)
        raise

def collect_files(root: Path, max_files: int = 1200, include_unknown: bool = False):
    collected = []
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for name in names:
            path = Path(current) / name
            try:
                supported = path.suffix.lower() in TEXT_SUFFIXES
                fallback_candidate = include_unknown and not path.suffix and path.name not in {"LICENSE", "Dockerfile", "Makefile"}
                if path.is_file() and (supported or fallback_candidate) and path.stat().st_size <= 500_000:
                    collected.append(path)
                    if len(collected) >= max_files:
                        return collected
            except OSError:
                continue
    return collected

def make_tree(root: Path, max_lines: int = 250) -> str:
    lines = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted([d for d in dirs if d not in IGNORED_DIRS])
        relative = Path(current).relative_to(root)
        depth = len(relative.parts)
        if depth > 4:
            dirs[:] = []
            continue
        for dirname in dirs:
            lines.append("  " * depth + "📁 " + str(dirname))
        for filename in sorted(names):
            lines.append("  " * depth + "📄 " + str(filename))
            if len(lines) >= max_lines:
                lines.append("... tree truncated ...")
                return "\n".join(lines)
    return "\n".join(lines) if lines else "(empty repository)"
