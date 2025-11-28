"""
HTN Service Wrapper
Wraps the indhtnpy Python bindings to provide a cleaner interface for the Flask API
"""

import json
import os
import sys

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

            print(f"DEBUG: Loading file: {absolute_path}")
            print(f"DEBUG: Content length: {len(file_content)} chars")

            # Compile the HTN file content
            # Use HtnCompileCustomVariables for files with ? syntax (like Taxi.htn)
            # Returns None on success, or an error string on failure
            error_result = self.planner.HtnCompileCustomVariables(file_content)

            print(f"DEBUG: Compile result: {error_result}")

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

    def get_state_facts(self):
        """
        Get the current state facts from the planner

        Uses a Prolog query to find all facts in the database.
        We query for facts with 0-3 arguments.

        Returns:
            list: List of fact strings
        """
        try:
            facts = []

            # Query for facts with different arities (0 to 3 arguments)
            # This will catch most common facts
            queries = [
                "?fact().",           # 0-arity facts
                "?fact(?a).",         # 1-arity facts
                "?fact(?a, ?b).",     # 2-arity facts
                "?fact(?a, ?b, ?c)." # 3-arity facts
            ]

            for query in queries:
                error, result_json = self.planner.PrologQuery(query)
                if error is None and result_json:
                    results = json.loads(result_json)
                    for result in results:
                        # Extract fact from result
                        if '?fact' in result:
                            fact_data = result['?fact']
                            if isinstance(fact_data, list) and len(fact_data) > 0:
                                fact_str = self._extract_value(fact_data[0])
                                if fact_str and fact_str != "true":
                                    facts.append(fact_str)

            return facts
        except Exception as e:
            print(f"Error getting state facts: {e}")
            return []
