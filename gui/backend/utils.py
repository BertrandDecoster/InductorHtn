"""Utility functions for InductorHTN GUI backend"""

import json


def pretty_solution(solution):
    """Convert a solution JSON to human-readable operator sequence.

    Input: [{"walk":[{"downtown":[]},{"park":[]}]}]
    Output: "walk(downtown, park)"
    """
    if isinstance(solution, str):
        solution = json.loads(solution)

    operators = []
    for op in solution:
        # Each op is a dict with one key (operator name) and value (list of args)
        for op_name, args in op.items():
            # Each arg is a dict with one key (the arg value) and empty list
            arg_values = [list(arg.keys())[0] for arg in args]
            operators.append(f"{op_name}({', '.join(arg_values)})")

    return ", ".join(operators)
