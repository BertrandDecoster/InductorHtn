"""Who did it: actor provenance for operators.

The GDD's pillar is "the companions must not solo the map". Read literally
as "some operator mentions the player", a no-op `opWait(player)` satisfies
it, and so does a companion shielding the player. Neither is the player
*doing* anything. This module gives the metrics the stronger reading:

  - an operator's **actor** is the argument the actor convention names -
    the first argument by default (`actor_position` in metrics.json), or
    the index a level's `funActor(opName, index)` fact declares;
  - an operator is **consequential** when it changes the world (non-empty
    del/add) and the level has not declared it bookkeeping with
    `funNoop(opName)`;
  - a **player action** is a consequential operator whose actor is the
    player; a **passive mention** is any operator that names the player
    without the player being its actor.

The same convention serves the plan trie (whose forks count as the player's
decisions only when the alternatives are player actions) and the MCP play
tools (which show the player their own actions and the companions'
intentions).
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, Set

from .config import Config
from .extract import OperatorInstance, PlanSpace, split_args


@dataclass
class ActorConvention:
    position: int = 0
    overrides: Dict[str, int] = field(default_factory=dict)
    noops: Set[str] = field(default_factory=set)
    player: str = "player"

    # ------------------------------------------------------------ building

    @classmethod
    def from_facts(cls, facts: Sequence[str], cfg: Config) -> "ActorConvention":
        overrides: Dict[str, int] = {}
        noops: Set[str] = set()
        for fact in facts:
            if fact.startswith("funActor("):
                args = split_args(fact[fact.find("(") + 1: fact.rfind(")")])
                if len(args) == 2:
                    try:
                        overrides[args[0]] = int(args[1])
                    except ValueError:
                        continue
            elif fact.startswith("funNoop("):
                args = split_args(fact[fact.find("(") + 1: fact.rfind(")")])
                if args:
                    noops.add(args[0])
        return cls(
            position=int(cfg.get("actor_position", 0)),
            overrides=overrides,
            noops=noops,
            player=cfg.player_atom,
        )

    @classmethod
    def from_space(cls, space: PlanSpace, cfg: Config) -> "ActorConvention":
        return cls.from_facts(space.facts_used, cfg)

    # ------------------------------------------------------------- queries

    def actor_of(self, op: OperatorInstance) -> Optional[str]:
        index = self.overrides.get(op.name, self.position)
        if 0 <= index < len(op.args):
            return op.args[index]
        return None

    def is_consequential(self, op: OperatorInstance) -> bool:
        return op.name not in self.noops and bool(op.dels or op.adds)

    def is_player_action(self, op: OperatorInstance) -> bool:
        return self.is_consequential(op) and self.actor_of(op) == self.player

    def is_passive_mention(self, op: OperatorInstance) -> bool:
        return self.player in op.args and self.actor_of(op) != self.player
