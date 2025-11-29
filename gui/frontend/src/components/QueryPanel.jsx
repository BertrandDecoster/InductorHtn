import { useState } from 'react'
import './QueryPanel.css'

// Group facts by functor name for display
function groupFacts(facts) {
  if (!facts || facts.length === 0) return []

  const groups = {}
  facts.forEach(fact => {
    // Extract functor name (before first parenthesis)
    const match = fact.match(/^([^(]+)/)
    const functor = match ? match[1] : fact
    if (!groups[functor]) groups[functor] = []
    groups[functor].push(fact)
  })

  const result = []
  Object.entries(groups).forEach(([functor, items]) => {
    if (items.length > 3) {
      // Create a collapsible group
      result.push({ type: 'group', functor, count: items.length, items })
    } else {
      // Add individual items
      items.forEach(fact => result.push({ type: 'item', fact }))
    }
  })

  return result
}

// Component for rendering a single fact or a group of facts
function FactItem({ item, className, expandedGroups, onToggleGroup }) {
  if (item.type === 'group') {
    const isExpanded = expandedGroups[item.functor]
    return (
      <div className={`fact-group ${className}`}>
        <div
          className="fact-group-header"
          onClick={() => onToggleGroup(item.functor)}
        >
          <span className="fact-group-arrow">{isExpanded ? '▼' : '▶'}</span>
          <span className="fact-group-name">{item.functor}(?...)</span>
          <span className="fact-group-count">— {item.count}</span>
        </div>
        {isExpanded && (
          <div className="fact-group-items">
            {item.items.map((fact, idx) => (
              <div key={idx} className={`state-item ${className}`}>
                {fact}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }
  return (
    <div className={`state-item ${className}`}>
      {item.fact}
    </div>
  )
}

function QueryPanel({ onQueryExecute, onHtnExecute, queryResults, stateFacts, factsDiff, selectedSolution, loading }) {
  const [query, setQuery] = useState('')
  const [queryHistory, setQueryHistory] = useState([])
  const [mode, setMode] = useState('htn')  // 'prolog' or 'htn'
  const [expandedGroups, setExpandedGroups] = useState({})

  const handleExecute = () => {
    let trimmedQuery = query.trim()
    if (!trimmedQuery) return

    // Auto-append period if missing
    if (!trimmedQuery.endsWith('.')) {
      trimmedQuery = trimmedQuery + '.'
    }

    if (mode === 'htn') {
      onHtnExecute(trimmedQuery)
    } else {
      onQueryExecute(trimmedQuery)
    }
    setQueryHistory([trimmedQuery, ...queryHistory].slice(0, 10)) // Keep last 10
  }

  const handleHistoryClick = (historicalQuery) => {
    setQuery(historicalQuery)
  }

  const toggleGroup = (functor) => {
    setExpandedGroups(prev => ({
      ...prev,
      [functor]: !prev[functor]
    }))
  }

  // Determine what facts to display
  const hasDiff = factsDiff && (factsDiff.added?.length > 0 || factsDiff.removed?.length > 0)

  // Group facts for display
  const groupedAdded = hasDiff ? groupFacts(factsDiff.added) : []
  const groupedRemoved = hasDiff ? groupFacts(factsDiff.removed) : []
  const groupedUnchanged = hasDiff ? groupFacts(factsDiff.unchanged) : groupFacts(stateFacts)

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
              {queryResults.pretty_solutions && queryResults.pretty_solutions.length > 0 ? (
                // HTN plan results with pretty formatting
                queryResults.pretty_solutions.map((solution, idx) => (
                  <div key={idx} className="result-item">
                    <span className="result-number">{idx + 1}.</span>
                    <div className="result-bindings">
                      <span className="var-value">{solution}</span>
                    </div>
                  </div>
                ))
              ) : queryResults.solutions && queryResults.solutions.length > 0 ? (
                // Prolog query results or fallback
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
                        // HTN plan results (array of operators) - fallback
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
          <label className="section-label">
            {hasDiff ? `State After Solution ${selectedSolution + 1}` : 'Current State (Facts)'}
          </label>
          <div className="state-list">
            {/* Added Facts (green) */}
            {groupedAdded.length > 0 && (
              <>
                <div className="facts-section-header facts-added-header">Added Facts ({factsDiff.added.length})</div>
                {groupedAdded.map((item, idx) => (
                  <FactItem
                    key={`added-${idx}`}
                    item={item}
                    className="fact-added"
                    expandedGroups={expandedGroups}
                    onToggleGroup={toggleGroup}
                  />
                ))}
              </>
            )}

            {/* Removed Facts (red) */}
            {groupedRemoved.length > 0 && (
              <>
                <div className="facts-section-header facts-removed-header">Removed Facts ({factsDiff.removed.length})</div>
                {groupedRemoved.map((item, idx) => (
                  <FactItem
                    key={`removed-${idx}`}
                    item={item}
                    className="fact-removed"
                    expandedGroups={expandedGroups}
                    onToggleGroup={toggleGroup}
                  />
                ))}
              </>
            )}

            {/* Unchanged Facts (default) */}
            {groupedUnchanged.length > 0 ? (
              <>
                {hasDiff && (
                  <div className="facts-section-header">Unchanged Facts ({factsDiff.unchanged.length})</div>
                )}
                {groupedUnchanged.map((item, idx) => (
                  <FactItem
                    key={`unchanged-${idx}`}
                    item={item}
                    className=""
                    expandedGroups={expandedGroups}
                    onToggleGroup={toggleGroup}
                  />
                ))}
              </>
            ) : (
              !hasDiff && <div className="no-state">No facts loaded</div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default QueryPanel
