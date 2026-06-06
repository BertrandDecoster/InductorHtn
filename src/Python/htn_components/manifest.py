"""
Manifest schema and validation for HTN components.

Each component has a manifest.json file that tracks:
- Component metadata (name, version, layer)
- Dependencies on other components
- Certification status
- Provides / requires contracts (auto-inferred during certify)

Tunable numeric knobs are expressed as Prolog facts inside src.htn
(e.g. `dashDistance(3).`), not as manifest parameters.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime


class ManifestValidationError(Exception):
    """Raised when manifest validation fails."""
    pass


@dataclass
class CertificationStatus:
    """Tracks certification status of a component."""
    linter: bool = False
    tests_pass: bool = False
    design_match: bool = False
    last_checked: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "linter": self.linter,
            "tests_pass": self.tests_pass,
            "design_match": self.design_match,
            "last_checked": self.last_checked
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CertificationStatus":
        return cls(
            linter=data.get("linter", False),
            tests_pass=data.get("tests_pass", False),
            design_match=data.get("design_match", False),
            last_checked=data.get("last_checked")
        )

    def is_certified(self) -> bool:
        """Return True if all certification checks have passed."""
        return self.linter and self.tests_pass and self.design_match


VALID_LAYERS = ["primitive", "strategy", "goal", "level", "challenges"]

VALID_CHALLENGE_CLASSES = ["S", "P", "C", "O"]


@dataclass
class ChallengeExpected:
    """Optional numeric bounds declared in a challenge block."""
    min_plans: Optional[int] = None
    max_plans: Optional[int] = None
    min_distinct_methods: Optional[int] = None

    def validate(self):
        """Validate expected bounds."""
        if self.min_plans is not None:
            if not isinstance(self.min_plans, int) or self.min_plans < 0:
                raise ManifestValidationError(
                    "challenge.expected.min_plans must be an integer >= 0"
                )
        if self.max_plans is not None:
            if not isinstance(self.max_plans, int) or self.max_plans < 1:
                raise ManifestValidationError(
                    "challenge.expected.max_plans must be an integer >= 1"
                )
        if self.min_distinct_methods is not None:
            if not isinstance(self.min_distinct_methods, int) or self.min_distinct_methods < 1:
                raise ManifestValidationError(
                    "challenge.expected.min_distinct_methods must be an integer >= 1"
                )
        if self.min_plans is not None and self.max_plans is not None:
            if self.min_plans > self.max_plans:
                raise ManifestValidationError(
                    f"challenge.expected.min_plans ({self.min_plans}) must be <= max_plans ({self.max_plans})"
                )

    def check_report(self, report: Dict[str, Any]) -> List[str]:
        """Return a list of violation strings for an evaluate_level report.

        Returns an empty list when all declared bounds are satisfied.
        """
        violations: List[str] = []
        plan_count = report.get("plan_count", 0)
        if self.min_plans is not None and plan_count < self.min_plans:
            violations.append(
                f"plan_count {plan_count} < min_plans {self.min_plans}"
            )
        if self.max_plans is not None and plan_count > self.max_plans:
            violations.append(
                f"plan_count {plan_count} > max_plans {self.max_plans}"
            )
        if self.min_distinct_methods is not None:
            distinct = len(report.get("operator_variety", []))
            if distinct < self.min_distinct_methods:
                violations.append(
                    f"distinct_methods {distinct} < min_distinct_methods {self.min_distinct_methods}"
                )
        return violations

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.min_plans is not None:
            d["min_plans"] = self.min_plans
        if self.max_plans is not None:
            d["max_plans"] = self.max_plans
        if self.min_distinct_methods is not None:
            d["min_distinct_methods"] = self.min_distinct_methods
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChallengeExpected":
        return cls(
            min_plans=data.get("min_plans"),
            max_plans=data.get("max_plans"),
            min_distinct_methods=data.get("min_distinct_methods"),
        )


@dataclass
class ChallengeBlock:
    """Optional challenge metadata for a component."""
    cls: str  # one of VALID_CHALLENGE_CLASSES — named 'cls' to avoid shadowing built-in
    behavioral_axes: List[str]
    expected: ChallengeExpected = field(default_factory=ChallengeExpected)

    def validate(self):
        """Validate the challenge block."""
        if self.cls not in VALID_CHALLENGE_CLASSES:
            raise ManifestValidationError(
                f"challenge.class must be one of {VALID_CHALLENGE_CLASSES}, got '{self.cls}'"
            )
        if not isinstance(self.behavioral_axes, list):
            raise ManifestValidationError(
                "challenge.behavioral_axes must be a list of strings"
            )
        for axis in self.behavioral_axes:
            if not isinstance(axis, str):
                raise ManifestValidationError(
                    f"challenge.behavioral_axes entries must be strings, got {axis!r}"
                )
        self.expected.validate()

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "class": self.cls,
            "behavioral_axes": self.behavioral_axes,
        }
        expected_dict = self.expected.to_dict()
        if expected_dict:
            d["expected"] = expected_dict
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChallengeBlock":
        if "class" not in data:
            raise ManifestValidationError(
                "challenge block requires 'class' field"
            )
        if "behavioral_axes" not in data:
            raise ManifestValidationError(
                "challenge block requires 'behavioral_axes' field"
            )
        return cls(
            cls=data["class"],
            behavioral_axes=data["behavioral_axes"],
            expected=ChallengeExpected.from_dict(data.get("expected", {})),
        )


@dataclass
class Manifest:
    """Component manifest containing metadata and certification status."""
    name: str
    version: str
    layer: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    certified: bool = False
    certification: CertificationStatus = field(default_factory=CertificationStatus)
    # Signatures (name/arity) defined by this component's src.htn.
    # Auto-inferred during certify; manually editing is discouraged.
    provides: List[str] = field(default_factory=list)
    # Signatures (name/arity) called by this component but defined elsewhere.
    # Auto-inferred during certify. Used by the loader to validate the dep closure.
    requires: List[str] = field(default_factory=list)
    # Optional challenge metadata — purely informational at load time,
    # validated as part of the certify command when present.
    challenge: Optional["ChallengeBlock"] = field(default=None)

    def __post_init__(self):
        self.validate()

    def validate(self):
        """Validate manifest data."""
        if not self.name:
            raise ManifestValidationError("Component name is required")

        if not self.version:
            raise ManifestValidationError("Component version is required")

        if self.layer not in VALID_LAYERS:
            raise ManifestValidationError(
                f"Invalid layer '{self.layer}'. Must be one of: {VALID_LAYERS}"
            )

        if self.challenge is not None:
            self.challenge.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary for JSON serialization."""
        d: Dict[str, Any] = {
            "name": self.name,
            "version": self.version,
            "layer": self.layer,
            "description": self.description,
            "dependencies": self.dependencies,
            "certified": self.certified,
            "certification": self.certification.to_dict(),
            "provides": self.provides,
            "requires": self.requires,
        }
        if self.challenge is not None:
            d["challenge"] = self.challenge.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Manifest":
        """Create manifest from dictionary."""
        challenge: Optional[ChallengeBlock] = None
        raw_challenge = data.get("challenge")
        if raw_challenge is not None:
            challenge = ChallengeBlock.from_dict(raw_challenge)
        return cls(
            name=data["name"],
            version=data["version"],
            layer=data["layer"],
            description=data.get("description", ""),
            dependencies=data.get("dependencies", []),
            certified=data.get("certified", False),
            certification=CertificationStatus.from_dict(
                data.get("certification", {})
            ),
            provides=data.get("provides", []),
            requires=data.get("requires", []),
            challenge=challenge,
        )

    def save(self, path: str):
        """Save manifest to JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "Manifest":
        """Load manifest from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def update_certification(self, linter: bool = None, tests_pass: bool = None,
                            design_match: bool = None):
        """Update certification status and timestamp."""
        if linter is not None:
            self.certification.linter = linter
        if tests_pass is not None:
            self.certification.tests_pass = tests_pass
        if design_match is not None:
            self.certification.design_match = design_match

        self.certification.last_checked = datetime.now().isoformat()
        self.certified = self.certification.is_certified()

    def add_dependency(self, dep: str):
        """Add a dependency if not already present."""
        if dep not in self.dependencies:
            self.dependencies.append(dep)

    def remove_dependency(self, dep: str):
        """Remove a dependency if present."""
        if dep in self.dependencies:
            self.dependencies.remove(dep)


def find_component_root(start_path: str) -> Optional[str]:
    """Find the components/ directory by walking up from start_path."""
    current = os.path.abspath(start_path)
    while current != os.path.dirname(current):
        components_dir = os.path.join(current, "components")
        if os.path.isdir(components_dir):
            return components_dir
        current = os.path.dirname(current)
    return None


def resolve_component_path(component_name: str, components_root: str) -> str:
    """Resolve a component name to its directory path.

    Component names can be:
    - Full path: "primitives/locomotion" or "levels/puzzle1"
    - Short name: "locomotion" (searches all layers)
    """
    # Try direct path first (in components/)
    direct_path = os.path.join(components_root, component_name)
    if os.path.isdir(direct_path):
        return direct_path

    # Check if it's a level (levels/ is at project root, not in components/)
    if component_name.startswith("levels/"):
        project_root = os.path.dirname(components_root)
        level_path = os.path.join(project_root, component_name)
        if os.path.isdir(level_path):
            return level_path

    # Search in layer directories within components/
    for layer_dir in ["primitives", "strategies", "goals", "challenges"]:
        layer_path = os.path.join(components_root, layer_dir, component_name)
        if os.path.isdir(layer_path):
            return layer_path

    # Also check levels/ at project root for short names
    project_root = os.path.dirname(components_root)
    levels_path = os.path.join(project_root, "levels", component_name)
    if os.path.isdir(levels_path):
        return levels_path

    raise FileNotFoundError(f"Component not found: {component_name}")


def get_component_manifest(component_path: str) -> Manifest:
    """Load the manifest for a component directory."""
    manifest_path = os.path.join(component_path, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"No manifest.json in {component_path}")
    return Manifest.load(manifest_path)


def list_all_components(components_root: str) -> List[Dict[str, Any]]:
    """List all components with their certification status."""
    components = []

    # List components from components/ directory
    for layer_dir in ["primitives", "strategies", "goals", "challenges"]:
        layer_path = os.path.join(components_root, layer_dir)
        if not os.path.isdir(layer_path):
            continue

        for component_name in os.listdir(layer_path):
            component_path = os.path.join(layer_path, component_name)
            manifest_path = os.path.join(component_path, "manifest.json")

            if os.path.isfile(manifest_path):
                try:
                    manifest = Manifest.load(manifest_path)
                    components.append({
                        "path": f"{layer_dir}/{component_name}",
                        "name": manifest.name,
                        "version": manifest.version,
                        "layer": manifest.layer,
                        "certified": manifest.certified,
                        "certification": manifest.certification.to_dict()
                    })
                except Exception as e:
                    components.append({
                        "path": f"{layer_dir}/{component_name}",
                        "name": component_name,
                        "error": str(e)
                    })

    # Also list levels from project_root/levels/
    project_root = os.path.dirname(components_root)
    levels_path = os.path.join(project_root, "levels")
    if os.path.isdir(levels_path):
        for level_name in os.listdir(levels_path):
            level_path = os.path.join(levels_path, level_name)
            manifest_path = os.path.join(level_path, "manifest.json")

            if os.path.isfile(manifest_path):
                try:
                    manifest = Manifest.load(manifest_path)
                    components.append({
                        "path": f"levels/{level_name}",
                        "name": manifest.name,
                        "version": manifest.version,
                        "layer": manifest.layer,
                        "certified": manifest.certified,
                        "certification": manifest.certification.to_dict()
                    })
                except Exception as e:
                    components.append({
                        "path": f"levels/{level_name}",
                        "name": level_name,
                        "error": str(e)
                    })

    return components
