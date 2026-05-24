"""Smoke tests for meok-agents-md-lint-mcp."""
import sys, os, inspect, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    lint_agents_md,
    check_required_sections,
    check_security_smells,
    check_consistency,
    list_spec_sections,
    generate_passing_template,
)


GOOD_AGENTS = """# AGENTS

This file describes how to operate in this repo.

## Setup
Run `uv sync` to install deps.

## Build
Run `uv sync` to build.

## Test
Run `pytest` to test.

## Conventions
Small commits.

## Security
No secrets in code.
"""

BAD_AGENTS = """# Random Doc
Not really an AGENTS file but it has the word agents.
sk-1234567890abcdefghij1234567890abcd
"""


def test_lint_passes_good_agents():
    r = lint_agents_md(GOOD_AGENTS)
    assert r["pass"] is True
    assert r["score_0_100"] >= 80


def test_lint_fails_missing_required():
    r = lint_agents_md(BAD_AGENTS)
    assert r["pass"] is False
    assert any("missing" in e for e in r["errors"])


def test_lint_detects_security_smell():
    r = lint_agents_md(BAD_AGENTS)
    assert any("SECURITY" in e for e in r["errors"])


def test_check_required_sections_returns_missing():
    r = check_required_sections("# Not it")
    assert r["pass"] is False
    assert len(r["missing"]) >= 3


def test_check_security_smells_detects_secret():
    r = check_security_smells("API key: sk-abcdefghij1234567890abcdef")
    assert r["clean"] is False
    assert len(r["issues"]) >= 1


def test_check_security_smells_clean():
    r = check_security_smells("# AGENTS\n## Setup\nuv sync\n")
    assert r["clean"] is True


def test_check_consistency_flags_undocumented_script():
    pj = {"scripts": {"test": "vitest", "build": "next build", "deploy": "vercel"}}
    r = check_consistency("# AGENTS\nRun npm run dev to start.\n", package_json=pj)
    # "deploy" is not in the standard check loop but "test" and "build" are
    assert any("test" in i or "build" in i for i in r["issues"])


def test_check_consistency_passes():
    pj = {"scripts": {"test": "vitest", "build": "next build"}}
    md = "# AGENTS\n## Test\nnpm run test\n## Build\nnpm run build\n"
    r = check_consistency(md, package_json=pj)
    assert r["consistent"] is True


def test_list_spec_sections_has_required():
    r = list_spec_sections()
    assert "AGENTS" in [s.split()[0] for s in r["required_sections"]] or any("AGENTS" in s for s in r["required_sections"])
    assert "python" in r["supported_project_types"]


def test_generate_template_python():
    r = generate_passing_template("python", "test-proj")
    assert "uv sync" in r["template"]
    audit = lint_agents_md(r["template"])
    assert audit["pass"] is True


def test_generate_template_node():
    r = generate_passing_template("node", "test-proj")
    assert "npm" in r["template"] or "package.json" in r["template"]


def test_generate_template_unknown():
    r = generate_passing_template("cobol-on-rails")
    assert "error" in r


if __name__ == "__main__":
    g = dict(globals())
    fns = [v for k, v in g.items() if k.startswith("test_") and inspect.isfunction(v)]
    p = f = 0
    for fn in fns:
        try:
            fn(); print(f"OK {fn.__name__}"); p += 1
        except Exception as e:
            print(f"X  {fn.__name__}: {type(e).__name__}: {e}"); traceback.print_exc(); f += 1
    print(f"\n{p} passed, {f} failed")
