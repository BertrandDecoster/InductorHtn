# InductorHTN IDE

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
