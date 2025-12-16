import { useState, useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'
import axios from 'axios'
import './EditorPanel.css'

const API_BASE = 'http://localhost:5000'

function EditorPanel({ sessionId, currentFile, onFileLoad }) {
  const [content, setContent] = useState('// Select a file to start editing')
  const [files, setFiles] = useState([])
  const [isDirty, setIsDirty] = useState(false)

  // Refs for Monaco lint integration
  const monacoRef = useRef(null)
  const editorRef = useRef(null)
  const lintTimeoutRef = useRef(null)

  useEffect(() => {
    // Load available files list
    const loadFiles = async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/file/list`)
        setFiles(response.data.files)
      } catch (err) {
        console.error('Failed to load files:', err)
      }
    }
    loadFiles()
  }, [])

  useEffect(() => {
    // Load file content when currentFile changes
    if (currentFile) {
      loadFileContent(currentFile)
    }
  }, [currentFile])

  const loadFileContent = async (filePath) => {
    try {
      const response = await axios.post(`${API_BASE}/api/file/content`, {
        file_path: filePath
      })
      setContent(response.data.content)
      setIsDirty(false)
      // Lint the loaded content
      setTimeout(() => lintContent(response.data.content), 100)
    } catch (err) {
      console.error('Failed to load file content:', err)
      setContent(`// Error loading file: ${err.message}`)
    }
  }

  const handleEditorChange = (value) => {
    setContent(value)
    setIsDirty(true)
  }

  // Lint content and show Monaco markers
  const lintContent = async (value) => {
    if (!monacoRef.current || !editorRef.current) return

    try {
      const response = await axios.post(`${API_BASE}/api/lint`, {
        content: value
      })

      const markers = (response.data.diagnostics || []).map(d => ({
        startLineNumber: d.line,
        startColumn: d.col,
        endLineNumber: d.line,
        endColumn: d.col + (d.length || 1),
        message: d.message,
        severity: d.severity === 'error'
          ? monacoRef.current.MarkerSeverity.Error
          : monacoRef.current.MarkerSeverity.Warning
      }))

      monacoRef.current.editor.setModelMarkers(
        editorRef.current.getModel(),
        'htn-linter',
        markers
      )
    } catch (err) {
      console.error('Lint failed:', err)
    }
  }

  const handleSaveFile = async () => {
    if (!currentFile) {
      alert('No file selected')
      return
    }

    try {
      await axios.post(`${API_BASE}/api/file/save`, {
        file_path: currentFile,
        content: content
      })
      setIsDirty(false)

      // Reload file into planner
      await onFileLoad(currentFile)
      alert('File saved and reloaded!')
    } catch (err) {
      alert('Failed to save file: ' + err.message)
    }
  }

  const handleFileSelect = (filePath) => {
    if (isDirty) {
      const confirm = window.confirm('You have unsaved changes. Continue without saving?')
      if (!confirm) return
    }
    onFileLoad(filePath)
  }

  return (
    <div className="panel-container">
      <div className="panel-header">
        Editor
        {isDirty && <span className="dirty-indicator">●</span>}
      </div>

      <div className="editor-toolbar">
        <select
          className="file-selector"
          value={currentFile || ''}
          onChange={(e) => handleFileSelect(e.target.value)}
        >
          <option value="">Select a file...</option>
          {files.map((file) => (
            <option key={file.path} value={file.path}>
              {file.name}
            </option>
          ))}
        </select>

        <button
          className="save-button"
          onClick={handleSaveFile}
          disabled={!isDirty || !currentFile}
        >
          Save & Reload
        </button>
      </div>

      <div className="editor-container">
        <Editor
          height="100%"
          defaultLanguage="prolog"
          theme="vs-dark"
          value={content}
          onMount={(editor, monaco) => {
            editorRef.current = editor
            monacoRef.current = monaco
          }}
          onChange={(value) => {
            handleEditorChange(value)
            // Debounced lint
            clearTimeout(lintTimeoutRef.current)
            lintTimeoutRef.current = setTimeout(() => lintContent(value), 500)
          }}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true
          }}
        />
      </div>
    </div>
  )
}

export default EditorPanel
