import { useState } from 'react'
import './QueryPanel.css'

function QueryPanel({ onQueryExecute, onHtnExecute, queryResults, stateFacts, loading }) {
  const [query, setQuery] = useState('')
  const [queryHistory, setQueryHistory] = useState([])
  const [mode, setMode] = useState('htn')  // 'prolog' or 'htn'

  const handleExecute = () => {
    if (!query.trim()) return

    if (mode === 'htn') {
      onHtnExecute(query)
    } else {
      onQueryExecute(query)
    }
    setQueryHistory([query, ...queryHistory].slice(0, 10)) // Keep last 10
  }

  const handleHistoryClick = (historicalQuery) => {
    setQuery(historicalQuery)
  }

  return (
    <div className="panel-container">
      <div className="panel-header">Query & State</div>

      <div className="query-panel-content">
        {/* Query Input Section */}
        <section className="query-section">
          {/* Mode toggle */}
          <div className="mode-toggle">
            <button
              className={mode === 'htn' ? 'active' : ''}
              onClick={() => setMode('htn')}
            >
              HTN Plan
            </button>
            <button
              className={mode === 'prolog' ? 'active' : ''}
              onClick={() => setMode('prolog')}
            >
              Prolog Query
            </button>
          </div>

          <label className="section-label">
            {mode === 'htn' ? 'HTN Goal' : 'Prolog Query'}
          </label>
          <div className="query-input-container">
            <input
              type="text"
              className="query-input"
              placeholder={mode === 'htn' ? 'travel-to(park).' : 'at(?where).'}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
              disabled={loading}
            />
            <button
              className="execute-button"
              onClick={handleExecute}
              disabled={loading || !query.trim()}
            >
              {loading ? 'Executing...' : 'Execute'}
            </button>
          </div>
        </section>

        {/* Query Results Section */}
        {queryResults && (
          <section className="results-section">
            <label className="section-label">
              Results: {queryResults.total_count} solution{queryResults.total_count !== 1 ? 's' : ''}
            </label>
            <div className="results-list">
              {queryResults.solutions && queryResults.solutions.length > 0 ? (
                queryResults.solutions.map((solution, idx) => (
                  <div key={idx} className="result-item">
                    <span className="result-number">{idx + 1}.</span>
                    <div className="result-bindings">
                      {typeof solution === 'object' && !Array.isArray(solution) ? (
                        // Prolog query results (variable bindings)
                        Object.entries(solution).map(([varName, value]) => (
                          <div key={varName} className="result-binding">
                            <span className="var-name">{varName}</span>
                            <span className="equals">=</span>
                            <span className="var-value">{typeof value === 'string' ? value : JSON.stringify(value)}</span>
                          </div>
                        ))
                      ) : (
                        // HTN plan results (array of operators)
                        <div className="result-binding">
                          <span className="var-value">{JSON.stringify(solution)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-results">No solutions found</div>
              )}
            </div>
          </section>
        )}

        {/* Query History Section */}
        {queryHistory.length > 0 && (
          <section className="history-section">
            <label className="section-label">Query History</label>
            <div className="history-list">
              {queryHistory.map((hq, idx) => (
                <div
                  key={idx}
                  className="history-item"
                  onClick={() => handleHistoryClick(hq)}
                >
                  {hq}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Current State Section */}
        <section className="state-section">
          <label className="section-label">Current State (Facts)</label>
          <div className="state-list">
            {stateFacts.length > 0 ? (
              stateFacts.map((fact, idx) => (
                <div key={idx} className="state-item">
                  {fact}
                </div>
              ))
            ) : (
              <div className="no-state">No facts loaded</div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default QueryPanel
