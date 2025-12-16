#!/usr/bin/env python3
"""
HTN Tools - Command-line interface for HTN analysis
Provides linting, semantic analysis, and batch processing of HTN files.
"""

import argparse
import json
import os
import sys
import glob
from typing import List, Dict, Any

# Add paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, '..', 'backend')
sys.path.insert(0, backend_dir)

from htn_linter import lint_file
from htn_analyzer import analyze_file
from invariants import get_registry, get_enabled_invariants


class HtnTools:
    """Command-line HTN analysis tools"""

    def __init__(self, verbose: bool = False, json_output: bool = False):
        self.verbose = verbose
        self.json_output = json_output
        self.project_root = os.path.abspath(os.path.join(script_dir, '../..'))

    def resolve_path(self, path: str) -> str:
        """Resolve a path relative to project root"""
        if os.path.isabs(path):
            return path
        return os.path.join(self.project_root, path)

    def lint(self, file_paths: List[str]) -> Dict[str, Any]:
        """Lint one or more HTN files"""
        results = {}
        total_errors = 0
        total_warnings = 0

        for path in file_paths:
            full_path = self.resolve_path(path)
            try:
                diagnostics = lint_file(full_path)
                errors = [d for d in diagnostics if d.get('severity') == 'error']
                warnings = [d for d in diagnostics if d.get('severity') == 'warning']

                results[path] = {
                    'diagnostics': diagnostics,
                    'error_count': len(errors),
                    'warning_count': len(warnings)
                }

                total_errors += len(errors)
                total_warnings += len(warnings)

                if not self.json_output:
                    self._print_lint_results(path, diagnostics)

            except FileNotFoundError:
                results[path] = {'error': 'File not found'}
                if not self.json_output:
                    print(f"ERROR: File not found: {path}")
            except Exception as e:
                results[path] = {'error': str(e)}
                if not self.json_output:
                    print(f"ERROR: {path}: {e}")

        if self.json_output:
            print(json.dumps({
                'results': results,
                'total_errors': total_errors,
                'total_warnings': total_warnings
            }, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"Total: {total_errors} errors, {total_warnings} warnings")

        return results

    def _print_lint_results(self, path: str, diagnostics: List[Dict]):
        """Print lint results for a single file"""
        print(f"\n{path}")
        print("-" * len(path))

        if not diagnostics:
            print("  No issues found")
            return

        for d in diagnostics:
            severity = d.get('severity', 'info').upper()
            line = d.get('line', 0)
            col = d.get('col', 0)
            msg = d.get('message', '')
            code = d.get('code', '')

            prefix = "E" if severity == 'ERROR' else "W" if severity == 'WARNING' else "I"
            print(f"  {prefix} {line}:{col} [{code}] {msg}")

    def analyze(self, file_paths: List[str], show_callgraph: bool = False) -> Dict[str, Any]:
        """Analyze one or more HTN files"""
        results = {}
        invariants = get_enabled_invariants()

        for path in file_paths:
            full_path = self.resolve_path(path)
            try:
                result = analyze_file(full_path, invariants)
                results[path] = result

                if not self.json_output:
                    self._print_analysis_results(path, result, show_callgraph)

            except FileNotFoundError:
                results[path] = {'error': 'File not found'}
                if not self.json_output:
                    print(f"ERROR: File not found: {path}")
            except Exception as e:
                results[path] = {'error': str(e)}
                if not self.json_output:
                    print(f"ERROR: {path}: {e}")

        if self.json_output:
            print(json.dumps({'results': results}, indent=2))

        return results

    def _print_analysis_results(self, path: str, result: Dict, show_callgraph: bool):
        """Print analysis results for a single file"""
        print(f"\n{'='*60}")
        print(f"Analysis: {path}")
        print("=" * 60)

        stats = result.get('stats', {})
        print(f"\nStatistics:")
        print(f"  Methods:    {stats.get('methods', 0)}")
        print(f"  Operators:  {stats.get('operators', 0)}")
        print(f"  Facts:      {stats.get('facts', 0)}")
        print(f"  Goals:      {stats.get('goals', 0)}")
        print(f"  Reachable:  {stats.get('reachable', 0)}")
        print(f"  Unreachable: {stats.get('unreachable', 0)}")
        print(f"  Cycles:     {stats.get('cycles', 0)}")

        # Show goals
        goals = result.get('goals', [])
        if goals:
            print(f"\nGoals: {', '.join(goals)}")

        # Show cycles
        cycles = result.get('cycles', [])
        if cycles:
            print(f"\nCycles detected:")
            for cycle in cycles:
                print(f"  {' -> '.join(cycle)}")

        # Show unreachable
        unreachable = result.get('unreachable', [])
        if unreachable:
            print(f"\nUnreachable code:")
            for item in unreachable:
                print(f"  {item}")

        # Show invariant violations
        violations = result.get('invariant_violations', [])
        if violations:
            print(f"\nInvariant violations:")
            for v in violations:
                print(f"  [{v.get('invariant')}] {v.get('operator')}: {v.get('message')}")

        # Show call graph
        if show_callgraph:
            print(f"\nCall Graph:")
            nodes = result.get('nodes', {})
            for key, node in nodes.items():
                node_type = node.get('type', 'unknown')
                calls = node.get('calls', [])
                if calls:
                    print(f"  {key} ({node_type}) -> {', '.join(calls)}")

        # Show diagnostics
        diagnostics = result.get('diagnostics', [])
        if diagnostics:
            print(f"\nDiagnostics:")
            for d in diagnostics:
                severity = d.get('severity', 'info').upper()
                line = d.get('line', 0)
                msg = d.get('message', '')
                code = d.get('code', '')
                print(f"  {severity[0]} {line}: [{code}] {msg}")

    def batch(self, directory: str, pattern: str = "*.htn") -> Dict[str, Any]:
        """Analyze all HTN files in a directory"""
        full_dir = self.resolve_path(directory)
        file_pattern = os.path.join(full_dir, pattern)
        files = glob.glob(file_pattern)

        if not files:
            if not self.json_output:
                print(f"No files matching {pattern} in {directory}")
            return {'error': 'No files found'}

        # Make paths relative for cleaner output
        rel_files = [os.path.relpath(f, self.project_root) for f in files]
        return self.analyze(rel_files)

    def invariants(self, action: str = 'list', invariant_id: str = None,
                   enabled: bool = None, config: Dict = None) -> Dict[str, Any]:
        """Manage invariants"""
        registry = get_registry()

        if action == 'list':
            result = registry.to_dict()
            if not self.json_output:
                print("\nAvailable Invariants:")
                print("-" * 40)
                for inv in result['invariants']:
                    status = "ON" if inv['enabled'] else "OFF"
                    print(f"  [{status}] {inv['id']}: {inv['name']}")
                    print(f"        {inv['description']}")
            else:
                print(json.dumps(result, indent=2))
            return result

        elif action == 'enable' and invariant_id:
            registry.enable(invariant_id, enabled if enabled is not None else True)
            if not self.json_output:
                status = "enabled" if enabled else "disabled"
                print(f"Invariant '{invariant_id}' {status}")
            return {'status': 'updated'}

        elif action == 'configure' and invariant_id and config:
            registry.configure(invariant_id, config)
            if not self.json_output:
                print(f"Invariant '{invariant_id}' configured")
            return {'status': 'configured'}

        return {'error': 'Invalid action'}


def main():
    parser = argparse.ArgumentParser(
        description='HTN Tools - Command-line HTN analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lint a single file
  python htn_tools.py lint Examples/Taxi.htn

  # Lint all files in ErrorTests
  python htn_tools.py lint Examples/ErrorTests/*.htn

  # Analyze with call graph
  python htn_tools.py analyze Examples/Game.htn --callgraph

  # Batch analyze a directory
  python htn_tools.py batch Examples/

  # List invariants
  python htn_tools.py invariants list

  # Enable an invariant
  python htn_tools.py invariants enable single_position

  # JSON output
  python htn_tools.py analyze Examples/Taxi.htn --json
"""
    )

    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Lint command
    lint_parser = subparsers.add_parser('lint', help='Lint HTN files')
    lint_parser.add_argument('files', nargs='+', help='Files to lint')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Semantic analysis')
    analyze_parser.add_argument('files', nargs='+', help='Files to analyze')
    analyze_parser.add_argument('--callgraph', '-c', action='store_true',
                                help='Show call graph')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch analyze directory')
    batch_parser.add_argument('directory', help='Directory to analyze')
    batch_parser.add_argument('--pattern', '-p', default='*.htn',
                              help='File pattern (default: *.htn)')

    # Invariants command
    inv_parser = subparsers.add_parser('invariants', help='Manage invariants')
    inv_parser.add_argument('action', choices=['list', 'enable', 'disable', 'configure'],
                           help='Action to perform')
    inv_parser.add_argument('invariant_id', nargs='?', help='Invariant ID')
    inv_parser.add_argument('--config', '-c', type=json.loads,
                           help='Configuration as JSON')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    tools = HtnTools(verbose=args.verbose, json_output=args.json)

    if args.command == 'lint':
        results = tools.lint(args.files)
        # Return non-zero if errors found
        total_errors = sum(r.get('error_count', 0) for r in results.values()
                          if isinstance(r, dict) and 'error_count' in r)
        return 1 if total_errors > 0 else 0

    elif args.command == 'analyze':
        tools.analyze(args.files, show_callgraph=args.callgraph)
        return 0

    elif args.command == 'batch':
        tools.batch(args.directory, pattern=args.pattern)
        return 0

    elif args.command == 'invariants':
        if args.action == 'enable':
            tools.invariants('enable', args.invariant_id, enabled=True)
        elif args.action == 'disable':
            tools.invariants('enable', args.invariant_id, enabled=False)
        elif args.action == 'configure':
            tools.invariants('configure', args.invariant_id, config=args.config)
        else:
            tools.invariants('list')
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
