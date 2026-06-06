"""
InductorHTN IDE - Flask Backend
Provides REST API for the web-based IDE interface
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import os
import sys

# Add parent directory to path to import indhtnpy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/Python'))

from htn_service import HtnService
from htn_linter import lint_htn, lint_file
from htn_analyzer import analyze_htn, analyze_file
from invariants import get_registry, get_enabled_invariants

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# In-memory session storage
sessions = {}

# --- HTN source folder ------------------------------------------------------
# The editor's file dropdown lists every .htn in a chosen folder. The choice is
# persisted (so it survives restarts) and appended to a log. Defaults to the
# repo's Examples/ directory (Taxi.htn etc.).
import json
import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DEFAULT_HTN_FOLDER = os.path.join(PROJECT_ROOT, 'Examples')
FOLDER_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'htn_folder.json')
FOLDER_LOG_PATH = os.path.join(os.path.dirname(__file__), 'htn_folder.log')


def get_current_folder():
    """The folder whose .htn files populate the dropdown. Falls back to Examples."""
    try:
        with open(FOLDER_CONFIG_PATH, 'r', encoding='utf-8') as f:
            folder = json.load(f).get('folder')
        if folder and os.path.isdir(folder):
            return folder
    except (FileNotFoundError, ValueError, OSError):
        pass
    return DEFAULT_HTN_FOLDER


def set_current_folder(folder):
    """Persist + log a new source folder. Returns its absolute path."""
    folder = os.path.abspath(os.path.expanduser(folder))
    if not os.path.isdir(folder):
        raise NotADirectoryError(folder)
    with open(FOLDER_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({'folder': folder}, f, indent=2)
    with open(FOLDER_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now().isoformat()}\t{folder}\n")
    return folder


def list_htn_files(folder):
    """Sorted [{name, path}] of *.htn in folder, with absolute paths."""
    files = []
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            if name.endswith('.htn'):
                files.append({'name': name, 'path': os.path.join(folder, name)})
    return files

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new HTN planner session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = HtnService(debug=False)
    return jsonify({
        'session_id': session_id,
        'status': 'created'
    })

@app.route('/api/session/delete/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete an existing session"""
    if session_id in sessions:
        del sessions[session_id]
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/file/load', methods=['POST'])
def load_file():
    """Load a .htn file into the planner"""
    data = request.json
    session_id = data.get('session_id')
    file_path = data.get('file_path')

    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    service = sessions[session_id]
    success, error = service.load_file(file_path)

    if success:
        return jsonify({
            'status': 'loaded',
            'file_path': file_path
        })
    else:
        return jsonify({'error': error}), 400

@app.route('/api/file/content', methods=['POST'])
def get_file_content():
    """Get the content of a file for the Monaco editor"""
    data = request.json
    file_path = data.get('file_path')

    try:
        # Resolve relative to project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        full_path = os.path.join(project_root, file_path)

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({
            'content': content,
            'file_path': file_path
        })
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/save', methods=['POST'])
def save_file():
    """Save edited content back to a file"""
    data = request.json
    file_path = data.get('file_path')
    content = data.get('content')

    try:
        # Resolve relative to project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        full_path = os.path.join(project_root, file_path)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({
            'status': 'saved',
            'file_path': file_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/list', methods=['GET'])
def list_files():
    """List available .htn files in the current source folder."""
    try:
        folder = get_current_folder()
        return jsonify({'folder': folder, 'files': list_htn_files(folder)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/folder', methods=['GET'])
def get_folder():
    """Return the current source folder and its .htn files."""
    folder = get_current_folder()
    return jsonify({'folder': folder, 'files': list_htn_files(folder)})


@app.route('/api/folder', methods=['POST'])
def set_folder():
    """Set the source folder. Body: { "folder": "/abs/or/~/path" }."""
    data = request.json or {}
    folder = data.get('folder')
    if not folder:
        return jsonify({'error': 'Must provide "folder"'}), 400
    try:
        folder = set_current_folder(folder)
        return jsonify({'folder': folder, 'files': list_htn_files(folder)})
    except NotADirectoryError:
        return jsonify({'error': f'Not a directory: {folder}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/folder/browse', methods=['POST'])
def browse_folder():
    """Server-side directory browser for the 'Change folder' picker.

    Body: { "path": "/abs/path" }  (defaults to the current folder)
    Returns the directory's subfolders and how many .htn files it holds.
    """
    data = request.json or {}
    path = data.get('path') or get_current_folder()
    try:
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(path):
            return jsonify({'error': f'Not a directory: {path}'}), 400

        dirs = []
        htn_count = 0
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if name.startswith('.'):
                continue
            if os.path.isdir(full):
                dirs.append(name)
            elif name.endswith('.htn'):
                htn_count += 1

        parent = os.path.dirname(path)
        return jsonify({
            'path': path,
            'parent': parent if parent != path else None,
            'dirs': dirs,
            'htnCount': htn_count,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query/execute', methods=['POST'])
def execute_query():
    """Execute a Prolog query and return results + computation tree"""
    data = request.json
    session_id = data.get('session_id')
    query = data.get('query')

    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    service = sessions[session_id]
    result = service.execute_prolog_query(query)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)

@app.route('/api/htn/execute', methods=['POST'])
def execute_htn():
    """Execute an HTN planning query and return plans + decomposition trees"""
    data = request.json
    session_id = data.get('session_id')
    query = data.get('query')  # e.g., "travel-to(park)."

    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    service = sessions[session_id]
    result = service.execute_htn_query(query)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)

@app.route('/api/state/get', methods=['POST'])
def get_state():
    """Get the current state (facts) from the planner"""
    data = request.json
    session_id = data.get('session_id')

    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    service = sessions[session_id]
    facts = service.get_state_facts()

    return jsonify({'facts': facts})

@app.route('/api/state/diff', methods=['POST'])
def get_state_diff():
    """Get the diff between initial state and a solution's final state"""
    data = request.json
    session_id = data.get('session_id')
    solution_index = data.get('solution_index', 0)

    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    service = sessions[session_id]
    diff = service.get_facts_diff(solution_index)

    return jsonify(diff)

@app.route('/api/plan/timeline', methods=['POST'])
def get_plan_timeline():
    """
    Get step-by-step state evolution for a plan.

    Returns a timeline showing the state after each operator, useful for
    debugging and visualization. Shows initial state, and state diff per step.

    Body: { "session_id": "...", "goal": "travel-to(park)." }
    Response: {
        "timeline": [
            {"step": 0, "operator": null, "state": [...], "added": [], "removed": []},
            {"step": 1, "operator": "walk(downtown, park)", "added": ["at(park)"], "removed": ["at(downtown)"]}
        ],
        "operators": [...],
        "total_steps": N
    }
    """
    data = request.json
    session_id = data.get('session_id')
    goal = data.get('goal')

    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    if not goal:
        return jsonify({'error': 'Goal is required'}), 400

    service = sessions[session_id]
    timeline = service.get_plan_timeline(goal)

    if 'error' in timeline:
        return jsonify(timeline), 400

    return jsonify(timeline)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'sessions': len(sessions)})


@app.route('/api/lint', methods=['POST'])
def lint_content():
    """
    Lint HTN content and return diagnostics

    Body: { "content": "..." } or { "file_path": "..." }
    Response: {
        "diagnostics": [
            {"line": 5, "col": 12, "severity": "error", "message": "...", "length": 1, "code": "SYN001"}
        ]
    }
    """
    data = request.json

    try:
        if 'content' in data:
            diagnostics = lint_htn(data['content'])
        elif 'file_path' in data:
            # Resolve relative to project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            full_path = os.path.join(project_root, data['file_path'])
            diagnostics = lint_file(full_path)
        else:
            return jsonify({'error': 'Must provide either "content" or "file_path"'}), 400

        return jsonify({'diagnostics': diagnostics})

    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lint/batch', methods=['POST'])
def lint_batch():
    """
    Lint multiple HTN files and return aggregated diagnostics

    Body: { "file_paths": ["Examples/Taxi.htn", "Examples/Game.htn"] }
    Response: {
        "results": {
            "Examples/Taxi.htn": { "diagnostics": [...] },
            "Examples/Game.htn": { "diagnostics": [...] }
        }
    }
    """
    data = request.json
    file_paths = data.get('file_paths', [])

    if not file_paths:
        return jsonify({'error': 'Must provide "file_paths" array'}), 400

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    results = {}

    for file_path in file_paths:
        try:
            full_path = os.path.join(project_root, file_path)
            diagnostics = lint_file(full_path)
            results[file_path] = {'diagnostics': diagnostics}
        except FileNotFoundError:
            results[file_path] = {'error': 'File not found'}
        except Exception as e:
            results[file_path] = {'error': str(e)}

    return jsonify({'results': results})


@app.route('/api/analyze', methods=['POST'])
def analyze_content():
    """
    Perform semantic analysis on HTN content

    Body: { "content": "..." } or { "file_path": "..." }
    Response: {
        "nodes": {...},
        "edges": [...],
        "goals": [...],
        "reachable": [...],
        "unreachable": [...],
        "cycles": [...],
        "diagnostics": [...],
        "initial_facts": [...],
        "state_changes": {...},
        "invariant_violations": [...],
        "stats": {...}
    }
    """
    data = request.json

    try:
        # Get enabled invariants
        invariants = get_enabled_invariants()

        if 'content' in data:
            result = analyze_htn(data['content'], invariants)
        elif 'file_path' in data:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            full_path = os.path.join(project_root, data['file_path'])
            result = analyze_file(full_path, invariants)
        else:
            return jsonify({'error': 'Must provide either "content" or "file_path"'}), 400

        return jsonify(result)

    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/batch', methods=['POST'])
def analyze_batch():
    """
    Analyze multiple HTN files

    Body: { "file_paths": ["Examples/Taxi.htn", "Examples/Game.htn"] }
    Response: {
        "results": {
            "Examples/Taxi.htn": { ... },
            "Examples/Game.htn": { ... }
        }
    }
    """
    data = request.json
    file_paths = data.get('file_paths', [])

    if not file_paths:
        return jsonify({'error': 'Must provide "file_paths" array'}), 400

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    invariants = get_enabled_invariants()
    results = {}

    for file_path in file_paths:
        try:
            full_path = os.path.join(project_root, file_path)
            result = analyze_file(full_path, invariants)
            results[file_path] = result
        except FileNotFoundError:
            results[file_path] = {'error': 'File not found'}
        except Exception as e:
            results[file_path] = {'error': str(e)}

    return jsonify({'results': results})


@app.route('/api/invariants', methods=['GET'])
def get_invariants():
    """
    Get all available invariants and their configuration

    Response: {
        "invariants": [...],
        "categories": [...]
    }
    """
    registry = get_registry()
    return jsonify(registry.to_dict())


@app.route('/api/invariants/<invariant_id>/enable', methods=['POST'])
def enable_invariant(invariant_id):
    """
    Enable or disable an invariant

    Body: { "enabled": true/false }
    """
    data = request.json
    enabled = data.get('enabled', True)

    registry = get_registry()
    invariant = registry.get(invariant_id)

    if not invariant:
        return jsonify({'error': f'Invariant {invariant_id} not found'}), 404

    registry.enable(invariant_id, enabled)
    return jsonify({'status': 'updated', 'invariant_id': invariant_id, 'enabled': enabled})


@app.route('/api/invariants/<invariant_id>/configure', methods=['POST'])
def configure_invariant(invariant_id):
    """
    Update configuration for an invariant

    Body: { "config": { ... } }
    """
    data = request.json
    config = data.get('config', {})

    registry = get_registry()
    invariant = registry.get(invariant_id)

    if not invariant:
        return jsonify({'error': f'Invariant {invariant_id} not found'}), 404

    registry.configure(invariant_id, config)
    return jsonify({'status': 'configured', 'invariant_id': invariant_id})


@app.route('/api/callgraph', methods=['POST'])
def get_callgraph():
    """
    Get just the call graph for visualization

    Body: { "content": "..." } or { "file_path": "..." }
    Response: {
        "nodes": [...],
        "edges": [...],
        "stats": {...}
    }
    """
    data = request.json

    try:
        if 'content' in data:
            result = analyze_htn(data['content'])
        elif 'file_path' in data:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            full_path = os.path.join(project_root, data['file_path'])
            result = analyze_file(full_path)
        else:
            return jsonify({'error': 'Must provide either "content" or "file_path"'}), 400

        # Return just call graph data
        return jsonify({
            'nodes': result['nodes'],
            'edges': result['edges'],
            'goals': result['goals'],
            'reachable': result['reachable'],
            'unreachable': result['unreachable'],
            'stats': result['stats']
        })

    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Port 5000 is taken by AirPlay Receiver on macOS, so default to 5001.
    # Override with INDHTN_GUI_BACKEND_PORT to match the frontend proxy.
    port = int(os.environ.get('INDHTN_GUI_BACKEND_PORT', '5001'))
    print("Starting InductorHTN IDE Backend Server...")
    print(f"Server will be available at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    app.run(debug=True, host='0.0.0.0', port=port)
