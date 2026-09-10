"""Narration: operators, intentions and facts as sentences.

Shared by `play`, the MCP level tools and the scorecard, so a plan reads the
same everywhere. Two rules keep it honest:

  - a known operator gets a hand-written sentence in the actor's voice, and
    the same sentence in the first person when it is a companion stating
    what it is about to do;
  - an unknown operator is narrated from its grounded del/add effects, and
    when even those are missing it is named rather than glossed. "Action
    completed" tells the reader nothing and is never emitted.

Strategy names never appear here: narration is what the player sees, and
the player sees moves, not the planner's labels.
"""

from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .extract import split_args

# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def parse_term(text: str) -> Tuple[str, List[str]]:
    """`"opLure(warden, bearer, exit, corridor)"` -> `("opLure", [...])`."""
    text = text.strip().rstrip(".")
    open_idx = text.find("(")
    if open_idx < 0:
        return text, []
    close_idx = text.rfind(")")
    inner = text[open_idx + 1: close_idx if close_idx > open_idx else len(text)]
    return text[:open_idx].strip(), split_args(inner)


def _cap(name: str) -> str:
    return name[:1].upper() + name[1:] if name else name


def _an(word: str) -> str:
    """`a lightning charge`, `an ignite charge`."""
    return f"an {word}" if word[:1].lower() in "aeiou" else f"a {word}"


def _nice(atom: str) -> str:
    """`companionA` -> `companionA`, `the_burn` -> `the burn`. Atoms are names;
    only underscores are turned into spaces."""
    return atom.replace("_", " ")


# --------------------------------------------------------------------------
# Operator table
#
# Each entry maps an operator name to a pair of templates: third person (for
# the play narrative) and first person (for a companion's stated intention).
# Templates take the operator's arguments by position. A template may be a
# callable when the sentence depends on the arguments.
# --------------------------------------------------------------------------

Template = Callable[[List[str]], str]


def _t(third: str, first: str) -> Tuple[Template, Template]:
    def render(fmt: str) -> Template:
        def go(args: List[str]) -> str:
            padded = list(args) + [""] * 8
            return fmt.format(*[_nice(a) for a in padded])
        return go
    return render(third), render(first)


_TABLE: Dict[str, Tuple[Template, Template]] = {
    # --- core vocabulary (components/core) ---
    "opNavigate": _t("{0} moves from {1} to {2}",
                     "I'll move from {1} to {2}"),
    "opLure": _t("{0} drags {1} from {2} into {3}",
                 "I'll drag {1} from {2} into {3}"),
    "opPush": _t("{0} shoves {1} from {2} into {3}",
                 "I'll shove {1} from {2} into {3}"),
    "opTaunt": _t("{0} dashes through {1}; both end up in {3}",
                  "I'll dash through {1} and pull it into {3}"),
    "opAnchor": _t("{0} plants the shield and holds position",
                   "I'll plant the shield and hold here"),
    "opRelease": _t("{0} lifts the shield and is free to move again",
                    "I'll lift the shield and move again"),
    "opSpendCharge": _t("{0} spends one {1} charge ({2})",
                        "I'll spend one {1} charge"),
    "opCastRegion": _t("{0} casts {1} on {2}: the {3} becomes {4}",
                       "I'll cast {1} on {2} and turn the {3} into {4}"),
    "opCastEntity": _t("{0} casts {1} on {2}: {2} is now {3}",
                       "I'll cast {1} on {2} - it will be {3}"),
    "opStatus": _t("{1} is now {2} ({0}'s doing)",
                   "I'll leave {1} {2}"),
    "opSync": _t("{0} and {1} act together ({2}, {3})",
                 "I'll act together with {1}"),
    # --- gamehack vocabulary (components/gamehack) ---
    "opMoveTo": _t("{0} moves from {1} to {2}",
                   "I'll move from {1} to {2}"),
    "opAggroMoveTo": _t("{0} follows its target from {1} to {2}",
                        "I'll follow from {1} to {2}"),
    "opAggro": _t("{0} draws {1}'s attention",
                  "I'll draw {1}'s attention"),
    "opRemoveAggro": _t("{0} no longer holds {1}'s attention",
                        "I'll let {1}'s attention go"),
    "opApplyTag": _t("{0} is now {1}",
                     "I'll make {0} {1}"),
    "opTagAlreadyOnTarget": _t("{1} is already {0}",
                               "{1} is already {0}"),
    "opTargetAlreadyAggroed": _t("the target is already engaged",
                                 "the target is already engaged"),
    "opSwapSkill": _t("{0} swaps {1} for {2}",
                      "I'll swap {1} for {2}"),
    "opGetSkill": _t("{0} picks up {1}",
                     "I'll pick up {1}"),
    "opSynchronize": _t("{0} and {1} act at the same moment",
                        "I'll act at the same moment as {1}"),
    "opSynchronizeOnPlates": _t("{0} and {1} step on {2} and {3} together",
                                "I'll step on {2} while {1} takes {3}"),
    "opStayInLocation": _t("{0} stays put",
                           "I'll stay put"),
    "opUnlock": _t("{0} is unlocked",
                   "I'll unlock {0}"),
    # --- original component tree (components/primitives|strategies|goals) ---
    "opGetAggro": _t("{0} now targets {1}",
                     "I'll draw {0} onto {1}"),
    "opLoseAggro": _t("{0} loses interest in {1}",
                      "I'll shake {0} off {1}"),
    "opApplyRoomTag": _t("{0} is now {1}",
                         "I'll make {0} {1}"),
    "opRemoveTag": _t("{0} is no longer {1}",
                      "I'll clear {1} from {0}"),
    "opConsumeHazard": _t("the {1} in {0} is used up",
                          "I'll use up the {1} in {0}"),
    "opActivateHazard": _t("the {1} in {0} goes off",
                           "I'll set off the {1} in {0}"),
    # --- reference fixtures ---
    "opClear": _t("{0} clears {2} with the {1}",
                  "I'll clear {2} with the {1}"),
}


def _sentence_from_effects(
    actor: Optional[str], name: str, args: Sequence[str],
    dels: Sequence[str], adds: Sequence[str],
) -> str:
    """Narrate an operator nobody wrote a sentence for.

    Its effects are the truth about what it does, so they are shown as-is:
    what stops being true, what becomes true. With no effects known, the
    operator is named with its arguments so the reader can look it up.
    """
    who = _nice(actor) if actor else (_nice(args[0]) if args else "someone")
    verb = _split_camel(name[2:] if name.startswith("op") else name)
    call = f"{name}({', '.join(args)})" if args else name
    parts: List[str] = [f"{who} {verb}" if verb else f"{who} does {call}"]
    if dels:
        parts.append("no longer: " + ", ".join(dels))
    if adds:
        parts.append("now: " + ", ".join(adds))
    if not dels and not adds:
        parts.append(f"({call})")
    return " - ".join(parts[:1]) + ("; " + "; ".join(parts[1:]) if len(parts) > 1 else "")


def _split_camel(name: str) -> str:
    out: List[str] = []
    for ch in name:
        if ch.isupper() and out and out[-1] != " ":
            out.append(" ")
        out.append(ch.lower())
    return "".join(out).strip()


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def narrate_operator(
    text: str,
    dels: Optional[Sequence[str]] = None,
    adds: Optional[Sequence[str]] = None,
    actor: Optional[str] = None,
) -> str:
    """One sentence for a ground operator, third person.

    `dels`/`adds` are the grounded effects (from `OperatorInstance`) and are
    used only when the operator has no entry in the table. `actor` names who
    performed it when the convention says it is not the first argument.
    """
    name, args = parse_term(text)
    entry = _TABLE.get(name)
    if entry is not None:
        return entry[0](args)
    return _sentence_from_effects(actor, name, args, list(dels or []), list(adds or []))


def narrate_intention(
    text: str,
    actor: str,
    dels: Optional[Sequence[str]] = None,
    adds: Optional[Sequence[str]] = None,
) -> str:
    """The same operator as the companion would announce it: `Warden: I'll ...`."""
    name, args = parse_term(text)
    entry = _TABLE.get(name)
    if entry is not None:
        body = entry[1](args)
    else:
        effects = list(adds or []) or list(dels or [])
        if effects:
            body = "I'll " + _split_camel(name[2:] if name.startswith("op") else name)
            body += " - " + ", ".join(effects)
        else:
            call = f"{name}({', '.join(args)})" if args else name
            body = f"I'll do {call}"
    if not body.startswith("I"):
        body = "I " + body if not body.startswith("the ") else "I note " + body
    return f"{_cap(_nice(actor))}: {body}"


_FACT_TABLE: Dict[str, Callable[[List[str]], Optional[str]]] = {
    "at": lambda a: f"{a[0]} at {a[1]}" if len(a) == 2 else None,
    "status": lambda a: f"{a[0]} is {a[1]}" if len(a) == 2 else None,
    "regionHas": lambda a: f"{a[0]} has {a[1]}" if len(a) == 2 else None,
    "hasTag": lambda a: f"{a[0]} has {a[1]}" if len(a) == 2 else None,
    "roomHasTag": lambda a: f"{a[0]} is {a[1]}" if len(a) == 2 else None,
    "roomHasHazard": lambda a: f"{a[0]} has {a[1]} hazard" if len(a) == 2 else None,
    "isEnemy": lambda a: f"{a[0]} (enemy)" if len(a) == 1 else None,
    "role": lambda a: f"{a[0]} is a {a[1]}" if len(a) == 2 else None,
    "hasSkill": lambda a: f"{a[0]} can use {a[1]}" if len(a) == 2 else None,
    "signature": lambda a: f"{a[0]}'s signature skill is {a[1]}" if len(a) == 2 else None,
    "charge": lambda a: f"{a[0]} holds {_an(a[1])} charge ({a[2]})" if len(a) == 3 else None,
    "carrying": lambda a: f"{a[0]} carries {a[1]}" if len(a) == 2 else None,
    "cleared": lambda a: f"{a[0]} is cleared" if len(a) == 1 else None,
    "hasAggro": lambda a: f"{a[0]} is fixed on {a[1]}" if len(a) == 2 else None,
    "connected": lambda a: f"{a[0]} leads to {a[1]}" if len(a) == 2 else None,
    "lineOfSight": lambda a: f"{a[1]} can be seen from {a[0]}" if len(a) == 2 else None,
}


def narrate_fact(fact: str) -> str:
    """`at(player,entry)` -> `player at entry`. Unknown facts are returned as-is."""
    name, args = parse_term(fact)
    renderer = _FACT_TABLE.get(name)
    if renderer is None:
        return fact.strip().rstrip(".")
    rendered = renderer([_nice(a) for a in args])
    return rendered if rendered is not None else fact.strip().rstrip(".")


def narrate_effects(dels: Sequence[str], adds: Sequence[str]) -> List[str]:
    """Effect lines for a step: `- player at entry` / `+ player at corridor`."""
    lines: List[str] = []
    for fact in dels:
        lines.append(f"- {narrate_fact(fact)}")
    for fact in adds:
        lines.append(f"+ {narrate_fact(fact)}")
    return lines


__all__ = [
    "narrate_effects",
    "narrate_fact",
    "narrate_intention",
    "narrate_operator",
    "parse_term",
]
