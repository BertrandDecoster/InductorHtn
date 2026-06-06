# Web IDE (GUI)

How to run the InductorHTN web IDE, plus the backend and frontend architecture.

## InductorHTN IDE

Web-based IDE with Monaco Editor and tree visualization.

## Quick Start

### Backend
```bash
cd gui/backend
pip install -r requirements.txt
python app.py
```
Runs on http://localhost:5000

### Frontend
```bash
cd gui/frontend
npm install
npm run dev
```
Runs on http://localhost:5173

## Usage

1. Open http://localhost:5173
2. Select file from dropdown (e.g., Taxi.htn)
3. Edit in Monaco editor
4. Click **Save & Reload**
5. Enter query (e.g., `at(?where).`)
6. Click **Execute**

## Troubleshooting

### "Could not import indhtnpy module"
Copy the library to Python path:
```bash
# Windows
copy build\Release\indhtnpy.dll src\Python\

# macOS
cp build/libindhtnpy.dylib /usr/local/lib/
```

### Port already in use
Edit port in:
- Backend: `app.py` line with `app.run()`
- Frontend: `vite.config.js` server.port

### Node/Python version
- Node 18+ required
- Python 3.7+ required

---

## GUI Backend

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
| `/api/plan/timeline` | POST | Step-by-step state evolution for a plan (state diff per operator) |
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

---

## GUI Frontend

React-based web IDE with Monaco Editor and tree visualization.

## Architecture

```
gui/frontend/
├── src/
│   ├── App.jsx              # Main app with 3-panel layout
│   ├── components/
│   │   ├── EditorPanel.jsx  # Monaco editor (left)
│   │   ├── TreePanel.jsx    # Tree visualization (middle)
│   │   └── QueryPanel.jsx   # Query interface (right)
│   └── index.css
├── package.json
└── vite.config.js
```

## Key Components

### EditorPanel.jsx
- Monaco Editor integration via `@monaco-editor/react`
- File selector dropdown
- Save & Reload functionality
- Dirty state indicator (unsaved changes)

### TreePanel.jsx
- Custom tree visualization (collapsible nodes)
- Color-coded status (success=green, failure=red)
- Variable bindings display
- Supports HTN decomposition trees and Prolog result trees

### QueryPanel.jsx
- Query input field
- Execute button (Enter to submit)
- Results display with variable bindings
- Query history (last 10)
- Current state (facts) display

## Technology Stack

- **React 18** - Component framework
- **Vite** - Build tool and dev server
- **@monaco-editor/react** - VS Code editor component
- **react-resizable-panels** - 3-panel layout
- **axios** - HTTP client
- **@mui/material** - Material UI components
- **@emotion/react** - CSS-in-JS styling

## Adding New Components

1. Create component in `src/components/`:
```jsx
import React from 'react';
import './NewComponent.css';

export default function NewComponent({ prop1, prop2 }) {
  return <div className="new-component">...</div>;
}
```

2. Import in `App.jsx` and add to layout

## Vite Configuration

`vite.config.js` sets up:
- Dev server on port 5173
- Proxy to backend (port 5000)
- React plugin

## API Communication

All API calls go through axios to backend:
```javascript
import axios from 'axios';

const response = await axios.post('/api/query/execute', {
  sessionId: sessionId,
  query: queryText
});
```

## Styling

- CSS files per component
- Global styles in `index.css`
- Resizable panels via react-resizable-panels

## Hot Reload

Vite provides instant HMR - changes appear immediately in browser.
