import { useRef, useEffect, useState } from 'react'
import { Tree } from 'react-arborist'
import './TreePanel.css'

function TreePanel({ treeData, solutions, selectedSolution, onSolutionSelect }) {
  const containerRef = useRef(null)
  const treeRef = useRef(null)
  const [containerHeight, setContainerHeight] = useState(600)

  // Measure container height when mounted or resized
  useEffect(() => {
    const updateHeight = () => {
      if (containerRef.current) {
        setContainerHeight(containerRef.current.offsetHeight)
      }
    }

    updateHeight()
    window.addEventListener('resize', updateHeight)
    return () => window.removeEventListener('resize', updateHeight)
  }, [])

  // Expand/collapse all
  const expandAll = () => {
    if (treeRef.current) {
      treeRef.current.openAll()
    }
  }

  const collapseAll = () => {
    if (treeRef.current) {
      treeRef.current.closeAll()
    }
  }

  // Transform tree data for react-arborist
  const transformTreeData = (node) => {
    if (!node) return []

    return [{
      id: node.id,
      name: node.name,
      fullSignature: node.fullSignature,
      taskName: node.taskName,
      isOperator: node.isOperator,
      status: node.status,
      bindings: node.bindings,
      conditionBindings: node.conditionBindings,
      failureReason: node.failureReason,
      children: node.children ? node.children.map(transformTreeData).flat() : []
    }]
  }

  // Handle both array of trees (HTN) and single tree (Prolog)
  const isHtnMode = Array.isArray(treeData)
  const currentTree = isHtnMode
    ? (treeData && treeData[selectedSolution])
    : treeData
  const data = currentTree ? transformTreeData(currentTree) : []

  // Custom node renderer matching console output format
  const Node = ({ node, style, dragHandle }) => {
    const hasBindings = node.data.bindings && Object.keys(node.data.bindings).length > 0
    const hasConditionBindings = node.data.conditionBindings && Object.keys(node.data.conditionBindings).length > 0
    const hasFailed = node.data.status === 'failure' && node.data.failureReason

    // Use different brackets for operators vs methods
    const nodeIdMatch = node.data.id ? node.data.id.match(/node(\d+)$/) : null
    const nodeIdNum = nodeIdMatch ? nodeIdMatch[1] : '?'
    const bracket = node.data.isOperator ? `[${nodeIdNum}]` : `{${nodeIdNum}}`

    return (
      <div
        style={style}
        ref={dragHandle}
        className={`tree-node tree-node-${node.data.status || 'default'}`}
        onClick={() => node.toggle()}
      >
        <span className="tree-node-arrow">
          {node.children && node.children.length > 0 ? (node.isOpen ? '▼' : '▶') : ' '}
        </span>
        <span className="tree-node-bracket">{bracket}</span>
        <span className="tree-node-name">{node.data.name}</span>

        {hasFailed && (
          <span className="tree-node-failure-badge">FAILED</span>
        )}

        {/* Full signature on next line */}
        {node.data.fullSignature && (
          <div className="tree-node-signature">{node.data.fullSignature}</div>
        )}

        {/* Head bindings */}
        {hasBindings && (
          <div className="tree-node-bindings">
            <span className="binding-label">Head:</span>
            {Object.entries(node.data.bindings).map(([key, value]) => (
              <span key={key} className="binding">{key}={value}</span>
            ))}
          </div>
        )}

        {/* Condition bindings */}
        {hasConditionBindings && (
          <div className="tree-node-bindings">
            <span className="binding-label">Condition:</span>
            {Object.entries(node.data.conditionBindings).map(([key, value]) => (
              <span key={key} className="binding">{key}={value}</span>
            ))}
          </div>
        )}

        {/* Failure reason */}
        {hasFailed && (
          <div className="tree-node-failure-reason">{node.data.failureReason}</div>
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
        {data.length > 0 ? (
          <Tree
            ref={treeRef}
            data={data}
            openByDefault={true}
            width={containerRef.current?.offsetWidth || 300}
            height={containerHeight - (isHtnMode && solutions && solutions.length > 1 ? 50 : 0)}
            indent={24}
            rowHeight={80}
          >
            {Node}
          </Tree>
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
