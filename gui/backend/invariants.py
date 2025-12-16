"""
HTN State Invariants
Defines state invariants that can be checked during semantic analysis.
"""

import re
from typing import List, Optional, Dict, Callable, Any
from dataclasses import dataclass, field


@dataclass
class InvariantDefinition:
    """Definition of a state invariant"""
    id: str
    name: str
    description: str
    category: str
    enabled: bool = True
    # Pattern-based configuration
    config: Dict[str, Any] = field(default_factory=dict)


class StateInvariant:
    """A state invariant checker"""

    def __init__(self, definition: InvariantDefinition,
                 check_fn: Callable[[str, List[str], List[str], List[str], Dict], Optional[str]]):
        self.definition = definition
        self.check_fn = check_fn

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def id(self) -> str:
        return self.definition.id

    @property
    def enabled(self) -> bool:
        return self.definition.enabled

    def check_operator(self, operator_name: str, deletes: List[str],
                       adds: List[str], initial_facts: List[str]) -> Optional[str]:
        """Check if an operator might violate this invariant"""
        if not self.enabled:
            return None
        try:
            return self.check_fn(operator_name, deletes, adds, initial_facts,
                                self.definition.config)
        except Exception as e:
            return f"Error checking invariant: {e}"

    def to_dict(self) -> Dict:
        return {
            'id': self.definition.id,
            'name': self.definition.name,
            'description': self.definition.description,
            'category': self.definition.category,
            'enabled': self.definition.enabled,
            'config': self.definition.config
        }


# ============================================================
# Invariant Check Functions
# ============================================================

def check_single_position(op_name: str, deletes: List[str], adds: List[str],
                          facts: List[str], config: Dict) -> Optional[str]:
    """Check that units don't get multiple positions"""
    position_pattern = config.get('pattern', r'at\(([^,]+),\s*(.+)\)')

    # Find units being given new positions
    units_added = set()
    for add in adds:
        match = re.match(position_pattern, add)
        if match:
            units_added.add(match.group(1))

    # Find units having positions removed
    units_removed = set()
    for delete in deletes:
        match = re.match(position_pattern, delete)
        if match:
            units_removed.add(match.group(1))

    # Problem: adding position without removing old one
    orphaned = units_added - units_removed
    if orphaned:
        # Check if this is a variable (starts with ?)
        for unit in orphaned:
            if not unit.startswith('?'):
                return f"Unit '{unit}' may get multiple positions (no del before add)"

    return None


def check_no_orphan_units(op_name: str, deletes: List[str], adds: List[str],
                          facts: List[str], config: Dict) -> Optional[str]:
    """Check that units aren't left without positions"""
    position_pattern = config.get('position_pattern', r'at\(([^,]+),')
    unit_pattern = config.get('unit_pattern', r'unit\(([^)]+)\)')

    # Find units losing positions
    units_losing_pos = set()
    for delete in deletes:
        match = re.match(position_pattern, delete)
        if match:
            units_losing_pos.add(match.group(1))

    # Find units getting new positions
    units_getting_pos = set()
    for add in adds:
        match = re.match(position_pattern, add)
        if match:
            units_getting_pos.add(match.group(1))

    # Find units being deleted
    units_deleted = set()
    for delete in deletes:
        match = re.match(unit_pattern, delete)
        if match:
            units_deleted.add(match.group(1))

    # Problem: unit loses position but doesn't get new one and isn't deleted
    orphaned = units_losing_pos - units_getting_pos - units_deleted
    if orphaned:
        for unit in orphaned:
            if not unit.startswith('?'):
                return f"Unit '{unit}' may be left without a position"

    return None


def check_tile_capacity(op_name: str, deletes: List[str], adds: List[str],
                        facts: List[str], config: Dict) -> Optional[str]:
    """Check that tiles don't exceed capacity"""
    position_pattern = config.get('pattern', r'at\([^,]+,\s*(.+)\)')
    max_capacity = config.get('max_capacity', 1)

    # Find tiles getting new occupants
    tiles_added = []
    for add in adds:
        match = re.match(position_pattern, add)
        if match:
            tiles_added.append(match.group(1))

    # Find tiles losing occupants
    tiles_removed = []
    for delete in deletes:
        match = re.match(position_pattern, delete)
        if match:
            tiles_removed.append(match.group(1))

    # Check if any tile gets net positive without losing
    for tile in tiles_added:
        if tile not in tiles_removed and not tile.startswith('?'):
            return f"Tile '{tile}' may exceed capacity (adding without removing)"

    return None


def check_resource_balance(op_name: str, deletes: List[str], adds: List[str],
                           facts: List[str], config: Dict) -> Optional[str]:
    """Check that resources are properly balanced (conservation)"""
    resource_pattern = config.get('pattern', r'has\(([^,]+),\s*(\d+)\)')

    # This is a simplified check - just warns about resource changes
    resources_changed = []
    for add in adds:
        match = re.match(resource_pattern, add)
        if match:
            resources_changed.append(f"+{match.group(1)}:{match.group(2)}")

    for delete in deletes:
        match = re.match(resource_pattern, delete)
        if match:
            resources_changed.append(f"-{match.group(1)}:{match.group(2)}")

    # Just informational - no automatic violation detection
    return None


def check_state_consistency(op_name: str, deletes: List[str], adds: List[str],
                            facts: List[str], config: Dict) -> Optional[str]:
    """Check for obviously inconsistent state changes"""
    # Check if same fact is both added and deleted
    for add in adds:
        if add in deletes:
            return f"Fact '{add}' is both added and deleted (no-op?)"

    # Check for conflicting facts
    conflict_patterns = config.get('conflicts', [])
    for pattern1, pattern2 in conflict_patterns:
        adds_p1 = [a for a in adds if re.match(pattern1, a)]
        adds_p2 = [a for a in adds if re.match(pattern2, a)]
        if adds_p1 and adds_p2:
            return f"Potentially conflicting facts added: {adds_p1[0]} and {adds_p2[0]}"

    return None


def check_delete_exists(op_name: str, deletes: List[str], adds: List[str],
                        facts: List[str], config: Dict) -> Optional[str]:
    """Warn when deleting facts that may not exist"""
    # This is a heuristic check - can't be certain without runtime analysis
    for delete in deletes:
        # Skip if it contains variables
        if '?' in delete:
            continue

        # Check if this fact (or a similar pattern) exists in initial facts
        base_pattern = delete.split('(')[0]
        matching = [f for f in facts if f.startswith(base_pattern + '(')]
        if not matching:
            return f"Deleting '{delete}' but no matching fact exists in initial state"

    return None


# ============================================================
# Invariant Registry
# ============================================================

class InvariantRegistry:
    """Registry of all available invariants"""

    def __init__(self):
        self.invariants: Dict[str, StateInvariant] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default invariants"""
        # Position invariants
        self.register(StateInvariant(
            InvariantDefinition(
                id='single_position',
                name='Single Position',
                description='Each unit can only occupy one position at a time',
                category='position',
                config={'pattern': r'at\(([^,]+),\s*(.+)\)'}
            ),
            check_single_position
        ))

        self.register(StateInvariant(
            InvariantDefinition(
                id='no_orphan_units',
                name='No Orphan Units',
                description='Units must always have a valid position',
                category='position',
                config={
                    'position_pattern': r'at\(([^,]+),',
                    'unit_pattern': r'unit\(([^)]+)\)'
                }
            ),
            check_no_orphan_units
        ))

        self.register(StateInvariant(
            InvariantDefinition(
                id='tile_capacity',
                name='Tile Capacity',
                description='Tiles cannot have more than max_capacity units',
                category='position',
                config={
                    'pattern': r'at\([^,]+,\s*(.+)\)',
                    'max_capacity': 1
                }
            ),
            check_tile_capacity
        ))

        # State consistency invariants
        self.register(StateInvariant(
            InvariantDefinition(
                id='state_consistency',
                name='State Consistency',
                description='Detect obviously inconsistent state changes',
                category='consistency',
                config={'conflicts': []}
            ),
            check_state_consistency
        ))

        self.register(StateInvariant(
            InvariantDefinition(
                id='delete_exists',
                name='Delete Exists',
                description='Warn when deleting facts that may not exist',
                category='consistency',
                enabled=False  # Disabled by default - too many false positives
            ),
            check_delete_exists
        ))

    def register(self, invariant: StateInvariant):
        """Register an invariant"""
        self.invariants[invariant.id] = invariant

    def get(self, invariant_id: str) -> Optional[StateInvariant]:
        """Get an invariant by ID"""
        return self.invariants.get(invariant_id)

    def get_all(self) -> List[StateInvariant]:
        """Get all registered invariants"""
        return list(self.invariants.values())

    def get_enabled(self) -> List[StateInvariant]:
        """Get all enabled invariants"""
        return [inv for inv in self.invariants.values() if inv.enabled]

    def get_by_category(self, category: str) -> List[StateInvariant]:
        """Get invariants by category"""
        return [inv for inv in self.invariants.values()
                if inv.definition.category == category]

    def enable(self, invariant_id: str, enabled: bool = True):
        """Enable or disable an invariant"""
        if invariant_id in self.invariants:
            self.invariants[invariant_id].definition.enabled = enabled

    def configure(self, invariant_id: str, config: Dict):
        """Update configuration for an invariant"""
        if invariant_id in self.invariants:
            self.invariants[invariant_id].definition.config.update(config)

    def to_dict(self) -> Dict:
        """Export registry as dictionary"""
        return {
            'invariants': [inv.to_dict() for inv in self.invariants.values()],
            'categories': list(set(inv.definition.category
                                  for inv in self.invariants.values()))
        }


# Global registry instance
_registry = InvariantRegistry()


def get_registry() -> InvariantRegistry:
    """Get the global invariant registry"""
    return _registry


def get_enabled_invariants() -> List[StateInvariant]:
    """Get all enabled invariants from the global registry"""
    return _registry.get_enabled()


def create_custom_invariant(id: str, name: str, description: str,
                           category: str, check_fn: Callable,
                           config: Dict = None) -> StateInvariant:
    """Create a custom invariant"""
    return StateInvariant(
        InvariantDefinition(
            id=id,
            name=name,
            description=description,
            category=category,
            config=config or {}
        ),
        check_fn
    )
