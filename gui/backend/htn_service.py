"""
HTN Service Wrapper
Wraps the indhtnpy Python bindings to provide a cleaner interface for the Flask API
"""

import json
import os
import sys

from utils import pretty_solution

# Add paths for indhtnpy module and DLL
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
python_dir = os.path.join(project_root, 'src', 'Python')
build_dir = os.path.join(project_root, 'build', 'Release')
build_debug_dir = os.path.join(project_root, 'build', 'Debug')

# Add Python directory to sys.path for indhtnpy.py import
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

# Add build directories to PATH for DLL loading on Windows
if sys.platform == 'win32':
    os.environ['PATH'] = f"{build_dir};{build_debug_dir};{python_dir};{os.environ.get('PATH', '')}"
    # Also add current directory
    os.add_dll_directory(python_dir)
    if os.path.exists(build_dir):
        os.add_dll_directory(build_dir)
    if os.path.exists(build_debug_dir):
        os.add_dll_directory(build_debug_dir)

# Import the Python bindings
try:
    from indhtnpy import HtnPlanner
except ImportError as e:
    print("ERROR: Could not import indhtnpy module")
    print(f"Import error: {e}")
    print(f"Python directory: {python_dir}")
    print(f"Build directory: {build_dir}")
    print("Make sure indhtnpy.dll (Windows) or libindhtnpy.dylib (macOS) or libindhtnpy.so (Linux) is available")
    print("You may need to copy it to the Python directory or build the project first")
    sys.exit(1)


class HtnService:
    """Service class that wraps HtnPlanner from Python bindings"""

    def __init__(self, debug=False):
        """Initialize the HTN planner"""
        self.planner = HtnPlanner(debug)
        self.current_file = None

    def load_file(self, file_path):
        """
        Load a .htn file into the planner

        Args:
            file_path: Relative or absolute path to .htn file

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            # Resolve to absolute path if relative
            if not os.path.isabs(file_path):
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
                absolute_path = os.path.join(project_root, file_path)
            else:
                absolute_path = file_path

            if not os.path.exists(absolute_path):
                return False, f"File not found: {absolute_path}"

            # HtnCompile expects the FILE CONTENT, not the file path!
            # Read the file content
            with open(absolute_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Hard reset: Explicitly delete old planner before creating new one
            # This ensures the C++ destructor runs before we create a new instance
            # (prevents race condition with garbage collector)
            if hasattr(self, 'planner') and self.planner is not None:
                del self.planner
                self.planner = None
                import gc
                gc.collect()

            self.planner = HtnPlanner(False)

            # Compile the HTN file content
            # Use HtnCompileCustomVariables for files with ? syntax (like Taxi.htn)
            # Returns None on success, or an error string on failure
            error_result = self.planner.HtnCompileCustomVariables(file_content)

            if error_result is None:  # None means success
                self.current_file = file_path
                return True, None
            else:
                return False, error_result  # error_result contains error message on failure

        except Exception as e:
            return False, str(e)

    def execute_prolog_query(self, query):
        """
        Execute a Prolog query and return results

        Args:
            query: Prolog query string (e.g., "at(?where).")

        Returns:
            dict: {
                'solutions': list of solution dicts,
                'variables': list of variable names,
                'total_count': int,
                'tree': computation tree structure (placeholder for now)
            }
            or {'error': error_message}
        """
        try:
            # Execute the query
            # PrologQuery returns (error_or_None, result_json_or_None)
            error, result_json = self.planner.PrologQuery(query)

            if error is not None:  # error is not None means there was an error
                return {'error': error}

            # Parse the JSON result
            results = json.loads(result_json)

            # Format into table structure
            formatted = self._format_prolog_results(results)

            # For now, create a simple placeholder tree
            # TODO: Implement actual computation tree capture
            tree = self._create_placeholder_tree(query, formatted['solutions'])

            return {
                'solutions': formatted['solutions'],
                'variables': formatted['variables'],
                'total_count': len(formatted['solutions']),
                'tree': tree,
                'query': query
            }

        except json.JSONDecodeError as e:
            return {'error': f'Failed to parse results: {str(e)}'}
        except Exception as e:
            return {'error': str(e)}

    def _format_prolog_results(self, results):
        """
        Format Prolog results into table structure

        Args:
            results: Parsed JSON results from PrologQuery

        Returns:
            dict: {
                'solutions': list of dicts with variable bindings,
                'variables': list of variable names
            }
        """
        if not results or len(results) == 0:
            return {'solutions': [], 'variables': []}

        solutions = []
        variables = set()

        for result in results:
            if not isinstance(result, dict):
                continue

            solution = {}
            for var_name, value in result.items():
                variables.add(var_name)
                # Extract the actual value from the nested structure
                if isinstance(value, list) and len(value) > 0:
                    # Handle structure like {"?x": [{"value": []}]}
                    solution[var_name] = self._extract_value(value[0])
                else:
                    solution[var_name] = str(value)

            solutions.append(solution)

        return {
            'solutions': solutions,
            'variables': sorted(list(variables))
        }

    def _extract_value(self, value_obj):
        """Extract the actual value from the nested JSON structure"""
        if isinstance(value_obj, dict):
            # Get the first key as the value name
            if len(value_obj) == 0:
                return "true"
            key = list(value_obj.keys())[0]
            nested = value_obj[key]
            if isinstance(nested, list) and len(nested) == 0:
                # Atom with no arguments
                return key
            elif isinstance(nested, list):
                # Compound term
                args = [self._extract_value(arg) for arg in nested]
                return f"{key}({', '.join(args)})"
        return str(value_obj)

    def _create_placeholder_tree(self, query, solutions):
        """
        Create a placeholder tree structure for visualization
        TODO: Replace with actual computation tree from C++ tracing

        Args:
            query: The query string
            solutions: List of solution dicts

        Returns:
            dict: Tree structure compatible with react-arborist
        """
        return {
            'id': 'root',
            'name': f'Query: {query}',
            'status': 'success' if len(solutions) > 0 else 'failure',
            'children': [
                {
                    'id': f'solution-{i}',
                    'name': f'Solution {i + 1}',
                    'status': 'success',
                    'bindings': solution
                }
                for i, solution in enumerate(solutions[:10])  # Limit to first 10 for now
            ]
        }

    def execute_htn_query(self, query):
        """
        Execute an HTN planning query and return plans + decomposition trees

        Args:
            query: HTN goal query (e.g., "travel-to(park).")

        Returns:
            dict: {
                'solutions': list of solution operators,
                'trees': list of tree structures (one per solution),
                'total_count': int
            }
        """
        try:
            # Execute HTN planning
            error, solutions_json = self.planner.FindAllPlansCustomVariables(query)

            if error is not None:
                return {'error': error}

            solutions = json.loads(solutions_json)

            # Get decomposition tree for each solution
            trees = []
            for i in range(len(solutions)):
                error, tree_json = self.planner.GetDecompositionTree(i)
                if error is None:
                    tree_nodes = json.loads(tree_json)
                    # Transform to react-arborist format
                    tree = self._transform_decomp_tree(tree_nodes, i)
                    trees.append(tree)

            # Format solutions nicely
            pretty_solutions = [pretty_solution(sol) for sol in solutions]

            return {
                'solutions': solutions,
                'pretty_solutions': pretty_solutions,
                'trees': trees,
                'total_count': len(solutions)
            }
        except Exception as e:
            return {'error': str(e)}

    def _transform_decomp_tree(self, nodes, solution_index):
        """
        Transform C++ decomposition tree JSON to react-arborist format

        C++ format (flat array):
        [
            {"nodeID": 0, "parentNodeID": -1, "childNodeIDs": [1,6], ...},
            {"nodeID": 1, "parentNodeID": 0, ...},
            ...
        ]

        react-arborist format (nested):
        {
            "id": "node-0",
            "name": "travel-to",
            "children": [...]
        }
        """
        if not nodes:
            return None

        # Build lookup map
        node_map = {n['nodeID']: n for n in nodes}

        # Find root (parentNodeID == -1)
        roots = [n for n in nodes if n['parentNodeID'] == -1]
        if not roots:
            return None

        def build_tree(node):
            node_id = node['nodeID']
            is_operator = node.get('isOperator', False)

            # Determine display name
            signature = node.get('operatorSignature') or node.get('methodSignature') or ''
            if signature:
                name = signature.split('(')[0]
            elif node.get('taskName'):
                name = node['taskName'].split('(')[0]
            else:
                name = '(leaf)'

            # Build bindings dict
            bindings = {}
            for u in node.get('unifiers', []):
                bindings.update(u)

            condition_bindings = {}
            for cb in node.get('conditionBindings', []):
                condition_bindings.update(cb)

            # Determine status
            status = 'default'
            if node.get('isFailed') and not node.get('isSuccess'):
                status = 'failure'
            elif node.get('isSuccess'):
                status = 'success'

            # Build children recursively
            children = []
            for child_id in node.get('childNodeIDs', []):
                if child_id in node_map:
                    children.append(build_tree(node_map[child_id]))

            return {
                'id': f'sol{solution_index}-node{node_id}',
                'name': name,
                'fullSignature': signature,
                'taskName': node.get('taskName', ''),
                'isOperator': is_operator,
                'status': status,
                'bindings': bindings,
                'conditionBindings': condition_bindings,
                'failureReason': node.get('failureReason', ''),
                'conditionTerms': node.get('conditionTerms', []),
                'children': children
            }

        return build_tree(roots[0])

    def get_state_facts(self):
        """
        Get the current state facts from the planner

        Uses the C++ API to get all facts directly from the ruleset.

        Returns:
            list: List of fact strings
        """
        print("DEBUG get_state_facts: START")
        try:
            print("DEBUG get_state_facts: Calling planner.GetStateFacts()...")
            error, result_json = self.planner.GetStateFacts()
            print(f"DEBUG get_state_facts: Got response, error={error}")
            if error is not None:
                print(f"Error getting state facts: {error}")
                return []

            facts = json.loads(result_json)
            print(f"DEBUG get_state_facts: Parsed {len(facts)} facts")
            return facts
        except Exception as e:
            print(f"Error getting state facts: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_solution_facts(self, solution_index):
        """
        Get the facts for a specific solution's final state

        Args:
            solution_index: Index of the solution (0-based)

        Returns:
            list: List of fact strings, or empty list on error
        """
        try:
            error, result_json = self.planner.GetSolutionFacts(solution_index)
            if error is not None:
                print(f"Error getting solution facts: {error}")
                return []

            facts = json.loads(result_json)
            return facts
        except Exception as e:
            print(f"Error getting solution facts: {e}")
            return []

    def get_facts_diff(self, solution_index):
        """
        Get the diff between initial state and solution's final state

        Args:
            solution_index: Index of the solution (0-based)

        Returns:
            dict: {
                'added': [...],      # Facts in solution but not in initial state
                'removed': [...],    # Facts in initial but not in solution
                'unchanged': [...]   # Facts in both
            }
        """
        try:
            initial_facts = set(self.get_state_facts())
            solution_facts = set(self.get_solution_facts(solution_index))

            added = list(solution_facts - initial_facts)
            removed = list(initial_facts - solution_facts)
            unchanged = list(initial_facts & solution_facts)

            # Sort for consistent display
            added.sort()
            removed.sort()
            unchanged.sort()

            return {
                'added': added,
                'removed': removed,
                'unchanged': unchanged
            }
        except Exception as e:
            print(f"Error getting facts diff: {e}")
            return {
                'added': [],
                'removed': [],
                'unchanged': []
            }
