import { useState, useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'
import axios from 'axios'
import './EditorPanel.css'

// Empty base => relative URLs through the Vite dev proxy (vite.config.js),
// so we never hardcode the backend port (5000 collides with macOS AirPlay).
const API_BASE = ''

function EditorPanel({ sessionId, currentFile, onFileLoad }) {
  const [content, setContent] = useState('// Select a file to start editing')
  const [files, setFiles] = useState([])
  const [folder, setFolder] = useState('')
  const [isDirty, setIsDirty] = useState(false)

  // Folder picker (server-side directory browser) state
  const [browseOpen, setBrowseOpen] = useState(false)
  const [browsePath, setBrowsePath] = useState('')
  const [browseParent, setBrowseParent] = useState(null)
  const [browseDirs, setBrowseDirs] = useState([])
  const [browseHtnCount, setBrowseHtnCount] = useState(0)
  const [browseError, setBrowseError] = useState('')

  // Refs for Monaco lint integration
  const monacoRef = useRef(null)
  const editorRef = useRef(null)
  const lintTimeoutRef = useRef(null)

  useEffect(() => {
    // Load the current source folder and its .htn files
    refreshFolder()
  }, [])

  useEffect(() => {
    // Load file content when currentFile changes
    if (currentFile) {
      loadFileContent(currentFile)
    }
  }, [currentFile])

  const refreshFolder = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/folder`)
      setFolder(response.data.folder || '')
      setFiles(response.data.files || [])
    } catch (err) {
      console.error('Failed to load folder:', err)
    }
  }

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

  // --- Folder picker -------------------------------------------------------

  const browseTo = async (path) => {
    setBrowseError('')
    try {
      const response = await axios.post(`${API_BASE}/api/folder/browse`, { path })
      setBrowsePath(response.data.path)
      setBrowseParent(response.data.parent)
      setBrowseDirs(response.data.dirs || [])
      setBrowseHtnCount(response.data.htnCount || 0)
    } catch (err) {
      setBrowseError(err.response?.data?.error || err.message)
    }
  }

  const openBrowser = () => {
    setBrowseOpen(true)
    browseTo(folder || '')
  }

  const useThisFolder = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/folder`, { folder: browsePath })
      setFolder(response.data.folder || '')
      setFiles(response.data.files || [])
      setBrowseOpen(false)
    } catch (err) {
      setBrowseError(err.response?.data?.error || err.message)
    }
  }

  const joinPath = (base, name) => `${base.replace(/\/$/, '')}/${name}`

  return (
    <div className="panel-container">
      <div className="panel-header">
        Editor
        {isDirty && <span className="dirty-indicator">●</span>}
      </div>

      <div className="folder-bar" title={folder}>
        <span className="folder-icon">📁</span>
        <span className="folder-path">{folder || '(no folder)'}</span>
        <button className="folder-change-button" onClick={openBrowser}>
          Change folder…
        </button>
      </div>

      <div className="editor-toolbar">
        <select
          className="file-selector"
          value={currentFile || ''}
          onChange={(e) => handleFileSelect(e.target.value)}
        >
          <option value="">
            {files.length ? 'Select a file...' : 'No .htn files in this folder'}
          </option>
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

      {browseOpen && (
        <div className="folder-modal-overlay" onClick={() => setBrowseOpen(false)}>
          <div className="folder-modal" onClick={(e) => e.stopPropagation()}>
            <div className="folder-modal-header">Choose a folder</div>
            <div className="folder-modal-path">{browsePath}</div>
            {browseError && <div className="folder-modal-error">{browseError}</div>}
            <ul className="folder-modal-list">
              {browseParent && (
                <li
                  className="folder-modal-entry up"
                  onClick={() => browseTo(browseParent)}
                >
                  ⬆ .. (parent)
                </li>
              )}
              {browseDirs.length === 0 && (
                <li className="folder-modal-empty">(no subfolders)</li>
              )}
              {browseDirs.map((d) => (
                <li
                  key={d}
                  className="folder-modal-entry"
                  onClick={() => browseTo(joinPath(browsePath, d))}
                >
                  📁 {d}
                </li>
              ))}
            </ul>
            <div className="folder-modal-footer">
              <span className="folder-modal-count">
                {browseHtnCount} .htn file{browseHtnCount === 1 ? '' : 's'} here
              </span>
              <div className="folder-modal-actions">
                <button onClick={() => setBrowseOpen(false)}>Cancel</button>
                <button className="primary" onClick={useThisFolder}>
                  Use this folder
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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
