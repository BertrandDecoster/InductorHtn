"""indhtn_quality — shared ruleset-quality tooling for InductorHTN levels.

Modules:
    static_model  — parser-backed operator/method templates (no engine)
    session_util  — in-process MCP session helpers shared by all drivers
    plan_replay   — causal-link extraction by replaying a plan over state
    dag           — the ruleset->DAG builder, metrics, renderers, CLI

Run as scripts with the repo's convention:
    PYTHONPATH=mcp-server python -m indhtn_quality.dag <level.htn> --goal "..."
"""

__version__ = "0.1.0"
