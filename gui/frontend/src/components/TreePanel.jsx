import { useRef, useEffect, useState } from 'react'
import './TreePanel.css'

function TreePanel({ treeData, solutions, selectedSolution, onSolutionSelect }) {
  const containerRef = useRef(null)
  const [expandedNodes, setExpandedNodes] = useState(new Set())
  const [expandedFailures, setExpandedFailures] = useState(new Set())

  // Initialize all nodes as expanded
  useEffect(() => {
    if (treeData) {
      const allIds = new Set()
      const collectIds = (node) => {
        if (node && node.id) {
          allIds.add(node.id)
          if (node.children) {
            node.children.forEach(collectIds)
          }
        }
      }
      if (Array.isArray(treeData)) {
        treeData.forEach(collectIds)
      } else {
        collectIds(treeData)
      }
      setExpandedNodes(allIds)
    }
  }, [treeData])

  // Toggle node expansion
  const toggleNode = (nodeId) => {
    setExpandedNodes(prev => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  // Toggle failure details expansion
  const toggleFailureDetails = (nodeId, e) => {
    e.stopPropagation()
    setExpandedFailures(prev => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  // Expand/collapse all
  const expandAll = () => {
    const allIds = new Set()
    const collectIds = (node) => {
      if (node && node.id) {
        allIds.add(node.id)
        if (node.children) {
          node.children.forEach(collectIds)
        }
      }
    }
    if (Array.isArray(treeData)) {
      treeData.forEach(collectIds)
    } else if (treeData) {
      collectIds(treeData)
    }
    setExpandedNodes(allIds)
  }

  const collapseAll = () => {
    setExpandedNodes(new Set())
  }

  // Handle both array of trees (HTN) and single tree (Prolog)
  const isHtnMode = Array.isArray(treeData)
  const currentTree = isHtnMode
    ? (treeData && treeData[selectedSolution])
    : treeData

  // Format method signature with styled keywords
  const formatSignature = (signature) => {
    if (!signature) return null

    // Replace "default" with "else" for display
    let text = signature.replace(/\bdefault,/, 'else,')

    // Split on keywords to apply styling
    const parts = text.split(/(\bif\(|\bdo\(|\belse,|\ballOf,|\banyOf,)/)

    return parts.map((part, i) => {
      if (part === 'if(' || part === 'do(') {
        return <span key={i}><strong>{part.slice(0, -1)}</strong>(</span>
      }
      if (part === 'else,' || part === 'allOf,' || part === 'anyOf,') {
        return <em key={i}>{part}</em>
      }
      return part
    })
  }

  // Format failure category for display
  const formatCategory = (category) => {
    const categoryMap = {
      'NO_MATCHING_METHOD': 'No Method',
      'PRECONDITION_FAILED': 'Precondition',
      'UNIFICATION_FAILED': 'Unification',
      'SUBTASK_FAILED': 'Subtask',
      'OPERATOR_FAILED': 'Operator',
      'BACKTRACKED': 'Backtracked',
      'UNKNOWN': 'Unknown'
    }
    return categoryMap[category] || category
  }

  // Recursive tree node renderer
  const TreeNode = ({ node, depth = 0 }) => {
    if (!node) return null

    const hasChildren = node.children && node.children.length > 0
    const isOpen = expandedNodes.has(node.id)
    const hasBindings = node.bindings && Object.keys(node.bindings).length > 0
    const hasConditionBindings = node.conditionBindings && Object.keys(node.conditionBindings).length > 0
    const hasFailed = node.status === 'failure'
    const hasFailureDetail = node.failureDetail
    const isFailureExpanded = expandedFailures.has(node.id)

    // Use different brackets for operators vs methods
    const nodeIdMatch = node.id ? node.id.match(/node(\d+)$/) : null
    const nodeIdNum = nodeIdMatch ? nodeIdMatch[1] : '?'
    const bracket = node.isOperator ? `[${nodeIdNum}]` : `{${nodeIdNum}}`

    return (
      <div className="tree-node-container">
        <div
          className={`tree-node tree-node-${node.status || 'default'}`}
          onClick={() => hasChildren && toggleNode(node.id)}
        >
          {/* Main node line */}
          <div className="tree-node-main">
            <span className="tree-node-arrow">
              {hasChildren ? (isOpen ? '▼' : '▶') : ' '}
            </span>
            <span className="tree-node-bracket">{bracket}</span>
            <span className={`tree-node-name ${node.isOperator ? 'tree-node-operator' : 'tree-node-method'}`}>
              {node.name}
            </span>

            {hasFailed && hasFailureDetail && (
              <span className={`tree-node-failure-badge failure-${node.failureDetail.category?.toLowerCase()}`}>
                {formatCategory(node.failureDetail.category)}
              </span>
            )}

            {hasFailed && !hasFailureDetail && (
              <span className="tree-node-failure-badge">FAILED</span>
            )}

            {hasFailed && hasFailureDetail && (
              <button
                className="tree-node-expand-btn"
                onClick={(e) => toggleFailureDetails(node.id, e)}
                title={isFailureExpanded ? "Hide details" : "Show why it failed"}
              >
                {isFailureExpanded ? '▲' : '▼'} Why?
              </button>
            )}
          </div>

          {/* Full signature */}
          {node.fullSignature && (
            <div className="tree-node-signature">{formatSignature(node.fullSignature)}</div>
          )}

          {/* Head bindings */}
          {hasBindings && (
            <div className="tree-node-bindings">
              <span className="binding-label">Head:</span>
              {Object.entries(node.bindings).map(([key, value]) => (
                <span key={key} className="binding">{key}={value}</span>
              ))}
            </div>
          )}

          {/* Condition bindings */}
          {hasConditionBindings && (
            <div className="tree-node-bindings">
              <span className="binding-label">Condition:</span>
              {Object.entries(node.conditionBindings).map(([key, value]) => (
                <span key={key} className="binding">{key}={value}</span>
              ))}
            </div>
          )}

          {/* Enhanced failure details (collapsible) */}
          {hasFailed && hasFailureDetail && isFailureExpanded && (
            <div className="tree-node-failure-details">
              {/* Failure message */}
              <div className="failure-message">
                <span className="failure-icon">⚠</span>
                {node.failureDetail.message}
              </div>

              {/* Missing facts */}
              {node.missingFacts && node.missingFacts.length > 0 && (
                <div className="failure-section">
                  <div className="failure-section-title">Missing Facts:</div>
                  <div className="failure-items">
                    {node.missingFacts.map((fact, i) => (
                      <span key={i} className="failure-item missing-fact">{fact}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Failed conditions */}
              {node.failedConditions && node.failedConditions.length > 0 && (
                <div className="failure-section">
                  <div className="failure-section-title">Failed Conditions:</div>
                  <div className="failure-items">
                    {node.failedConditions.map((cond, i) => (
                      <span key={i} className="failure-item failed-condition">{cond}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Alternatives tried */}
              {node.alternativesTried && node.alternativesTried.length > 0 && (
                <div className="failure-section">
                  <div className="failure-section-title">Alternatives Tried:</div>
                  <div className="alternatives-list">
                    {node.alternativesTried.map((alt, i) => (
                      <div key={i} className={`alternative ${alt.success ? 'alt-success' : 'alt-failed'}`}>
                        <span className="alt-status">{alt.success ? '✓' : '✗'}</span>
                        <span className="alt-name">{alt.signature || alt.method_name}</span>
                        {alt.failure_reason && (
                          <span className="alt-reason">{alt.failure_reason}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggestions */}
              {node.failureDetail.suggestions && node.failureDetail.suggestions.length > 0 && (
                <div className="failure-section">
                  <div className="failure-section-title">💡 Suggestions:</div>
                  <ul className="suggestions-list">
                    {node.failureDetail.suggestions.map((suggestion, i) => (
                      <li key={i}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Legacy failure reason (if no enhanced details) */}
          {hasFailed && !hasFailureDetail && node.failureReason && (
            <div className="tree-node-failure-reason">{node.failureReason}</div>
          )}
        </div>

        {/* Children */}
        {hasChildren && isOpen && (
          <div className="tree-node-children">
            {node.children.map((child, idx) => (
              <TreeNode key={child.id || idx} node={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="panel-container">
      <div className="panel-header">
        <span>Plan Tree</span>
        <div className="panel-header-controls">
          <button onClick={expandAll} title="Expand All">⊞</button>
          <button onClick={collapseAll} title="Collapse All">⊟</button>
        </div>
      </div>

      {/* Solution selector (if multiple solutions) */}
      {isHtnMode && solutions && solutions.length > 1 && (
        <div className="solution-selector">
          {solutions.map((_, i) => (
            <button
              key={i}
              className={selectedSolution === i ? 'active' : ''}
              onClick={() => onSolutionSelect(i)}
            >
              Solution {i + 1}
            </button>
          ))}
        </div>
      )}

      <div className="tree-content" ref={containerRef}>
        {currentTree ? (
          <TreeNode node={currentTree} depth={0} />
        ) : (
          <div className="tree-empty">
            <p>No plan tree to display</p>
            <p className="tree-hint">Execute an HTN query to see the decomposition tree</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default TreePanel
