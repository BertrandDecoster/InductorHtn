#!/usr/bin/env python3
"""
HTN Tree Reconstructor - Rebuilds the complete HTN planning tree from trace logs

This module reconstructs the search tree explored by the HTN planner using only
minimal local information from trace logs. No global state storage needed.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class HtnPlanNode:
    """
    Lightweight representation of a node in the HTN planning tree.
    Contains only local information needed for tree reconstruction.
    """
    node_id: int
    parent_id: Optional[int] = None
    
    # Task being solved at this node
    current_task: Optional[str] = None
    
    # Method or operator being applied
    method_signature: Optional[str] = None
    operator_signature: Optional[str] = None
    
    # Variable bindings extracted from conditions (e.g., {"?p": "downtown"})
    variable_bindings: Dict[str, str] = field(default_factory=dict)
    
    # Operator effects (for operators only)
    operator_deletes: List[str] = field(default_factory=list)
    operator_adds: List[str] = field(default_factory=list)
    
    # Node outcome
    success: Optional[bool] = None
    
    # Tree structure
    children: List[int] = field(default_factory=list)
    
    def __str__(self) -> str:
        task_str = f"Task: {self.current_task}" if self.current_task else ""
        method_str = f"Method: {self.method_signature}" if self.method_signature else ""
        op_str = f"Operator: {self.operator_signature}" if self.operator_signature else ""
        bindings_str = f"Bindings: {self.variable_bindings}" if self.variable_bindings else ""
        success_str = f"Success: {self.success}" if self.success is not None else "Pending"
        
        parts = [p for p in [task_str, method_str, op_str, bindings_str, success_str] if p]
        return f"Node {self.node_id}: {', '.join(parts)}"


class HtnTreeReconstructor:
    """
    Reconstructs the HTN planning tree from trace logs.
    
    Parses trace entries to build a complete tree structure showing:
    - Which tasks were solved
    - Which methods/operators were tried
    - Variable bindings at each step
    - Success/failure outcomes
    - Parent-child relationships
    """
    
    def __init__(self):
        self.nodes: Dict[int, HtnPlanNode] = {}
        self.root_node_id: Optional[int] = None
        
    def parse_traces(self, traces: List[str]) -> Dict[int, HtnPlanNode]:
        """
        Parse trace entries and build the complete tree.
        
        Args:
            traces: List of trace strings from HtnPlanner
            
        Returns:
            Dictionary mapping node_id to HtnPlanNode
        """
        for trace in traces:
            self._parse_trace_entry(trace.strip())
            
        # Find root node (node with no parent)
        self._find_root_node()
            
        return self.nodes
    
    def _find_root_node(self) -> None:
        """Find and set the root node (node with no parent)."""
        for node_id, node in self.nodes.items():
            if node.parent_id is None:
                self.root_node_id = node_id
                break
    
    def _parse_trace_entry(self, trace: str) -> None:
        """Parse a single trace entry and update tree structure."""
        if not trace:
            return
            
        # Extract timestamp and trace content
        # Format: "MMDD HH:MM:SS ^time.ms HtnPlanner::FindPlan STATUS message"
        if "HtnPlanner::FindPlan" not in trace:
            return
            
        # Find the status part after HtnPlanner::FindPlan
        htn_pos = trace.find("HtnPlanner::FindPlan")
        if htn_pos == -1:
            return
            
        content = trace[htn_pos + len("HtnPlanner::FindPlan"):].strip()
        
        # Parse different trace types
        if content.startswith("PUSH"):
            self._parse_push(content)
        elif content.startswith("POP"):
            self._parse_pop(content)
        elif content.startswith("SOLVE"):
            self._parse_solve(content)
        elif content.startswith("METHOD"):
            self._parse_method(content)
        elif content.startswith("OPERATOR"):
            self._parse_operator(content)
        elif content.startswith("SUCCESS"):
            self._parse_success(content)
        elif content.startswith("FAIL"):
            self._parse_fail(content)
        elif "condition:" in content:
            self._parse_condition(content)
    
    def _parse_push(self, content: str) -> None:
        """Parse PUSH nodeID:X parentID:Y"""
        match = re.search(r"nodeID:(\d+)\s+parentID:(\d+)", content)
        if match:
            node_id = int(match.group(1))
            parent_id = int(match.group(2))
            
            # Create or update node
            if node_id not in self.nodes:
                self.nodes[node_id] = HtnPlanNode(node_id=node_id)
            self.nodes[node_id].parent_id = parent_id
            
            # Update parent's children list
            if parent_id not in self.nodes:
                self.nodes[parent_id] = HtnPlanNode(node_id=parent_id)
            if node_id not in self.nodes[parent_id].children:
                self.nodes[parent_id].children.append(node_id)
    
    def _parse_pop(self, content: str) -> None:
        """Parse POP nodeID:X returnValue:Y"""
        match = re.search(r"nodeID:(\d+)\s+returnValue:([01])", content)
        if match:
            node_id = int(match.group(1))
            return_value = bool(int(match.group(2)))
            
            if node_id not in self.nodes:
                self.nodes[node_id] = HtnPlanNode(node_id=node_id)
            self.nodes[node_id].success = return_value
    
    def _parse_solve(self, content: str) -> None:
        """Parse SOLVE nodeID:X goal:'task' remaining:Y"""
        match = re.search(r"nodeID:(\d+)\s+goal:'([^']+)'", content)
        if match:
            node_id = int(match.group(1))
            task = match.group(2)
            
            if node_id not in self.nodes:
                self.nodes[node_id] = HtnPlanNode(node_id=node_id)
            self.nodes[node_id].current_task = task
    
    def _parse_method(self, content: str) -> None:
        """Parse METHOD nodeID:X resolve next method 'signature'"""
        match = re.search(r"nodeID:(\d+).*method\s+'([^']+)'", content)
        if match:
            node_id = int(match.group(1))
            method_sig = match.group(2)
            
            if node_id not in self.nodes:
                self.nodes[node_id] = HtnPlanNode(node_id=node_id)
            self.nodes[node_id].method_signature = method_sig
    
    def _parse_operator(self, content: str) -> None:
        """Parse OPERATOR nodeID:X Operator 'sig1' unifies with 'sig2'"""
        # Extract node ID
        node_match = re.search(r"nodeID:(\d+)", content)
        if not node_match:
            return
        node_id = int(node_match.group(1))
        
        # Extract operator signature
        op_match = re.search(r"Operator\s+'([^']+)'\s+unifies", content)
        if op_match:
            op_sig = op_match.group(1)
            
            if node_id not in self.nodes:
                self.nodes[node_id] = HtnPlanNode(node_id=node_id)
            self.nodes[node_id].operator_signature = op_sig
    
    def _parse_success(self, content: str) -> None:
        """Parse SUCCESS nodeID:X no tasks remain"""
        match = re.search(r"nodeID:(\d+)", content)
        if match:
            node_id = int(match.group(1))
            
            if node_id not in self.nodes:
                self.nodes[node_id] = HtnPlanNode(node_id=node_id)
            self.nodes[node_id].success = True
    
    def _parse_fail(self, content: str) -> None:
        """Parse FAIL nodeID:X reason"""
        match = re.search(r"nodeID:(\d+)", content)
        if match:
            node_id = int(match.group(1))
            
            if node_id not in self.nodes:
                self.nodes[node_id] = HtnPlanNode(node_id=node_id)
            self.nodes[node_id].success = False
    
    def _parse_condition(self, content: str) -> None:
        """Parse condition: (?var = value, ?var2 = value2) for variable bindings"""
        # Look for variable bindings in format (?var = value)
        bindings = re.findall(r"\?(\w+)\s*=\s*([^,\)]+)", content)
        if not bindings:
            return
        
        # Find the most recent node that this applies to
        # Look backwards through traces to find the associated nodeID
        # For now, we'll associate with the most recently created node
        if self.nodes:
            latest_node_id = max(self.nodes.keys())
            node = self.nodes[latest_node_id]
            
            for var, value in bindings:
                node.variable_bindings[f"?{var}"] = value.strip()
    
    def get_root_node(self) -> Optional[HtnPlanNode]:
        """Get the root node of the tree."""
        return self.nodes.get(self.root_node_id) if self.root_node_id is not None else None
    
    def print_tree(self, node_id: Optional[int] = None, indent: int = 0) -> None:
        """Print the tree structure starting from given node (or root)."""
        if node_id is None:
            node_id = self.root_node_id
        
        if node_id is None or node_id not in self.nodes:
            return
            
        node = self.nodes[node_id]
        prefix = "  " * indent
        print(f"{prefix}{node}")
        
        # Print children
        for child_id in node.children:
            self.print_tree(child_id, indent + 1)
    
    def get_successful_path(self) -> List[HtnPlanNode]:
        """Get the path through the tree that led to success."""
        if self.root_node_id is None or self.root_node_id not in self.nodes:
            return []
            
        def find_success_path(node_id: int) -> List[HtnPlanNode]:
            if node_id not in self.nodes:
                return []
                
            node = self.nodes[node_id]
            
            # If this is a leaf node (no children), include it if successful
            if not node.children:
                return [node] if node.success else []
            
            # Find successful child path
            for child_id in node.children:
                child_path = find_success_path(child_id)
                if child_path:  # Found a successful path through this child
                    return [node] + child_path
                    
            return []
        
        return find_success_path(self.root_node_id)


if __name__ == "__main__":
    # Example usage
    example_traces = [
        "0902 15:54:01 ^0.0000 HtnPlanner::FindPlan ALL BEGIN  Goals:(travel-to(park))",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan            SOLVE      nodeID:0 goal:'travel-to(park)' remaining:()",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan            METHOD     nodeID:0 resolve next method 'travel-to(?q) => if(at(?p), walking-distance(?p,?q)), do(walk(?p,?q))'",
        "0902 15:54:01 ^0.0000 HtnPlanner::FindPlan                       condition: (?p = downtown)",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan                       PUSH       nodeID:1 parentID:0",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan                       SOLVE      nodeID:1 goal:'walk(downtown,park)' remaining:()",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan                       OPERATOR   nodeID:1 Operator 'walk(?here,?there)' unifies with 'walk(downtown,park)'",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan                                  PUSH       nodeID:2 parentID:1",
        "0902 15:54:01 ^0.0000 HtnPlanner::FindPlan                                  SUCCESS    nodeID:2 no tasks remain",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan                                  POP        nodeID:2 returnValue:1",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan                       POP        nodeID:1 returnValue:1",
        "0902 15:54:01 =0.0000 HtnPlanner::FindPlan            POP        nodeID:0 returnValue:1",
    ]
    
    reconstructor = HtnTreeReconstructor()
    nodes = reconstructor.parse_traces(example_traces)
    
    print("Reconstructed HTN Planning Tree:")
    print("=" * 50)
    reconstructor.print_tree()
    
    print("\nSuccessful execution path:")
    print("=" * 30)
    success_path = reconstructor.get_successful_path()
    for i, node in enumerate(success_path):
        print(f"{i}: {node}")