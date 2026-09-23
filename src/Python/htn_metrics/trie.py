"""The plan space as a trie of operator prefixes.

Every plan is an operator sequence; laid over each other they form a trie
whose forks are where the plans diverge. That structure answers two
questions the flat plan list cannot:

  - **Where does the player decide?** A node whose children include two or
    more distinct player actions is a decision the player makes; a node
    whose children are all companion operators is a decision the planner
    makes on the companions' behalf.
  - **What would play look like?** Advancing through companion-only nodes
    by the planner's own preference (lowest plan index first, which is the
    method order the author wrote) and stopping wherever the player has an
    action to take is the skeleton of a player-perspective playthrough.

The trie is built once per plan space and is cheap to walk.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .agency import ActorConvention
from .extract import OperatorInstance, PlanSpace

FINISHED = "<done>"

Prefix = Tuple[str, ...]


@dataclass
class Choice:
    """One child of a trie node: the next operator, or the end of a plan."""

    text: str
    op: Optional[OperatorInstance]
    plan_indices: List[int] = field(default_factory=list)
    actor: Optional[str] = None
    consequential: bool = False

    @property
    def finished(self) -> bool:
        return self.op is None

    @property
    def preference(self) -> int:
        """Lower is preferred: the planner found this branch first."""
        return min(self.plan_indices) if self.plan_indices else 1 << 30


@dataclass
class _Node:
    plans: List[int] = field(default_factory=list)
    children: Dict[str, "_Node"] = field(default_factory=dict)
    op: Optional[OperatorInstance] = None      # the operator that led here
    finished: List[int] = field(default_factory=list)


class PlanTrie:
    def __init__(self, space: PlanSpace, convention: ActorConvention):
        self.space = space
        self.convention = convention
        self._root = _Node()
        for plan in space.plans:
            node = self._root
            node.plans.append(plan.index)
            for op in plan.operators:
                child = node.children.get(op.text)
                if child is None:
                    child = _Node(op=op)
                    node.children[op.text] = child
                child.plans.append(plan.index)
                node = child
            node.finished.append(plan.index)

    # ------------------------------------------------------------ walking

    def _node(self, prefix: Sequence[str]) -> Optional[_Node]:
        node = self._root
        for text in prefix:
            node = node.children.get(text)
            if node is None:
                return None
        return node

    def surviving(self, prefix: Sequence[str]) -> List[int]:
        """Plan indices consistent with `prefix`."""
        node = self._node(prefix)
        return list(node.plans) if node else []

    def children(self, prefix: Sequence[str]) -> Dict[str, Choice]:
        """The distinct next steps after `prefix`, keyed by operator text.

        Plans that end exactly at `prefix` appear under `FINISHED`.
        """
        node = self._node(prefix)
        if node is None:
            return {}
        out: Dict[str, Choice] = {}
        for text, child in node.children.items():
            op = child.op
            out[text] = Choice(
                text=text, op=op, plan_indices=list(child.plans),
                actor=self.convention.actor_of(op) if op else None,
                consequential=self.convention.is_consequential(op) if op else False,
            )
        if node.finished:
            out[FINISHED] = Choice(text=FINISHED, op=None, plan_indices=list(node.finished))
        return out

    def player_options(self, prefix: Sequence[str]) -> List[Choice]:
        return [
            c for c in self.children(prefix).values()
            if not c.finished and c.consequential
            and c.actor == self.convention.player
        ]

    def auto_advance_companions(self, prefix: Sequence[str]) -> Prefix:
        """Follow companion-only steps by the planner's preference until the
        player has an action to take, a plan is complete, or nothing follows."""
        current: Prefix = tuple(prefix)
        while True:
            options = self.children(current)
            if not options:
                return current
            if any(c.finished for c in options.values()):
                return current
            if any(
                c.consequential and c.actor == self.convention.player
                for c in options.values()
            ):
                return current
            best = min(options.values(), key=lambda c: c.preference)
            current = current + (best.text,)

    def nodes(self) -> Iterable[Prefix]:
        """Every prefix in the trie, root first, depth-first."""
        stack: List[Tuple[Prefix, _Node]] = [((), self._root)]
        while stack:
            prefix, node = stack.pop()
            yield prefix
            for text, child in node.children.items():
                stack.append((prefix + (text,), child))

    def player_decision_points(self) -> int:
        """Nodes where the player has a choice: at least two distinct next
        steps, at least one of which is the player's own action. Choosing to
        act, or to let a companion open instead, is a decision; a fork among
        companion operators alone is the planner's."""
        count = 0
        for prefix in self.nodes():
            options = [c for c in self.children(prefix).values() if not c.finished]
            if len({c.text for c in options}) >= 2 and self.player_options(prefix):
                count += 1
        return count
