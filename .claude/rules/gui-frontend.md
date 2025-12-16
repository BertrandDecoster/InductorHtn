---
description: GUI frontend React components and Vite setup
globs: gui/frontend/**
---

# GUI Frontend

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
- Tree visualization via `react-arborist`
- Collapsible nodes
- Color-coded status (success=green, failure=red)
- Variable bindings display

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
- **react-arborist** - Tree visualization
- **react-resizable-panels** - 3-panel layout
- **axios** - HTTP client

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
