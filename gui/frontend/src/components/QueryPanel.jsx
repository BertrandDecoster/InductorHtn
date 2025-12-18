import { useState, useEffect } from 'react'
import { getQueryHistory, addQueryToHistory } from '../utils/storage'
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

// Highlight parts of instantiated query that were substituted
function highlightSubstitutions(instantiatedQuery, originalQuery, bindings) {
  if (!instantiatedQuery || !bindings) {
    return [{ text: instantiatedQuery || '', isVar: false }]
  }

  const parts = []
  let lastIndex = 0

  // Find each substituted value in the instantiated query
  Object.values(bindings).forEach(value => {
    const valueStr = String(value)
    const index = instantiatedQuery.indexOf(valueStr, lastIndex)
    if (index !== -1) {
      if (index > lastIndex) {
        parts.push({ text: instantiatedQuery.slice(lastIndex, index), isVar: false })
      }
      parts.push({ text: valueStr, isVar: true })
      lastIndex = index + valueStr.length
    }
  })

  if (lastIndex < instantiatedQuery.length) {
    parts.push({ text: instantiatedQuery.slice(lastIndex), isVar: false })
  }

  return parts.length > 0 ? parts : [{ text: instantiatedQuery, isVar: false }]
}

function QueryPanel({ onQueryExecute, onHtnExecute, queryResults, stateFacts, factsDiff, selectedSolution, loading }) {
  const [query, setQuery] = useState('')
  const [htnHistory, setHtnHistory] = useState([])
  const [prologHistory, setPrologHistory] = useState([])
  const [mode, setMode] = useState('htn')  // 'prolog' or 'htn'
  const [expandedGroups, setExpandedGroups] = useState({})
  const [expandedUnifiers, setExpandedUnifiers] = useState({})

  // Load query history from localStorage on mount
  useEffect(() => {
    setHtnHistory(getQueryHistory('htn'))
    setPrologHistory(getQueryHistory('prolog'))
  }, [])

  const toggleUnifier = (idx) => {
    setExpandedUnifiers(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }))
  }

  const handleExecute = () => {
    let trimmedQuery = query.trim()
    if (!trimmedQuery) return

    // Auto-append period if missing
    if (!trimmedQuery.endsWith('.')) {
      trimmedQuery = trimmedQuery + '.'
    }

    if (mode === 'htn') {
      onHtnExecute(trimmedQuery)
      setHtnHistory(addQueryToHistory('htn', trimmedQuery))
    } else {
      onQueryExecute(trimmedQuery)
      setPrologHistory(addQueryToHistory('prolog', trimmedQuery))
    }
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
            {/* HTN plan results */}
            {queryResults.pretty_solutions && queryResults.pretty_solutions.length > 0 ? (
              <>
                <label className="section-label">
                  Results: {queryResults.total_count} plan{queryResults.total_count !== 1 ? 's' : ''}
                </label>
                <div className="results-list">
                  {queryResults.pretty_solutions.map((solution, planIdx) => {
                    // Split comma-separated operators into individual lines
                    const operators = solution.split(', ')
                    return (
                      <div key={planIdx} className="result-item htn-plan">
                        <span className="result-number">{planIdx + 1}.</span>
                        <div className="result-operators">
                          {operators.map((op, opIdx) => (
                            <div key={opIdx} className="operator-line">
                              <span className="operator-index">{opIdx}.</span>
                              <span className="operator-text">{op}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            ) : queryResults.has_variables === false ? (
              /* Ground query: show [TRUE] or [FALSE] */
              <>
                <label className="section-label">Result</label>
                <div className="ground-query-result">
                  {queryResults.total_count > 0 ? (
                    <span className="result-status-true">[TRUE]</span>
                  ) : (
                    <span className="result-status-false">[FALSE]</span>
                  )}
                </div>
              </>
            ) : (
              /* Variable query: show instantiated queries with unifiers */
              <>
                <label className="section-label">
                  Results: {queryResults.total_count} solution{queryResults.total_count !== 1 ? 's' : ''}
                </label>
                <div className="results-list">
                  {queryResults.solutions && queryResults.solutions.length > 0 ? (
                    queryResults.solutions.map((solution, idx) => {
                      const instantiated = queryResults.instantiated_queries?.[idx] || ''
                      const parts = highlightSubstitutions(instantiated, queryResults.query, solution)
                      const isExpanded = expandedUnifiers[idx]

                      return (
                        <div key={idx} className="result-item">
                          <span className="result-number">{idx + 1}.</span>
                          <div className="result-body">
                            {/* Instantiated query with highlighted variables */}
                            <div className="instantiated-query">
                              {parts.map((part, i) => (
                                part.isVar ? (
                                  <span key={i} className="substituted-var">{part.text}</span>
                                ) : (
                                  <span key={i}>{part.text}</span>
                                )
                              ))}
                            </div>

                            {/* Collapsible unifier */}
                            {Object.keys(solution).length > 0 && (
                              <div className="unifier-section">
                                <button
                                  className="unifier-toggle"
                                  onClick={() => toggleUnifier(idx)}
                                >
                                  {isExpanded ? '▼' : '▶'} Unifier
                                </button>
                                {isExpanded && (
                                  <div className="unifier-bindings">
                                    {Object.entries(solution).map(([varName, value]) => (
                                      <div key={varName} className="result-binding">
                                        <span className="var-name">{varName}</span>
                                        <span className="equals">=</span>
                                        <span className="var-value">
                                          {typeof value === 'string' ? value : JSON.stringify(value)}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })
                  ) : (
                    <div className="no-results">No solutions found</div>
                  )}
                </div>
              </>
            )}
          </section>
        )}

        {/* Query History Section */}
        {(() => {
          const currentHistory = mode === 'htn' ? htnHistory : prologHistory
          return currentHistory.length > 0 && (
            <section className="history-section">
              <label className="section-label">
                {mode === 'htn' ? 'HTN' : 'Prolog'} Query History
              </label>
              <div className="history-list">
                {currentHistory.map((hq, idx) => (
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
          )
        })()}

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
