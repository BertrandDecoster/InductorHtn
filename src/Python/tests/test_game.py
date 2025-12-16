"""
Test Suite for Game.htn

Tests the tile-based chess-like game with AI planning.

Domain summary:
- 5x5 tile grid (0-4 x 0-4)
- Player1 units: King1-1 at (2,4), Pawn1-1 at (2,3), Pawn1-2 at (1,4), Pawn1-3 at (3,4)
- Player2 units: King2-1 at (2,0), Pawn2-1 at (2,1), Pawn2-2 at (1,0), Pawn2-3 at (3,0)
- AI methods: attackKingAttackers, attackKing, defendKing, attackOpponentUnit, moveTowardsOpponentKing
- Movement: Units can move one square in any direction (including diagonal)
- Capture: Moving to an occupied enemy tile captures that unit
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from htn_test_framework import HtnTestSuite, no_duplicate_positions, fact_count


def run_tests(verbose: bool = False) -> HtnTestSuite:
    """Run all Game.htn tests."""
    suite = HtnTestSuite("Examples/Game.htn", verbose=verbose)

    # =========================================================================
    # Basic Query Tests - Verify Initial State
    # =========================================================================

    suite.assert_query(
        "tile(0, 0).",
        min_solutions=1,
        msg="Tile (0,0) exists"
    )

    suite.assert_query(
        "tile(4, 4).",
        min_solutions=1,
        msg="Tile (4,4) exists (5x5 grid)"
    )

    suite.assert_query(
        "unit(King1-1, King, Player1).",
        min_solutions=1,
        msg="Player1 King exists"
    )

    suite.assert_query(
        "at(King1-1, tile(2, 4)).",
        min_solutions=1,
        msg="Player1 King is at tile(2,4)"
    )

    suite.assert_query(
        "opponent(Player1, ?enemy).",
        bindings={"enemy": "Player2"},
        msg="Player1's opponent is Player2"
    )

    # =========================================================================
    # Distance and Movement Tests
    # =========================================================================

    suite.assert_query(
        "distance(tile(0,0), tile(1,1), ?d).",
        bindings={"d": "1"},
        msg="Diagonal distance is 1 (Chebyshev distance)"
    )

    suite.assert_query(
        "distance(tile(0,0), tile(2,0), ?d).",
        bindings={"d": "2"},
        msg="Horizontal distance of 2 tiles"
    )

    # =========================================================================
    # AI Planning Tests
    # =========================================================================

    # The AI should be able to produce at least one action
    suite.assert_plan(
        "doAI(Player1).",
        min_solutions=1,
        msg="Player1 AI can plan at least one action"
    )

    suite.assert_plan(
        "doAI(Player2).",
        min_solutions=1,
        msg="Player2 AI can plan at least one action"
    )

    # =========================================================================
    # Movement Tests
    # =========================================================================

    # Pawn1-1 is at (2,3), should be able to move to (2,2)
    suite.assert_plan(
        "tryMove(Pawn1-1, tile(2, 2)).",
        min_solutions=1,
        msg="Pawn can move forward"
    )

    # Should not be able to move more than 1 square
    suite.assert_no_plan(
        "tryMove(Pawn1-1, tile(2, 1)).",
        msg="Pawn cannot move 2 squares"
    )

    # =========================================================================
    # State Change Tests
    # =========================================================================

    suite.assert_state_after(
        "tryMove(Pawn1-1, tile(2, 2)).",
        has=["at(Pawn1-1,tile(2,2))"],
        not_has=["at(Pawn1-1,tile(2,3))"],
        msg="Moving pawn updates position"
    )

    # =========================================================================
    # Decomposition Tests
    # =========================================================================

    suite.assert_decomposition(
        "doAI(Player1).",
        uses_method=["doAI"],
        msg="AI uses doAI method"
    )

    suite.assert_decomposition(
        "tryMove(Pawn1-1, tile(2, 2)).",
        uses_method=["tryMove", "doMoveOrCapture"],
        uses_operator=["doMove"],
        msg="tryMove decomposes correctly"
    )

    # =========================================================================
    # State Invariant Tests
    # =========================================================================

    # In the initial state, no two units should share a tile
    suite.assert_state_invariant(
        no_duplicate_positions,
        "No two units on same tile (initial state)"
    )

    # =========================================================================
    # NEW TESTS: King-related Tests
    # =========================================================================

    suite.assert_query(
        "unit(?king, King, Player1).",
        bindings={"king": "King1-1"},
        msg="Player1 has one King named King1-1"
    )

    suite.assert_query(
        "unit(?king, King, Player2).",
        bindings={"king": "King2-1"},
        msg="Player2 has one King named King2-1"
    )

    suite.assert_query(
        "at(King2-1, tile(2, 0)).",
        min_solutions=1,
        msg="Player2 King is at tile(2,0)"
    )

    # Kings should be on opposite sides of the board
    suite.assert_query(
        "at(King1-1, tile(2, 4)).",
        min_solutions=1,
        msg="Player1 King starts at row 4 (bottom)"
    )

    suite.assert_query(
        "at(King2-1, tile(2, 0)).",
        min_solutions=1,
        msg="Player2 King starts at row 0 (top)"
    )

    # =========================================================================
    # NEW TESTS: Pawn Position Tests
    # =========================================================================

    suite.assert_query(
        "unit(?pawn, Pawn, Player1).",
        min_solutions=3,
        msg="Player1 has 3 pawns"
    )

    suite.assert_query(
        "unit(?pawn, Pawn, Player2).",
        min_solutions=3,
        msg="Player2 has 3 pawns"
    )

    suite.assert_query(
        "at(Pawn1-1, tile(2, 3)).",
        min_solutions=1,
        msg="Pawn1-1 starts at tile(2,3)"
    )

    suite.assert_query(
        "at(Pawn2-1, tile(2, 1)).",
        min_solutions=1,
        msg="Pawn2-1 starts at tile(2,1)"
    )

    # =========================================================================
    # NEW TESTS: Distance Calculations (Chebyshev)
    # =========================================================================

    suite.assert_query(
        "distance(tile(0,0), tile(0,0), ?d).",
        bindings={"d": "0"},
        msg="Distance to self is 0"
    )

    suite.assert_query(
        "distance(tile(0,0), tile(4,4), ?d).",
        bindings={"d": "4"},
        msg="Corner to corner distance is 4"
    )

    suite.assert_query(
        "distance(tile(2,0), tile(2,4), ?d).",
        bindings={"d": "4"},
        msg="Vertical distance across board is 4"
    )

    suite.assert_query(
        "distance(tile(0,2), tile(4,2), ?d).",
        bindings={"d": "4"},
        msg="Horizontal distance across board is 4"
    )

    # =========================================================================
    # NEW TESTS: Invalid Move Attempts
    # =========================================================================

    # Cannot move to a tile occupied by own unit (Pawn1-2 at (1,4), King1-1 at (2,4))
    suite.assert_no_plan(
        "tryMove(Pawn1-2, tile(2, 4)).",
        msg="Cannot move to tile occupied by own King"
    )

    # Cannot move diagonally more than 1 square
    suite.assert_no_plan(
        "tryMove(Pawn1-1, tile(0, 1)).",
        msg="Cannot move diagonally 2+ squares"
    )

    # Cannot move to non-adjacent tile
    suite.assert_no_plan(
        "tryMove(King1-1, tile(0, 0)).",
        msg="King cannot teleport across board"
    )

    # =========================================================================
    # NEW TESTS: Valid Diagonal Movement
    # =========================================================================

    # Pawn1-1 at (2,3) should be able to move diagonally
    suite.assert_plan(
        "tryMove(Pawn1-1, tile(1, 2)).",
        min_solutions=1,
        msg="Pawn can move diagonally (2,3) to (1,2)"
    )

    suite.assert_plan(
        "tryMove(Pawn1-1, tile(3, 2)).",
        min_solutions=1,
        msg="Pawn can move diagonally (2,3) to (3,2)"
    )

    # =========================================================================
    # NEW TESTS: Opponent Relationship
    # =========================================================================

    suite.assert_query(
        "opponent(Player2, ?enemy).",
        bindings={"enemy": "Player1"},
        msg="Player2's opponent is Player1"
    )

    # =========================================================================
    # NEW TESTS: Grid boundary tests
    # =========================================================================

    suite.assert_query(
        "tile(5, 0).",
        min_solutions=0,
        msg="Tile (5,0) does not exist - outside grid"
    )

    suite.assert_query(
        "tile(0, 5).",
        min_solutions=0,
        msg="Tile (0,5) does not exist - outside grid"
    )

    suite.assert_query(
        "tile(-1, 0).",
        min_solutions=0,
        msg="Tile (-1,0) does not exist - negative coordinate"
    )

    # =========================================================================
    # NEW TESTS: Total tile count
    # =========================================================================

    suite.assert_query(
        "tile(?x, ?y).",
        min_solutions=25,
        msg="5x5 grid has 25 tiles"
    )

    # =========================================================================
    # NEW TESTS: Units in Range Tests
    # =========================================================================

    suite.assert_query(
        "unitsInRange(King1-1, 1, ?unit).",
        min_solutions=1,
        msg="At least one unit within range 1 of King1-1"
    )

    # =========================================================================
    # NEW TESTS: AI Decomposition Tests
    # =========================================================================

    suite.assert_decomposition(
        "doAI(Player1).",
        uses_operator=["doMove"],
        msg="AI planning results in doMove operator"
    )

    # =========================================================================
    # NEW TESTS: State after AI move
    # =========================================================================

    suite.assert_state_after(
        "doAI(Player1).",
        has=["unit(King1-1,King,Player1)"],
        msg="King1-1 unit definition persists after AI move"
    )

    # =========================================================================
    # NEW TESTS: Coordinate helper functions
    # =========================================================================

    suite.assert_query(
        "x(tile(3, 2), ?val).",
        bindings={"val": "3"},
        msg="x() extracts X coordinate from tile"
    )

    suite.assert_query(
        "y(tile(3, 2), ?val).",
        bindings={"val": "2"},
        msg="y() extracts Y coordinate from tile"
    )

    # =========================================================================
    # NEW TESTS: Unit total count
    # =========================================================================

    suite.assert_query(
        "unit(?u, ?t, ?p).",
        min_solutions=8,
        msg="8 total units on the board (4 per player)"
    )

    suite.assert_query(
        "unit(?u, ?t, Player1).",
        min_solutions=4,
        msg="Player1 has 4 units total"
    )

    suite.assert_query(
        "unit(?u, ?t, Player2).",
        min_solutions=4,
        msg="Player2 has 4 units total"
    )

    # =========================================================================
    # NEW TESTS: At predicate counts
    # =========================================================================

    suite.assert_query(
        "at(?unit, ?tile).",
        min_solutions=8,
        msg="8 units have positions on the board"
    )

    # =========================================================================
    # NEW TESTS: Square generation tests
    # =========================================================================

    suite.assert_query(
        "square(tile(2, 2), 1, ?tile).",
        min_solutions=1,
        msg="Square around (2,2) with radius 1 generates tiles"
    )

    # =========================================================================
    # NEW TESTS: Custom invariant - all units have positions
    # =========================================================================

    def all_units_have_positions(facts):
        """Check that every unit has an at() fact."""
        units = set()
        positions = set()
        for fact in facts:
            if fact.startswith("unit("):
                # Extract unit name (first argument)
                inner = fact[5:-1]  # Remove "unit(" and ")"
                unit_name = inner.split(",")[0].strip()
                units.add(unit_name)
            if fact.startswith("at("):
                inner = fact[3:-1]  # Remove "at(" and ")"
                unit_name = inner.split(",")[0].strip()
                positions.add(unit_name)
        return units == positions

    suite.assert_state_invariant(
        all_units_have_positions,
        "Every unit has a position on the board"
    )

    # =========================================================================
    # NEW TESTS: State after diagonal move
    # =========================================================================

    suite.assert_state_after(
        "tryMove(Pawn1-1, tile(1, 2)).",
        has=["at(Pawn1-1,tile(1,2))"],
        not_has=["at(Pawn1-1,tile(2,3))"],
        msg="Diagonal move updates position correctly"
    )

    return suite


def get_suite(verbose: bool = False) -> HtnTestSuite:
    """Alias for run_tests for test discovery."""
    return run_tests(verbose)


if __name__ == "__main__":
    import sys
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    suite = run_tests(verbose=verbose)
    print(suite.summary())
    sys.exit(0 if suite.all_passed() else 1)
