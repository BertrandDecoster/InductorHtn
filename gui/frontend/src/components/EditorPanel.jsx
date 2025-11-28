import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import axios from 'axios'
import './EditorPanel.css'

const API_BASE = 'http://localhost:5000'

function EditorPanel({ sessionId, currentFile, onFileLoad }) {
  const [content, setContent] = useState('// Select a file to start editing')
  const [files, setFiles] = useState([])
  const [isDirty, setIsDirty] = useState(false)

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
    } catch (err) {
      console.error('Failed to load file content:', err)
      setContent(`// Error loading file: ${err.message}`)
    }
  }

  const handleEditorChange = (value) => {
    setContent(value)
    setIsDirty(true)
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
          onChange={handleEditorChange}
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
