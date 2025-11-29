import { useState, useEffect } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import axios from 'axios'
import EditorPanel from './components/EditorPanel'
import TreePanel from './components/TreePanel'
import QueryPanel from './components/QueryPanel'
import './App.css'

const API_BASE = 'http://localhost:5000'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentFile, setCurrentFile] = useState(null)
  const [treeData, setTreeData] = useState(null)
  const [queryResults, setQueryResults] = useState(null)
  const [stateFacts, setStateFacts] = useState([])
  const [solutions, setSolutions] = useState([])

  // Initialize session on mount and load Game.htn by default
  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await axios.post(`${API_BASE}/api/session/create`)
        const newSessionId = response.data.session_id
        setSessionId(newSessionId)

        // Auto-load Game.htn
        try {
          await axios.post(`${API_BASE}/api/file/load`, {
            session_id: newSessionId,
            file_path: 'Examples/Game.htn'
          })
          setCurrentFile('Examples/Game.htn')

          // Get initial state facts
          const stateResponse = await axios.post(`${API_BASE}/api/state/get`, {
            session_id: newSessionId
          })
          setStateFacts(stateResponse.data.facts || [])
        } catch (loadErr) {
          console.error('Failed to auto-load Game.htn:', loadErr)
        }

        setLoading(false)
      } catch (err) {
        setError('Failed to initialize session: ' + err.message)
        setLoading(false)
      }
    }

    initSession()
  }, [])

  const handleFileLoad = async (filePath) => {
    try {
      setLoading(true)
      setError(null)

      // Load file into planner
      await axios.post(`${API_BASE}/api/file/load`, {
        session_id: sessionId,
        file_path: filePath
      })

      setCurrentFile(filePath)
      setLoading(false)

      // Refresh state facts
      await refreshState()
    } catch (err) {
      setError('Failed to load file: ' + err.message)
      setLoading(false)
    }
  }

  const handleQueryExecute = async (query) => {
    try {
      setLoading(true)
      setError(null)

      const response = await axios.post(`${API_BASE}/api/query/execute`, {
        session_id: sessionId,
        query: query
      })

      setQueryResults(response.data)
      setTreeData(response.data.tree)  // Single tree for Prolog
      setSolutions([])  // Clear HTN solutions
      setLoading(false)

      // Refresh state facts
      await refreshState()
    } catch (err) {
      setError('Query failed: ' + (err.response?.data?.error || err.message))
      setLoading(false)
    }
  }

  const handleHtnExecute = async (query) => {
    try {
      setLoading(true)
      setError(null)

      const response = await axios.post(`${API_BASE}/api/htn/execute`, {
        session_id: sessionId,
        query: query
      })

      setSolutions(response.data.solutions)
      setTreeData(response.data.trees)  // Array of trees for HTN
      setQueryResults({
        solutions: response.data.solutions,
        total_count: response.data.total_count
      })
      setLoading(false)

      // Refresh state facts
      await refreshState()
    } catch (err) {
      setError('HTN planning failed: ' + (err.response?.data?.error || err.message))
      setLoading(false)
    }
  }

  const refreshState = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/state/get`, {
        session_id: sessionId
      })
      setStateFacts(response.data.facts)
    } catch (err) {
      console.error('Failed to refresh state:', err)
    }
  }

  if (loading && !sessionId) {
    return (
      <div style={{ padding: '20px' }}>
        <h2>Initializing InductorHTN IDE...</h2>
        <p>Creating session...</p>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>InductorHTN IDE</h1>
        {currentFile && <span className="current-file">{currentFile}</span>}
        {error && <div className="error-banner">{error}</div>}
      </header>

      <PanelGroup direction="horizontal" className="panel-group">
        {/* Left Panel - Editor */}
        <Panel defaultSize={33} minSize={20}>
          <EditorPanel
            sessionId={sessionId}
            currentFile={currentFile}
            onFileLoad={handleFileLoad}
          />
        </Panel>

        <PanelResizeHandle className="resize-handle" />

        {/* Middle Panel - Computation Tree */}
        <Panel defaultSize={34} minSize={20}>
          <TreePanel
            treeData={treeData}
            solutions={solutions}
          />
        </Panel>

        <PanelResizeHandle className="resize-handle" />

        {/* Right Panel - Query Interface */}
        <Panel defaultSize={33} minSize={20}>
          <QueryPanel
            onQueryExecute={handleQueryExecute}
            onHtnExecute={handleHtnExecute}
            queryResults={queryResults}
            stateFacts={stateFacts}
            loading={loading}
          />
        </Panel>
      </PanelGroup>
    </div>
  )
}

export default App
