import { useRef, useEffect, useState } from 'react'
import { Tree } from 'react-arborist'
import './TreePanel.css'

function TreePanel({ treeData }) {
  const containerRef = useRef(null)
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

  // Transform tree data for react-arborist
  const transformTreeData = (node) => {
    if (!node) return []

    return [{
      id: node.id,
      name: node.name,
      status: node.status,
      bindings: node.bindings,
      children: node.children ? node.children.map(transformTreeData).flat() : []
    }]
  }

  const data = treeData ? transformTreeData(treeData) : []

  // Custom node renderer
  const Node = ({ node, style, dragHandle }) => {
    const hasBindings = node.data.bindings && Object.keys(node.data.bindings).length > 0

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
        <span className="tree-node-name">{node.data.name}</span>

        {hasBindings && (
          <div className="tree-node-bindings">
            {Object.entries(node.data.bindings).map(([key, value]) => (
              <span key={key} className="binding">
                {key} = {JSON.stringify(value)}
              </span>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="panel-container">
      <div className="panel-header">Computation Tree</div>

      <div className="tree-content" ref={containerRef}>
        {data.length > 0 ? (
          <Tree
            data={data}
            openByDefault={true}
            width={containerRef.current?.offsetWidth || 300}
            height={containerHeight}
            indent={24}
            rowHeight={36}
          >
            {Node}
          </Tree>
        ) : (
          <div className="tree-empty">
            <p>No computation tree to display</p>
            <p className="tree-hint">Execute a query to see the resolution tree</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default TreePanel
