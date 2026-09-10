"""Rendering a `FunProfile`: terminal scorecard, JSON, markdown.

The terminal form is the one an author reads while iterating, so it leads with
the verdicts and the findings that caused them, and keeps the raw numbers
underneath rather than in front.
"""

import json
from typing import Any, List, Sequence

from .metrics import FAIL, PASS, SKIP, WARN
from .profile import FunProfile

_MARK = {PASS: "PASS", WARN: "WARN", FAIL: "FAIL", SKIP: "n/a "}


def _clip(text: str, width: int) -> str:
    """Keep a column a column. Long metric values are for --json, not here."""
    return text if len(text) <= width else text[: width - 1] + "~"


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3g}"
    if isinstance(value, dict):
        return ", ".join(f"{k}={_fmt(v)}" for k, v in value.items())
    if isinstance(value, list):
        if not value:
            return "-"
        return ", ".join(_fmt(v) for v in value[:6]) + (
            f" (+{len(value) - 6} more)" if len(value) > 6 else ""
        )
    if value is None:
        return "-"
    return str(value)


def render_terminal(profile: FunProfile, verbose: bool = False) -> str:
    lines: List[str] = []
    title = f"Fun profile: {profile.level_id}"
    lines.append("")
    lines.append(title)
    lines.append("=" * len(title))
    lines.append(f"goal      : {profile.goal}")
    lines.append(f"plans     : {profile.plan_count}")

    if profile.truncated:
        lines.append("")
        lines.append("*** PLAN SPACE TRUNCATED ***")
        lines.append(f"    {profile.truncation_reason}")
        lines.append(
            "    Every number below is computed over a partial plan set and is "
            "unreliable."
        )

    lines.append("")
    lines.append("Strategy classes")
    lines.append("-" * 16)
    if profile.strategy_classes:
        for cls in profile.strategy_classes:
            lines.append(f"  {cls['size']:>5}x  {cls['label']}")
            if verbose:
                rep = cls.get("representative", {})
                for op in rep.get("operators", []):
                    lines.append(f"           . {op}")
    else:
        lines.append("  (none)")

    lines.append("")
    for family in profile.families:
        lines.append(f"[{_MARK[family.verdict]}] {family.title}")
        lines.append(f"        encodes: {family.encodes}")
        for key, value in family.metrics.items():
            if key.startswith("_"):
                continue
            if not verbose and key in ("class_sizes", "per_class", "red_herrings",
                                       "insight_depth_per_class", "critical_facts",
                                       "soloable_plan_indices"):
                continue
            lines.append(f"        {key:<26} {_fmt(value)}")
        for finding in family.findings:
            lines.append(f"     -> {finding}")
        lines.append("")

    lines.append("-" * 60)
    if profile.fun_score is None:
        lines.append(f"composite  : withheld ({profile.score_withheld_reason})")
    else:
        lines.append(
            f"composite  : {profile.fun_score:.2f}   "
            f"(least trustworthy output - read the families above)"
        )
    lines.append(f"overall    : {profile.overall.upper()}")

    if profile.notes:
        lines.append("")
        lines.append("Notes")
        for note in profile.notes:
            lines.append(f"  - {note}")
    lines.append("")
    return "\n".join(lines)


def render_json(profile: FunProfile) -> str:
    return json.dumps(profile.to_dict(), indent=2, sort_keys=False)


def render_markdown(profile: FunProfile) -> str:
    lines: List[str] = []
    lines.append(f"# Fun profile: {profile.level_id}")
    lines.append("")
    lines.append(f"- **goal**: `{profile.goal}`")
    lines.append(f"- **plans**: {profile.plan_count}")
    lines.append(f"- **overall**: **{profile.overall.upper()}**")
    if profile.fun_score is None:
        lines.append(f"- **composite**: withheld - {profile.score_withheld_reason}")
    else:
        lines.append(
            f"- **composite**: {profile.fun_score:.2f} "
            f"(least trustworthy output; read the families)"
        )
    if profile.truncated:
        lines.append("")
        lines.append(
            f"> **Plan space truncated.** {profile.truncation_reason} "
            f"Numbers below are unreliable."
        )

    lines.append("")
    lines.append("## Strategy classes")
    lines.append("")
    lines.append("| plans | class |")
    lines.append("|------:|-------|")
    for cls in profile.strategy_classes:
        lines.append(f"| {cls['size']} | {cls['label']} |")

    lines.append("")
    lines.append("## Families")
    for family in profile.families:
        lines.append("")
        lines.append(f"### {_MARK[family.verdict].strip()} - {family.title}")
        lines.append("")
        lines.append(f"*Encodes: {family.encodes}*")
        lines.append("")
        lines.append("| metric | value |")
        lines.append("|--------|-------|")
        for key, value in family.metrics.items():
            lines.append(f"| `{key}` | {_fmt(value)} |")
        if family.findings:
            lines.append("")
            for finding in family.findings:
                lines.append(f"- {finding}")

    if profile.notes:
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        for note in profile.notes:
            lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def render_comparison(profiles: Sequence[FunProfile]) -> str:
    """A one-row-per-level table for `fun-all`."""
    families = ["f1_multiplicity", "f2_distinctness", "f3_depth",
                "f4_choice", "f5_discovery", "f6_player"]
    headers = ["level", "plans", "classes", "F1", "F2", "F3", "F4", "F5", "F6",
               "score", "overall"]

    rows: List[List[str]] = []
    for profile in profiles:
        by_key = {f.key: f for f in profile.families}
        classes = str(len(profile.strategy_classes))
        score = (
            "trunc" if profile.truncated
            else (f"{profile.fun_score:.2f}" if profile.fun_score is not None else "-")
        )
        rows.append(
            [profile.level_id, str(profile.plan_count), classes]
            + [_MARK.get(by_key[k].verdict, "?").strip() if k in by_key else "-"
               for k in families]
            + [score, profile.overall.upper()]
        )

    widths = [
        max(len(headers[i]), max((len(r[i]) for r in rows), default=0))
        for i in range(len(headers))
    ]
    out = [
        "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)),
        "  ".join("-" * widths[i] for i in range(len(headers))),
    ]
    for row in rows:
        out.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(out)


def render_diff(a: FunProfile, b: FunProfile) -> str:
    """Side-by-side family comparison of two levels."""
    lines = [
        "",
        f"{a.level_id}  vs  {b.level_id}",
        "=" * (len(a.level_id) + len(b.level_id) + 8),
        "",
    ]
    by_a = {f.key: f for f in a.families}
    by_b = {f.key: f for f in b.families}

    col = 34

    def row(label: str, left: Any, right: Any, indent: str = "") -> str:
        left_text = _clip(_fmt(left), col - 2)
        return (
            f"{indent}{label:<{col - len(indent)}}"
            f"{left_text:<{col}}{_clip(_fmt(right), col - 2)}"
        )

    lines.append(row("", a.level_id, b.level_id))
    lines.append(row("plans", a.plan_count, b.plan_count))
    lines.append(
        row("strategy classes", len(a.strategy_classes), len(b.strategy_classes))
    )
    lines.append("")

    # Fixed family order so two runs of `fun-compare` are diffable.
    ordered = [f.key for f in a.families] + [
        f.key for f in b.families if f.key not in {g.key for g in a.families}
    ]
    for key in ordered:
        fam_a, fam_b = by_a.get(key), by_b.get(key)
        source = fam_a or fam_b
        if source is None:
            continue
        lines.append(source.title)
        lines.append(
            row("verdict",
                fam_a.verdict if fam_a else "-",
                fam_b.verdict if fam_b else "-",
                indent="  ")
        )
        for metric_key in (fam_a.metrics if fam_a else {}):
            if metric_key.startswith("_"):
                continue
            left = fam_a.metrics.get(metric_key) if fam_a else None
            right = fam_b.metrics.get(metric_key) if fam_b else None
            if _fmt(left) == _fmt(right):
                continue
            lines.append(row(metric_key, left, right, indent="  "))
        lines.append("")

    score_a = f"{a.fun_score:.2f}" if a.fun_score is not None else "withheld"
    score_b = f"{b.fun_score:.2f}" if b.fun_score is not None else "withheld"
    lines.append(f"{'composite':<34}{score_a:<22}{score_b}")
    lines.append("")
    return "\n".join(lines)
