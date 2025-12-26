import { useState, useEffect } from 'react'
import './ValidationPanel.css'

/**
 * ValidationPanel - Step-by-step plan timeline for human validation
 *
 * Shows the state evolution through a plan, allowing users to:
 * - Scrub through plan steps
 * - See state diffs per step
 * - Add assertions for expected facts
 * - View timeline visualization
 */
function ValidationPanel({ sessionId, onTimelineLoad }) {
  const [goal, setGoal] = useState('')
  const [timeline, setTimeline] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [assertions, setAssertions] = useState([])
  const [newAssertion, setNewAssertion] = useState('')
  const [expandedSections, setExpandedSections] = useState({
    added: true,
    removed: true,
    state: false
  })

  // Load timeline for a goal
  const loadTimeline = async () => {
    if (!sessionId || !goal) {
      setError('Session and goal are required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/plan/timeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, goal })
      })

      const data = await response.json()

      if (data.error) {
        setError(data.error)
        setTimeline(null)
      } else {
        setTimeline(data)
        setCurrentStep(0)
        setAssertions([])
        if (onTimelineLoad) onTimelineLoad(data)
      }
    } catch (err) {
      setError(`Failed to load timeline: ${err.message}`)
      setTimeline(null)
    } finally {
      setLoading(false)
    }
  }

  // Get current step data
  const getCurrentStepData = () => {
    if (!timeline || !timeline.timeline) return null
    return timeline.timeline[currentStep] || null
  }

  // Check assertions against current state
  const checkAssertions = () => {
    const stepData = getCurrentStepData()
    if (!stepData) return []

    const stateStr = stepData.state.join(' ')
    return assertions.map(assertion => ({
      pattern: assertion,
      pass: stateStr.includes(assertion)
    }))
  }

  // Add assertion
  const addAssertion = () => {
    if (newAssertion && !assertions.includes(newAssertion)) {
      setAssertions([...assertions, newAssertion])
      setNewAssertion('')
    }
  }

  // Remove assertion
  const removeAssertion = (pattern) => {
    setAssertions(assertions.filter(a => a !== pattern))
  }

  // Toggle section expansion
  const toggleSection = (section) => {
    setExpandedSections({
      ...expandedSections,
      [section]: !expandedSections[section]
    })
  }

  const stepData = getCurrentStepData()
  const assertionResults = checkAssertions()

  return (
    <div className="validation-panel">
      <div className="validation-header">
        <h3>Plan Timeline</h3>
      </div>

      {/* Goal Input */}
      <div className="goal-input">
        <input
          type="text"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Enter goal (e.g., travel-to(park).)"
          onKeyDown={(e) => e.key === 'Enter' && loadTimeline()}
        />
        <button onClick={loadTimeline} disabled={loading}>
          {loading ? 'Loading...' : 'Load Timeline'}
        </button>
      </div>

      {error && <div className="validation-error">{error}</div>}

      {timeline && (
        <>
          {/* Timeline Scrubber */}
          <div className="timeline-scrubber">
            <div className="timeline-controls">
              <button
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                disabled={currentStep === 0}
              >
                &lt;
              </button>
              <span className="step-indicator">
                Step {currentStep} / {timeline.total_steps - 1}
              </span>
              <button
                onClick={() => setCurrentStep(Math.min(timeline.total_steps - 1, currentStep + 1))}
                disabled={currentStep >= timeline.total_steps - 1}
              >
                &gt;
              </button>
            </div>
            <input
              type="range"
              min="0"
              max={timeline.total_steps - 1}
              value={currentStep}
              onChange={(e) => setCurrentStep(parseInt(e.target.value))}
              className="timeline-slider"
            />
          </div>

          {/* Current Step Info */}
          {stepData && (
            <div className="step-info">
              <div className="operator-name">
                {stepData.operator ? (
                  <><strong>Operator:</strong> {stepData.operator}</>
                ) : (
                  <em>[Initial State]</em>
                )}
              </div>

              {/* State Changes */}
              {stepData.removed.length > 0 && (
                <div className="state-section removed">
                  <div
                    className="section-header"
                    onClick={() => toggleSection('removed')}
                  >
                    <span>{expandedSections.removed ? '▼' : '▶'}</span>
                    <span className="section-title">Removed ({stepData.removed.length})</span>
                  </div>
                  {expandedSections.removed && (
                    <div className="section-content">
                      {stepData.removed.map((fact, i) => (
                        <div key={i} className="fact-item removed">- {fact}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {stepData.added.length > 0 && (
                <div className="state-section added">
                  <div
                    className="section-header"
                    onClick={() => toggleSection('added')}
                  >
                    <span>{expandedSections.added ? '▼' : '▶'}</span>
                    <span className="section-title">Added ({stepData.added.length})</span>
                  </div>
                  {expandedSections.added && (
                    <div className="section-content">
                      {stepData.added.map((fact, i) => (
                        <div key={i} className="fact-item added">+ {fact}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Full State (collapsible) */}
              <div className="state-section full-state">
                <div
                  className="section-header"
                  onClick={() => toggleSection('state')}
                >
                  <span>{expandedSections.state ? '▼' : '▶'}</span>
                  <span className="section-title">Full State ({stepData.state.length} facts)</span>
                </div>
                {expandedSections.state && (
                  <div className="section-content">
                    {stepData.state.slice(0, 50).map((fact, i) => (
                      <div key={i} className="fact-item">{fact}</div>
                    ))}
                    {stepData.state.length > 50 && (
                      <div className="fact-item more">... and {stepData.state.length - 50} more</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Assertions */}
          <div className="assertions-section">
            <h4>Assertions</h4>
            <div className="assertion-input">
              <input
                type="text"
                value={newAssertion}
                onChange={(e) => setNewAssertion(e.target.value)}
                placeholder="Add assertion pattern..."
                onKeyDown={(e) => e.key === 'Enter' && addAssertion()}
              />
              <button onClick={addAssertion}>Add</button>
            </div>
            <div className="assertion-list">
              {assertionResults.map(({ pattern, pass }, i) => (
                <div key={i} className={`assertion-item ${pass ? 'pass' : 'fail'}`}>
                  <span className="assertion-status">{pass ? '✓' : '✗'}</span>
                  <span className="assertion-pattern">{pattern}</span>
                  <button
                    className="assertion-remove"
                    onClick={() => removeAssertion(pattern)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Operators List */}
          <div className="operators-list">
            <h4>Plan ({timeline.operators.length} operators)</h4>
            <div className="operators-content">
              {timeline.operators.map((op, i) => (
                <div
                  key={i}
                  className={`operator-item ${i + 1 === currentStep ? 'current' : ''}`}
                  onClick={() => setCurrentStep(i + 1)}
                >
                  <span className="operator-index">{i + 1}.</span>
                  <span className="operator-text">{op}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ValidationPanel
