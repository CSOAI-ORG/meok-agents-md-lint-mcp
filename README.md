# MEOK AGENTS.md Linter MCP

> ## 🧱 Part of the MEOK Governance + A2A Substrate
> See [meok.ai/docs](https://meok.ai/docs) and [meok.ai/a2a](https://meok.ai/a2a).

# Lint your AGENTS.md against the cross-vendor coding-agent spec

<!-- mcp-name: io.github.CSOAI-ORG/meok-agents-md-lint-mcp -->

[![PyPI](https://img.shields.io/pypi/v/meok-agents-md-lint-mcp)](https://pypi.org/project/meok-agents-md-lint-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What this does

[AGENTS.md](https://agents.md) is the cross-vendor specification that tells coding agents (Cursor, Claude Code, Cline, Windsurf, Aider, OpenAI Codex) how to operate in your repo. Stewarded by the Agentic AI Foundation under the Linux Foundation.

This MCP lints any `AGENTS.md` against the spec — required sections, recommended sections, security smells (no secrets in agent instructions), anti-patterns (no `rm -rf`, no `sudo`, no `--force-push`), and consistency with `package.json` / `pyproject.toml` / `Makefile`.

## Tools

| Tool | Purpose |
|---|---|
| `lint_agents_md(content)` | Full lint with score 0-100 |
| `check_required_sections(content)` | Fast required-section gate |
| `check_security_smells(content)` | Secrets + dangerous instruction patterns |
| `check_consistency(content, package_json?, pyproject_toml_text?, makefile_text?)` | Cross-file lint |
| `list_spec_sections()` | Canonical AGENTS.md section taxonomy |
| `generate_passing_template(project_type)` | Minimal-passing AGENTS.md (python/node/next/rust/go/mcp) |

## Why this exists

Every Cursor / Claude Code / Cline / Windsurf user **has** an AGENTS.md (or should). Few do it well. Common failure modes:

- Missing required sections (Build / Test)
- Hardcoded API keys in agent instructions (`sk-...`, AWS keys, bearer tokens)
- Dangerous shell patterns in instructions (`curl ... | bash`, `rm -rf`)
- `package.json` defines `npm run test` but AGENTS.md tells the agent something different
- "Ignore safety" / "override warnings" patterns smuggled in

This MCP catches all of them in under a second + emits a numeric score you can tweet.

## Sister MCPs

- `mcp-spec-compliance-mcp` — lint your MCP `server.json`
- `agent-prompt-injection-firewall-mcp` — OWASP LLM01 scan
- `bft-progress-council-mcp` — anti-loop guardrail for agents that use your AGENTS.md

Full catalogue: [meok.ai/anthropic-registry](https://meok.ai/anthropic-registry)

## Pricing

| Option | Price |
|---|---|
| Self-host MIT | £0 |
| Universal PAYG | £29/mo + £0.0002/call |
| Governance Substrate | £499/mo |
| A2A Substrate | £999/mo |

## Wire it up — full stack

Pair with `mcp-spec-compliance-mcp` to lint both your `AGENTS.md` AND your `server.json` in one CI check.

See [meok.ai/mcp-stack](https://meok.ai/mcp-stack).

## Licence

MIT. By [MEOK AI Labs](https://meok.ai) (CSOAI LTD, UK Companies House 16939677).
