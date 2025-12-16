---
description: GUI backend Flask API and HTN service
globs: gui/backend/**
---

# GUI Backend

Flask-based REST API server for the InductorHTN web IDE.

## Architecture

```
gui/backend/
├── app.py              # Flask REST API server
├── htn_service.py      # HTN planner wrapper
├── htn_parser.py       # HTN parsing utilities
├── htn_analyzer.py     # Semantic analysis
├── htn_linter.py       # Linting and diagnostics
├── failure_analyzer.py # Plan failure analysis
├── invariants.py       # Invariant checking
├── utils.py            # Utility functions
└── requirements.txt    # Python dependencies
```

## Key Components

### app.py - Flask API Server

Main endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/session/create` | POST | Create new planner session |
| `/api/session/delete/<id>` | DELETE | Delete session |
| `/api/file/load` | POST | Load .htn file into planner |
| `/api/file/save` | POST | Save edited file |
| `/api/file/content` | POST | Get file content for editor |
| `/api/file/list` | GET | List available .htn files |
| `/api/query/execute` | POST | Execute Prolog query |
| `/api/htn/execute` | POST | Execute HTN planning query |
| `/api/state/get` | POST | Get current facts |
| `/api/state/diff` | POST | Get state diff after solution |
| `/api/lint` | POST | Run linter on HTN code |
| `/api/lint/batch` | POST | Batch lint multiple files |
| `/api/analyze` | POST | Semantic analysis |
| `/api/analyze/batch` | POST | Batch semantic analysis |
| `/api/invariants` | GET | Get invariant registry |
| `/api/invariants/<id>/enable` | POST | Enable/disable invariant |
| `/api/invariants/<id>/configure` | POST | Configure invariant |
| `/api/callgraph` | POST | Generate call graph |
| `/health` | GET | Health check |

### htn_service.py - HTN Wrapper

Wraps indhtnpy Python bindings:
- `HtnService` class - manages planner instance
- Query execution with result formatting
- JSON result parsing from C++ output

Key methods:
- `__init__(debug)` - Initialize with optional debug mode
- `load_file(file_path)` - Load HTN file
- `execute_prolog_query(query)` - Run Prolog query
- `execute_htn_query(query, enhanced_trace)` - Run HTN query with tracing
- `get_state_facts()` - Get current world state
- `get_solution_facts(index)` - Get facts for solution
- `get_facts_diff(index)` - Get state diff after solution

## Adding New Endpoints

1. Add route in `app.py`:
```python
@app.route('/api/new/endpoint', methods=['POST'])
def new_endpoint():
    data = request.get_json()
    # Process request
    return jsonify({'result': ...})
```

2. If needed, add method to `HtnService` in `htn_service.py`

## Dependencies

```
flask==3.0.0
flask-cors==4.0.0
```

Requires `indhtnpy` module - Python bindings from C++ build.

## Error Handling

- Returns JSON with `error` field on failure
- HTTP 500 for server errors
- HTTP 400 for bad requests

## CORS Configuration

Enabled for localhost development:
```python
CORS(app)  # Allows all origins in development
```

## Session Management

- Sessions are stateful (planner state persists)
- Each session has unique ID
- Session stores loaded files and planner state
