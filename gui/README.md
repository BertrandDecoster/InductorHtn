# InductorHTN IDE - Web-Based GUI

A modern, web-based IDE for InductorHTN with Monaco Editor, computation tree visualization, and an intuitive 3-panel layout.

## Features

- **Monaco Editor** - VS Code-quality editor with syntax highlighting for .htn files
- **Computation Tree Visualization** - Collapsible tree view showing Prolog resolution steps
- **3-Panel Layout** - Resizable panels for editing, visualization, and query interface
- **File Management** - Load, edit, and save .htn files
- **Query Interface** - Execute Prolog queries and view results
- **State Display** - View current facts in the knowledge base

## Prerequisites

### Backend Requirements
- Python 3.7 or higher
- InductorHTN Python bindings (`indhtnpy.dll` on Windows, `libindhtnpy.dylib` on macOS, `libindhtnpy.so` on Linux)

### Frontend Requirements
- Node.js 18+ and npm

## Installation

### Step 1: Setup Backend

```bash
cd gui/backend

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Verify Python Bindings

Make sure the InductorHTN Python bindings are accessible:

**Windows:**
```bash
# The indhtnpy.dll should be in build/Debug/ or build/Release/
# You may need to copy it or add it to PATH
```

**macOS/Linux:**
```bash
# The libindhtnpy.dylib (macOS) or libindhtnpy.so (Linux) should be available
# You may need to copy it to /usr/local/lib or set LD_LIBRARY_PATH
```

### Step 3: Setup Frontend

```bash
cd gui/frontend

# Install dependencies
npm install
```

## Running the IDE

You need to run both the backend and frontend servers:

### Terminal 1: Start Backend Server

```bash
cd gui/backend
python app.py
```

The backend server will start on `http://localhost:5000`

### Terminal 2: Start Frontend Dev Server

```bash
cd gui/frontend
npm run dev
```

The frontend will start on `http://localhost:5173`

### Step 4: Open in Browser

Navigate to `http://localhost:5173` in your web browser.

## Usage Guide

### 1. Loading a File

1. Click the dropdown in the **Editor Panel** (left)
2. Select a file from the Examples folder (e.g., `Taxi.htn`)
3. The file will load into both the editor and the planner

### 2. Editing Files

1. Make changes in the Monaco editor
2. The file tab will show a dot (●) indicating unsaved changes
3. Click **Save & Reload** to save and recompile the file

### 3. Executing Queries

1. In the **Query Panel** (right), enter a Prolog query
2. Example queries:
   - `at(?where).` - Find all locations
   - `tile(?x, ?y).` - Find all tiles
   - `have-cash(?amount).` - Check cash amount
3. Click **Execute** or press Enter
4. Results will appear below the query input
5. The computation tree will display in the middle panel

### 4. Viewing the Computation Tree

- The **Tree Panel** (middle) shows the resolution process
- Click nodes to expand/collapse
- Green border = success
- Red border = failure
- Variable bindings are shown for each solution node

### 5. Query History

- Recent queries are saved in the **Query History** section
- Click any historical query to reuse it

### 6. Current State

- The **Current State** section shows all facts in the knowledge base
- This updates after executing queries

## Project Structure

```
gui/
├── backend/
│   ├── app.py                 # Flask REST API server
│   ├── htn_service.py         # HTN planner wrapper
│   └── requirements.txt       # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── App.jsx            # Main application
    │   ├── components/
    │   │   ├── EditorPanel.jsx   # Monaco editor (left panel)
    │   │   ├── TreePanel.jsx      # Tree visualization (middle)
    │   │   └── QueryPanel.jsx     # Query interface (right)
    │   └── index.css
    ├── package.json
    └── vite.config.js
```

## API Endpoints

The backend exposes these REST endpoints:

- `POST /api/session/create` - Create new planner session
- `POST /api/file/load` - Load .htn file into planner
- `POST /api/file/save` - Save edited file
- `POST /api/file/content` - Get file content for editor
- `GET /api/file/list` - List available .htn files
- `POST /api/query/execute` - Execute Prolog query
- `POST /api/state/get` - Get current facts
- `GET /health` - Health check

## Troubleshooting

### "Could not import indhtnpy module"

**Solution:** Make sure the Python bindings are built and accessible:

1. Build InductorHTN:
   ```bash
   mkdir build && cd build
   cmake ../src
   cmake --build . --config Release
   ```

2. Copy the library to the Python directory:
   ```bash
   # Windows
   copy build\Release\indhtnpy.dll src\Python\

   # macOS
   cp build/libindhtnpy.dylib src/Python/

   # Linux
   cp build/libindhtnpy.so src/Python/
   ```

### Backend Won't Start

**Check Python version:**
```bash
python --version  # Should be 3.7+
```

**Reinstall dependencies:**
```bash
cd gui/backend
pip install --upgrade -r requirements.txt
```

### Frontend Won't Build

**Check Node version:**
```bash
node --version  # Should be 18+
```

**Clear cache and reinstall:**
```bash
cd gui/frontend
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

If ports 5000 or 5173 are already in use:

**Backend:** Edit `app.py` and change the port:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

**Frontend:** Edit `vite.config.js`:
```javascript
server: {
  port: 5174  // Change port
}
```

## Development

### Hot Reload

Both backend and frontend support hot reload:

- **Backend:** Flask auto-reloads when you edit Python files
- **Frontend:** Vite provides instant HMR for React components

### Adding Custom Syntax Highlighting

The Monaco editor currently uses generic Prolog syntax. To add custom `.htn` syntax:

1. Edit `EditorPanel.jsx`
2. Add a custom language definition using Monaco's `registerLanguage` API
3. Define tokens for HTN-specific keywords (`if`, `do`, `del`, `add`, etc.)

## Future Enhancements

- [ ] Real computation tree capture from C++ (currently using placeholder)
- [ ] HTN planning visualization (method decomposition tree)
- [ ] State diff viewer (before/after operators)
- [ ] Query debugger with step-through execution
- [ ] Export plans as images/PDFs
- [ ] Dark/light theme toggle
- [ ] Multi-file project support

## License

Same as InductorHTN core project.

## Contributing

Contributions welcome! Please ensure:
1. Backend tests pass
2. Frontend builds without errors
3. Code follows existing style conventions
