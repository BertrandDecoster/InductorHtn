import { useState } from 'react'
import './QueryPanel.css'

function QueryPanel({ onQueryExecute, queryResults, stateFacts, loading }) {
  const [query, setQuery] = useState('')
  const [queryHistory, setQueryHistory] = useState([])

  const handleExecute = () => {
    if (!query.trim()) return

    onQueryExecute(query)
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
          <label className="section-label">Prolog Query</label>
          <div className="query-input-container">
            <input
              type="text"
              className="query-input"
              placeholder="at(?where)."
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
              {queryResults.solutions.length > 0 ? (
                queryResults.solutions.map((solution, idx) => (
                  <div key={idx} className="result-item">
                    <span className="result-number">{idx + 1}.</span>
                    <div className="result-bindings">
                      {Object.entries(solution).map(([varName, value]) => (
                        <div key={varName} className="result-binding">
                          <span className="var-name">{varName}</span>
                          <span className="equals">=</span>
                          <span className="var-value">{value}</span>
                        </div>
                      ))}
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
