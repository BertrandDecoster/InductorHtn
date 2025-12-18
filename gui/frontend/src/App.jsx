import { useState, useEffect } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import axios from 'axios'
import EditorPanel from './components/EditorPanel'
import TreePanel from './components/TreePanel'
import QueryPanel from './components/QueryPanel'
import './App.css'
import { getLastFile, setLastFile } from './utils/storage'

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
  const [selectedSolution, setSelectedSolution] = useState(0)
  const [factsDiff, setFactsDiff] = useState(null)

  // Initialize session on mount and load Game.htn by default
  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await axios.post(`${API_BASE}/api/session/create`)
        const newSessionId = response.data.session_id
        setSessionId(newSessionId)

        // Auto-load last file or default to Game.htn
        const fileToLoad = getLastFile() || 'Examples/Game.htn'
        try {
          await axios.post(`${API_BASE}/api/file/load`, {
            session_id: newSessionId,
            file_path: fileToLoad
          })
          setCurrentFile(fileToLoad)

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
    console.log('[handleFileLoad] START - filePath:', filePath, 'loading:', loading)

    // Prevent multiple concurrent loads
    if (loading) {
      console.log('[handleFileLoad] BLOCKED - already loading')
      return
    }

    try {
      setLoading(true)
      setError(null)

      // Clear all query-related state before loading new file
      console.log('[handleFileLoad] Clearing state...')
      setQueryResults(null)
      setTreeData(null)
      setSolutions([])
      setSelectedSolution(0)
      setFactsDiff(null)

      // Load file into planner
      console.log('[handleFileLoad] Calling backend /api/file/load...')
      await axios.post(`${API_BASE}/api/file/load`, {
        session_id: sessionId,
        file_path: filePath
      })
      console.log('[handleFileLoad] Backend returned OK')

      setCurrentFile(filePath)
      setLastFile(filePath)  // Save to localStorage for auto-load on next visit
      setLoading(false)

      // Refresh state facts
      console.log('[handleFileLoad] Refreshing state...')
      await refreshState()
      console.log('[handleFileLoad] DONE')
    } catch (err) {
      console.error('[handleFileLoad] ERROR:', err)
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
        pretty_solutions: response.data.pretty_solutions,
        total_count: response.data.total_count
      })
      setSelectedSolution(0)  // Reset to first solution
      setFactsDiff(null)  // Clear facts diff until solution selected
      setLoading(false)

      // Refresh state facts
      await refreshState()

      // Fetch facts diff for first solution if there are solutions
      if (response.data.solutions && response.data.solutions.length > 0) {
        await fetchFactsDiff(0)
      }
    } catch (err) {
      setError('HTN planning failed: ' + (err.response?.data?.error || err.message))
      setLoading(false)
    }
  }

  const fetchFactsDiff = async (solutionIndex) => {
    try {
      const response = await axios.post(`${API_BASE}/api/state/diff`, {
        session_id: sessionId,
        solution_index: solutionIndex
      })
      setFactsDiff(response.data)
    } catch (err) {
      console.error('Failed to fetch facts diff:', err)
      setFactsDiff(null)
    }
  }

  const handleSolutionSelect = async (index) => {
    setSelectedSolution(index)
    await fetchFactsDiff(index)
  }

  const refreshState = async () => {
    console.log('[refreshState] START - sessionId:', sessionId)
    try {
      console.log('[refreshState] Calling /api/state/get...')
      const response = await axios.post(`${API_BASE}/api/state/get`, {
        session_id: sessionId
      })
      console.log('[refreshState] Got response, facts count:', response.data.facts?.length)
      setStateFacts(response.data.facts)
      console.log('[refreshState] DONE')
    } catch (err) {
      console.error('[refreshState] ERROR:', err)
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
            selectedSolution={selectedSolution}
            onSolutionSelect={handleSolutionSelect}
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
            factsDiff={factsDiff}
            selectedSolution={selectedSolution}
            loading={loading}
          />
        </Panel>
      </PanelGroup>
    </div>
  )
}

export default App
