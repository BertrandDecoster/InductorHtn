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

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# In-memory session storage
sessions = {}

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
    """List available .htn files in the Examples directory"""
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        examples_dir = os.path.join(project_root, 'Examples')

        files = []
        if os.path.exists(examples_dir):
            for filename in os.listdir(examples_dir):
                if filename.endswith('.htn'):
                    files.append({
                        'name': filename,
                        'path': f'Examples/{filename}'
                    })

        return jsonify({'files': files})
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

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'sessions': len(sessions)})

if __name__ == '__main__':
    print("Starting InductorHTN IDE Backend Server...")
    print("Server will be available at http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, host='0.0.0.0', port=5000)
