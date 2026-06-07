#!/usr/bin/env python3
"""
Buy Pro: https://www.csoai.org/checkout

MEOK AGENTS.md Linter MCP — cross-vendor coding-agent spec validator
=====================================================================

By MEOK AI Labs · https://meok.ai · MIT
<!-- mcp-name: io.github.CSOAI-ORG/meok-agents-md-lint-mcp -->

WHAT THIS DOES
--------------
AGENTS.md is the cross-vendor specification (Cursor, Claude Code, Cline,
Windsurf, Aider, Continue, OpenAI Codex) for telling coding agents how
to operate in a repo. Stewarded by the Agentic AI Foundation (Linux
Foundation). Spec: https://agents.md

Every repo with a coding-agent integration should have one. Few do it well.
This MCP lints any AGENTS.md against the spec — required sections, recommended
sections, anti-patterns, security smells (secrets in agent instructions),
and consistency with package.json / pyproject.toml / Makefile.

VIRAL WEDGE
-----------
Every Cursor / Claude Code / Cline / Windsurf user has an AGENTS.md and wants
it validated before checking it in. DevRel-friendly: install + run on your repo
+ tweet the score. Companion to mcp-spec-compliance-mcp.

TOOLS
-----
- lint_agents_md(content): full lint with score 0-100
- check_required_sections(content): fast required-section gate
- check_security_smells(content): secrets / unsafe instruction patterns
- check_consistency(content, package_json?, pyproject_toml?): cross-file lint
- list_spec_sections(): canonical AGENTS.md section taxonomy
- generate_passing_template(project_type): minimal-passing AGENTS.md

PRICING
-------
Free MIT self-host · £29/mo Starter · A2A Substrate £999/mo.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from typing import Optional
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("meok-agents-md-lint")
_HMAC_SECRET = os.environ.get("MEOK_HMAC_SECRET", "")


SPEC_VERSION = "AGENTS.md spec v1.1 (2026-04)"

REQUIRED_SECTIONS = [
    ("# AGENTS", r"^#\s+AGENTS"),
    ("Setup", r"(?im)^#{1,3}\s+(setup|installation|getting started)"),
    ("Build", r"(?im)^#{1,3}\s+(build|compile|how to build)"),
    ("Test", r"(?im)^#{1,3}\s+(test|tests|how to test)"),
]

RECOMMENDED_SECTIONS = [
    ("Conventions", r"(?im)^#{1,3}\s+(conventions|code\s+style|style guide)"),
    ("Architecture", r"(?im)^#{1,3}\s+(architecture|design|structure)"),
    ("Security", r"(?im)^#{1,3}\s+(security|secrets|sensitive)"),
    ("Deployment", r"(?im)^#{1,3}\s+(deploy|deployment|release)"),
    ("Troubleshooting", r"(?im)^#{1,3}\s+(troubleshoot|known issues|faq)"),
]

SECURITY_SMELLS = [
    (r"sk-[A-Za-z0-9]{20,}",          "Hardcoded API key (sk-...)"),
    (r"AKIA[0-9A-Z]{16}",              "AWS Access Key ID"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY", "Private key block"),
    (r"(?i)password\s*=\s*['\"][^'\"]+['\"]", "Plain-text password assignment"),
    (r"(?i)bearer\s+[A-Za-z0-9._-]{20,}", "Bearer token in instructions"),
    (r"(?im)^#{1,6}\s+(ignore|disregard|override).*safety", "Instruction to ignore safety"),
    (r"(?im)curl\s+[^\s]+\s*\|\s*(bash|sh)", "Pipe-to-shell pattern in instructions"),
]

ANTI_PATTERNS = [
    (r"(?im)run\s+`?rm\s+-rf", "Destructive command in agent instructions"),
    (r"(?im)disable\s+.*test", "Instruction to disable tests"),
    (r"(?im)skip.*ci", "Instruction to skip CI"),
    (r"(?im)force\s*push", "Instruction to force-push"),
    (r"(?im)\bsudo\b", "Sudo usage in agent instructions"),
]

PROJECT_TYPES = {
    "python":  {"build": "uv sync", "test": "pytest", "deps": "pyproject.toml"},
    "node":    {"build": "npm install", "test": "npm test", "deps": "package.json"},
    "next":    {"build": "npm install && npm run build", "test": "npm test", "deps": "package.json"},
    "rust":    {"build": "cargo build", "test": "cargo test", "deps": "Cargo.toml"},
    "go":      {"build": "go build ./...", "test": "go test ./...", "deps": "go.mod"},
    "mcp":     {"build": "uv sync", "test": "python tests/test_*.py", "deps": "pyproject.toml"},
}


def _sign(payload: dict) -> str:
    if not _HMAC_SECRET:
        return "unsigned-no-key-configured"
    return hmac.new(_HMAC_SECRET.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def lint_agents_md(content: str) -> dict:
    """
    Full lint of an AGENTS.md file.

    Args:
        content: Full text of the AGENTS.md file.

    Returns:
        {pass, score_0_100, errors, warnings, info, spec_version}
    """
    errors, warnings, info = [], [], []

    # Required
    for name, pattern in REQUIRED_SECTIONS:
        if not re.search(pattern, content):
            errors.append(f"missing required section: {name}")

    # Recommended
    for name, pattern in RECOMMENDED_SECTIONS:
        if not re.search(pattern, content):
            warnings.append(f"recommended section absent: {name}")

    # Security smells
    for pattern, desc in SECURITY_SMELLS:
        if re.search(pattern, content):
            errors.append(f"SECURITY: {desc}")

    # Anti-patterns
    for pattern, desc in ANTI_PATTERNS:
        if re.search(pattern, content):
            warnings.append(f"anti-pattern: {desc}")

    # Length sanity
    word_count = len(content.split())
    if word_count < 80:
        warnings.append(f"AGENTS.md is short ({word_count} words). Recommended 200-2000.")
    elif word_count > 5000:
        info.append(f"AGENTS.md is long ({word_count} words). Consider splitting into AGENTS-<topic>.md.")

    # Score
    base = 100
    base -= 12 * len(errors)
    base -= 3 * len(warnings)
    score = max(0, base)

    return {
        "pass": len(errors) == 0,
        "score_0_100": score,
        "spec_version": SPEC_VERSION,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "word_count": word_count,
        "linted_at": _ts(),
        "next_step": "Fix errors before checking in." if errors else "Looks good. Tweet your score!",
    }


@mcp.tool()
def check_required_sections(content: str) -> dict:
    """Fast gate: only check required sections."""
    missing = [name for name, pat in REQUIRED_SECTIONS if not re.search(pat, content)]
    return {"pass": len(missing) == 0, "missing": missing}


@mcp.tool()
def check_security_smells(content: str) -> dict:
    """Scan for secrets, dangerous instructions, and pipe-to-shell patterns."""
    found = []
    for pattern, desc in SECURITY_SMELLS:
        if re.search(pattern, content):
            found.append(desc)
    return {"clean": len(found) == 0, "issues": found, "scanned_at": _ts()}


@mcp.tool()
def check_consistency(
    content: str,
    package_json: Optional[dict] = None,
    pyproject_toml_text: Optional[str] = None,
    makefile_text: Optional[str] = None,
) -> dict:
    """
    Cross-file lint: does AGENTS.md say the same things as the actual build/test files?

    Args:
        content: AGENTS.md content.
        package_json: Parsed package.json dict.
        pyproject_toml_text: Raw pyproject.toml text.
        makefile_text: Raw Makefile text.

    Returns:
        {consistent, issues}
    """
    issues = []
    md_lower = content.lower()

    if package_json:
        scripts = package_json.get("scripts", {})
        for script_name in ("test", "build", "dev", "start", "lint"):
            if script_name in scripts and f"npm run {script_name}" not in md_lower and f"npm {script_name}" not in md_lower:
                issues.append(f"package.json defines `{script_name}` script not mentioned in AGENTS.md")

    if pyproject_toml_text:
        if re.search(r"\[tool\.pytest", pyproject_toml_text) and "pytest" not in md_lower:
            issues.append("pyproject.toml configures pytest but AGENTS.md doesn't mention it")
        if re.search(r"\[tool\.ruff", pyproject_toml_text) and "ruff" not in md_lower:
            issues.append("pyproject.toml configures ruff but AGENTS.md doesn't mention it")

    if makefile_text:
        targets = re.findall(r"^([a-z_-]+):", makefile_text, re.MULTILINE)
        for target in targets[:8]:
            if f"make {target}" not in md_lower and target not in ("clean", "help"):
                issues.append(f"Makefile target `{target}` not in AGENTS.md")

    return {"consistent": len(issues) == 0, "issues": issues}


@mcp.tool()
def list_spec_sections() -> dict:
    """Return the canonical AGENTS.md section taxonomy."""
    return {
        "spec_version": SPEC_VERSION,
        "required_sections": [name for name, _ in REQUIRED_SECTIONS],
        "recommended_sections": [name for name, _ in RECOMMENDED_SECTIONS],
        "supported_project_types": list(PROJECT_TYPES.keys()),
        "spec_url": "https://agents.md",
    }


@mcp.tool()
def generate_passing_template(project_type: str = "python", project_name: str = "my-project") -> dict:
    """
    Generate a minimal-passing AGENTS.md template.

    Args:
        project_type: One of python / node / next / rust / go / mcp.
        project_name: Project name.

    Returns:
        {template, project_type}
    """
    if project_type not in PROJECT_TYPES:
        return {"error": f"Unknown project_type. Use one of {list(PROJECT_TYPES)}"}
    pt = PROJECT_TYPES[project_type]
    template = f"""# AGENTS

This file tells coding agents (Cursor, Claude Code, Cline, Windsurf, Aider, OpenAI Codex) how to operate in this repo.

## Setup

```bash
{pt['build']}
```

Dependencies live in `{pt['deps']}`.

## Build

```bash
{pt['build']}
```

## Test

```bash
{pt['test']}
```

All tests should pass before opening a PR.

## Conventions

- Prefer small, focused commits with imperative messages.
- Run the test suite before pushing.
- Don't disable tests to make the suite pass.

## Security

- No secrets in code. Use environment variables.
- Never `rm -rf`, never `sudo`, never `git push --force`.
- If you discover a vulnerability, file an issue privately at security@<your-org>.

## Architecture

`{project_name}` is a {project_type} project. Key entry points:

- `src/` — source code
- `tests/` — tests

## Troubleshooting

- If the build fails, check `{pt['deps']}` is committed and dependencies are pinned.
- If tests fail, run `{pt['test']}` locally before opening a PR.
"""
    return {
        "template": template,
        "project_type": project_type,
        "next_step": "Save as AGENTS.md at repo root. Customise sections to your project.",
    }


if __name__ == "__main__":
    mcp.run()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/00wfZjcgAeUW4c5cyQ8k90K"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
