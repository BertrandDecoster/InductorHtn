# PythonUsageTrace.py - Test the new GetDecompositionTree() API
# This demonstrates the efficient decomposition tree API that replaces
# trace string parsing with direct structured access
import json
import os
import pprint
import sys

from indhtnpy import HtnPlanner


def prettySolution(solution):
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


def print_tree_node(node, indent=0):
    """Pretty print a single tree node with improved formatting"""
    prefix = "  " * indent

    # Use different brackets for operators vs methods
    node_id = node['nodeID']
    if node.get("isOperator"):
        bracket = f"[{node_id}]"  # Operators use square brackets
    else:
        bracket = f"{{{node_id}}}"  # Methods use curly braces

    # Get signature and extract name
    signature = node.get("operatorSignature") or node.get("methodSignature") or ""
    if signature:
        name = signature.split("(")[0]
    elif node['taskName']:
        name = node['taskName'].split("(")[0]
    else:
        name = "(leaf)"

    # Show failure info only for failed nodes that didn't eventually succeed
    status = ""
    if node.get("isFailed") and not node.get("isSuccess"):
        status = f" FAILED: {node.get('failureReason', '')}"

    print(f"{prefix}{bracket} {name}{status}")

    # Show full signature on next line if present
    if signature:
        print(f"{prefix}    {signature}")

    # Show head bindings
    if node.get("unifiers"):
        bindings = ", ".join([f"{k}={v}" for u in node["unifiers"] for k, v in u.items()])
        print(f"{prefix}    Head: {bindings}")

    # Show condition bindings (if() clause)
    if node.get("conditionBindings"):
        bindings = ", ".join([f"{k}={v}" for u in node["conditionBindings"] for k, v in u.items()])
        print(f"{prefix}    Condition: {bindings}")


def print_tree_recursive(nodes, node_id, indent=0):
    """Recursively print tree from a given node"""
    # Find node by ID
    node = None
    for n in nodes:
        if n["nodeID"] == node_id:
            node = n
            break

    if not node:
        return

    print_tree_node(node, indent)

    # Print children
    for child_id in node.get("childNodeIDs", []):
        print_tree_recursive(nodes, child_id, indent + 1)


def print_full_tree(nodes):
    """Print the complete tree starting from root nodes"""
    if not nodes:
        print("  (empty tree)")
        return

    # Find root nodes (parentNodeID == -1)
    roots = [n for n in nodes if n["parentNodeID"] == -1]

    for root in roots:
        print_tree_recursive(nodes, root["nodeID"], 0)


def main():
    print("=" * 70)
    print("Testing GetDecompositionTree() API")
    print("=" * 70)
    print()

    # Create planner (debug mode off for cleaner output)
    planner = HtnPlanner(False)

    # Simple travel domain from Taxi.htn
    program = """
    travel-to(?q) :-
        if(at(?p), walking-distance(?p, ?q)),
        do(walk(?p, ?q)).
    travel-to(?q) :-
        if(at(?p), have-taxi-fare(?p, ?q)),
        do(ride-taxi(?p, ?q)).

    walk(?from, ?to) :- del(at(?from)), add(at(?to)).
    ride-taxi(?from, ?to) :- del(at(?from), have-cash), add(at(?to)).

    walking-distance(downtown, park).
    have-taxi-fare(downtown, park).
    at(downtown).
    have-cash.
    """

    result = planner.Compile(program)
    if result is not None:
        print(f"Compile Error: {result}")
        sys.exit(1)

    # Find all plans
    query = "travel-to(park)."
    print(f"Query: {query}")
    print()

    error, solutions = planner.FindAllPlansCustomVariables(query)
    if error:
        print(f"Planning Error: {error}")
        sys.exit(1)

    solutions_json = json.loads(solutions)
    print(f"Found {len(solutions_json)} solution(s)")
    print()

    # Get decomposition tree for each solution
    for i in range(len(solutions_json)):
        print("-" * 50)
        print(f"Solution {i}: {solutions_json[i]}")
        print("-" * 50)

        error, tree_json = planner.GetDecompositionTree(i)
        if error:
            print(f"  GetDecompositionTree Error: {error}")
            continue

        nodes = json.loads(tree_json)
        print(f"Tree has {len(nodes)} nodes:")
        print()
        print_full_tree(nodes)
        print()

    # Also test with a failing plan to see failed branches
    print("=" * 70)
    print("Testing with scenario that has failures")
    print("=" * 70)
    print()

    planner2 = HtnPlanner(False)

    # Program where one method will fail
    program2 = """
    get-to-work(?dest) :-
        if(at(?p), has-car),
        do(drive(?p, ?dest)).
    get-to-work(?dest) :-
        if(at(?p)),
        do(walk-to-work(?p, ?dest)).

    drive(?from, ?to) :- del(at(?from)), add(at(?to)).
    walk-to-work(?from, ?to) :- del(at(?from)), add(at(?to), tired).

    at(home).
    """

    result2 = planner2.Compile(program2)
    if result2 is not None:
        print(f"Compile Error: {result2}")
        sys.exit(1)

    query2 = "get-to-work(office)."
    print(f"Query: {query2}")
    print("Note: has-car is NOT in the database, so drive method should fail")
    print()

    error2, solutions2 = planner2.FindAllPlansCustomVariables(query2)
    if error2:
        print(f"Planning Error: {error2}")
        sys.exit(1)

    solutions2_json = json.loads(solutions2)
    print(f"Found {len(solutions2_json)} solution(s)")

    for i in range(len(solutions2_json)):
        print("-" * 50)
        print(f"Solution {i}: {solutions2_json[i]}")
        print("-" * 50)

        error, tree_json = planner2.GetDecompositionTree(i)
        if error:
            print(f"  GetDecompositionTree Error: {error}")
            continue

        nodes = json.loads(tree_json)
        print(f"Tree has {len(nodes)} nodes:")
        print()

        # Raw JSON for inspection
        print("Raw JSON:")
        pp = pprint.PrettyPrinter(indent=2, width=100)
        pp.pprint(nodes)
        print()

        print("Tree view:")
        print_full_tree(nodes)
        print()


    # Test with Taxi.htn if available
    print("=" * 70)
    print("Testing Taxi.htn")
    print("=" * 70)
    print()

    # Try to find Taxi.htn from project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    taxi_path = os.path.join(project_root, "Examples", "Taxi.htn")

    if not os.path.exists(taxi_path):
        print(f"Taxi.htn not found at {taxi_path}, skipping...")
        return

    planner3 = HtnPlanner(False)

    with open(taxi_path, "r") as f:
        program3 = f.read()

    result3 = planner3.Compile(program3)
    if result3 is not None:
        print(f"Compile Error: {result3}")
        sys.exit(1)

    query3 = "travel-to(uptown)."
    print(f"Query: {query3}")
    print()

    error3, solutions3 = planner3.FindAllPlansCustomVariables(query3)
    if error3:
        print(f"Planning Error: {error3}")
        sys.exit(1)

    solutions3_json = json.loads(solutions3)
    print(f"Found {len(solutions3_json)} solution(s)")

    for i in range(len(solutions3_json)):
        print("-" * 50)
        print(f"Solution {i}: {solutions3_json[i]}")
        print("-" * 50)

        error, tree_json = planner3.GetDecompositionTree(i)
        if error:
            print(f"  GetDecompositionTree Error: {error}")
            continue

        nodes = json.loads(tree_json)
        print(f"Tree has {len(nodes)} nodes:")
        print()

        # Raw JSON for inspection
        print("Raw JSON:")
        pp = pprint.PrettyPrinter(indent=2, width=100)
        pp.pprint(nodes)
        print()


        print("Tree view:")
        print_full_tree(nodes)
        print()


if __name__ == "__main__":
    main()
