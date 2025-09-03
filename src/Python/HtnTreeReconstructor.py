#!/usr/bin/env python3
"""
HTN Tree Reconstructor - Rebuilds the complete HTN planning tree from trace logs

This module reconstructs the search tree explored by the HTN planner using only
minimal local information from trace logs. No global state storage needed.
"""

import http.server
import json
import os
import re
import socketserver
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class NodeType(Enum):
    METHOD = " METHOD "  # Method applications with unifications
    DUMMY = "INFO_OP "  # Dummy method markers from preprocessing
    OPERATOR = "OPERATOR"  # Primitive operators
    SUCCESS = "  FINAL "  # Successful completion nodes
    UNKNOWN = "UNKNOWN "  # Unknown node type


@dataclass
class HtnPlanNode:
    """
    Lightweight representation of a node in the HTN planning tree.
    Contains only local information needed for tree reconstruction.
    """

    node_id: int
    depth: int = 0
    current_task: Optional[str] = None
    remaining_tasks: List[str] = field(default_factory=list)

    node_type: NodeType = NodeType.UNKNOWN
    parent_id: Optional[int] = None
    children: List[int] = field(default_factory=list)
    current_plan: List[str] = field(default_factory=list)

    # Variable unifications for the head of the method/operator, as well as anything carried from your parents
    substitution_unifier: Dict[str, str] = field(default_factory=dict)

    # Only used for SUCCESS nodes
    success: Optional[bool] = None

    parent_method_that_spawned_dummy: Optional[str] = None

    # Temporary data, stored to set up the children nodes
    # If the task unifies with a METHOD
    method_signature: Optional[str] = None
    if_unifier: Dict[str, str] = field(default_factory=dict)

    # If the task unifies with an operator
    operator_signature: Optional[str] = None
    operator_deletes: List[str] = field(default_factory=list)
    operator_adds: List[str] = field(default_factory=list)

    def _apply_unifier(self, string, unifier):
        """Apply a unifier to a string by replacing variables with their values."""
        for var, value in unifier.items():
            string = string.replace(var, value)
        return string

    def _unify_method(self) -> str:
        """Apply variable substitutions to show the unified method"""
        all_unifiers = {**self.substitution_unifier, **self.if_unifier}
        return self._apply_unifier(self.method_signature, all_unifiers)

    def _unify_operator(self) -> str:
        return self._apply_unifier(self.operator_signature, self.substitution_unifier)

    def _format_number(self, value: str) -> str:
        """Format numeric values to remove unnecessary trailing zeros"""
        try:
            # Try to parse as float
            num = float(value)
            if num.is_integer():
                return str(int(num))
            else:
                # Remove trailing zeros and decimal point if not needed
                formatted = f"{num:g}"
                return formatted
        except (ValueError, TypeError):
            return value

    def __str__(self) -> str:
        text = (
            " " * self.depth + f"Node {self.node_id}: [" + self.node_type.value + "] "
        )

        if self.node_type == NodeType.METHOD:
            text = text + self.current_task
        elif self.node_type == NodeType.DUMMY:
            text = text + self.parent_method_that_spawned_dummy
        elif self.node_type == NodeType.OPERATOR:
            text = text + self.operator_signature
        elif self.node_type == NodeType.SUCCESS:
            text = text + (
                "SUCCESS plan:(" + ", ".join(self.current_plan) + ")"
                if self.success
                else "FAILURE"
            )
        else:
            text = text + "<UNKNOWN>"

        return text


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
        return self.nodes

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

        content = trace[htn_pos + len("HtnPlanner::FindPlan") :].strip()

        # Parse different trace types
        if content.startswith("SOLVE"):
            self._parse_solve(content)
        elif content.startswith("METHOD"):
            self._parse_method(content)
        elif "substituted condition:" in content:
            self._parse_substituted_condition(content)
        elif "condition:" in content:
            self._parse_condition(content)
        elif content.startswith("OPERATOR"):
            self._parse_operator(content)
        elif content.startswith("PUSH"):
            self._parse_push(content)
        elif content.startswith("SUCCESS"):
            self._parse_success(content)
        elif content.startswith("FAIL"):
            self._parse_fail(content)

    def _parse_solve(self, content: str) -> None:
        # SOLVE      nodeID:0 task:'travel-to(park)' remaining:()
        match = re.search(
            r"nodeID:(\d+)\s+task:'([^']+)'\s+remaining:'([^']+)'", content
        )
        if match:
            node = self.get_node(int(match.group(1)))
            node.current_task = match.group(2)
            node.remaining_tasks = match.group(3)  # ERM
        else:
            print(f"Warning: Could not parse SOLVE trace: {content}")

    def _parse_method(self, content: str) -> None:
        # METHOD     nodeID:0 resolve next method 'travel-to(?q) => if(at(?p), first(walking-distance(?p,?q))), do(m1_travel-to(?q), walk(?p,?q))'
        match = re.search(r"nodeID:(\d+).*method\s+'([^']+)'", content)
        if match:
            node = self.get_node(int(match.group(1)))
            node.method_signature = match.group(2)
            node.node_type = NodeType.METHOD
        else:
            print(f"Warning: Could not parse METHOD trace: {content}")

    def _parse_push(self, content: str) -> None:
        """Parse PUSH nodeID:X parentID:Y"""
        match = re.search(r"nodeID:(\d+)\s+parentID:(\d+)", content)
        if match:
            child = self.get_node(int(match.group(1)))
            parent = self.get_node(int(match.group(2)))
            parent.children.append(child.node_id)
            child.parent_id = parent.node_id
            child.current_plan = parent.current_plan.copy()
            child.depth = parent.depth + 1

            # if parent.node_type == NodeType.METHOD:
            #     child.parent_method_that_spawned_me = parent._unify_method()
        else:
            print(f"Warning: Could not parse PUSH trace: {content}")

    def _parse_operator(self, content: str) -> None:
        # nodeID:1 Operator 'm1_travel-to(?q)' unifies with 'm1_travel-to(park)'
        match = re.search(
            r"nodeID:(\d+) Operator '([^']+)' unifies with '([^']+)'", content
        )
        if match:
            node = self.get_node(int(match.group(1)))
            node.operator_signature = match.group(3)
            node.node_type = NodeType.OPERATOR
            node.current_plan = node.current_plan.copy() + [match.group(3)]

            if self._is_dummy_method(node.current_task):
                node.node_type = NodeType.DUMMY
                parent = self.get_node(node.parent_id)
                node.parent_method_that_spawned_dummy = parent._unify_method()

        else:
            print(f"Warning: Could not parse OPERATOR trace: {content}")

    def _parse_success(self, content: str) -> None:
        """Parse SUCCESS nodeID:X no tasks remain"""
        match = re.search(r"nodeID:(\d+)", content)
        if match:
            node = self.get_node(int(match.group(1)))
            node.node_type = NodeType.SUCCESS
            node.success = True

    def _parse_fail(self, content: str) -> None:
        """Parse FAIL nodeID:X reason"""
        match = re.search(r"nodeID:(\d+)", content)
        if match:
            node = self.get_node(int(match.group(1)))
            node.node_type = NodeType.SUCCESS
            node.success = False

    def _parse_substituted_condition(self, content: str) -> None:
        # nodeID:0 substituted condition:'(at(?p), first(walking-distance(?p,park)))' with unifier '(?q = park)'
        match = re.search(
            r"nodeID:(\d+)\s+substituted condition:\s*'([^']+)' with unifier '([^']+)'",
            content,
        )
        if match:
            node = self.get_node(int(match.group(1)))
            substituted = match.group(2)
            node.substitution_unifier = self._extract_variable_assignments(
                match.group(3)
            )
        else:
            print(f"Warning: Could not parse substituted condition trace: {content}")

    def _extract_variable_assignments(self, unifier: str):
        # '(?q = park)'
        unifier = unifier.split("(")[1]
        unifier = unifier.split(")")[0]
        variable_assignment = [s.strip().split("=") for s in unifier.split(",")]
        variable_assignment = {
            var.strip(): val.strip() for var, val in variable_assignment
        }
        return variable_assignment

    def _parse_condition(self, content: str) -> None:
        # nodeID:0 condition:(?p = downtown)
        match = re.search(r"nodeID:(\d+)\s+condition:\s*'([^']+)", content)
        if match:
            node = self.get_node(int(match.group(1)))
            node.if_unifier = self._extract_variable_assignments(match.group(2))
        else:
            print(f"Warning: Could not parse condition trace: {content}")

    def get_root_node(self) -> None:
        """Find and set the root node (node with no parent)."""
        for node_id, node in self.nodes.items():
            if node.parent_id is None:
                self.root_node_id = node_id
                break

    def print_tree(
        self, node_id: Optional[int] = None, indent: int = 0, hide_dummy: bool = False
    ) -> None:
        """Print the tree structure starting from given node (or root)."""

        for node in self.nodes.values():
            print(node)
        return
        if node_id is None:
            node_id = self.root_node_id

        if node_id is None or node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # Skip dummy nodes if requested
        if hide_dummy and node.node_type == NodeType.DUMMY:
            # Print children directly without showing this dummy node
            for child_id in node.children:
                self.print_tree(child_id, indent, hide_dummy)
            return

        prefix = "  " * indent
        print(f"{prefix}{node}")

        # Print children
        for child_id in node.children:
            self.print_tree(child_id, indent + 1, hide_dummy)

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

    def get_node(self, node_id: int) -> HtnPlanNode:
        """Create or get existing node"""
        if node_id not in self.nodes:
            self.nodes[node_id] = HtnPlanNode(node_id=node_id)
        return self.nodes[node_id]

    def _is_dummy_method(self, task_signature: str) -> bool:
        """Check if a task is a dummy method (m[digit]+_pattern)"""
        if not task_signature:
            return False
        return bool(re.match(r"^m\d+_", task_signature))

    def _format_number(self, value: str) -> str:
        """Format numeric values to remove unnecessary trailing zeros"""
        try:
            # Try to parse as float
            num = float(value)
            if num.is_integer():
                return str(int(num))
            else:
                # Remove trailing zeros and decimal point if not needed
                formatted = f"{num:g}"
                return formatted
        except (ValueError, TypeError):
            return value

    def _find_successful_child(self, node_id: int) -> Optional[int]:
        """Find which child of this node led to success"""
        node = self.nodes.get(node_id)
        if not node:
            return None

        # Look for a child that has a successful path
        for child_id in node.children:
            child = self.nodes.get(child_id)
            if child and self._has_successful_path(child_id):
                return child_id

        return None

    def _has_successful_path(self, node_id: int) -> bool:
        """Check if there's a successful path starting from this node"""
        node = self.nodes.get(node_id)
        if not node:
            return False

        # If this is a leaf node, check if it's successful
        if not node.children:
            return node.success is True

        # If this node has children, check if any child has a successful path
        for child_id in node.children:
            if self._has_successful_path(child_id):
                return True

        return False

    def visualize(self, auto_open: bool = True, port: int = 8000) -> None:
        """Create interactive visualization and open in browser"""
        # Create standalone HTML with embedded JSON data
        json_data = self.to_json()
        html_content = self._create_html_template(json_data)
        html_file = "htn_tree_viewer.html"

        # Write to current directory
        full_path = os.path.abspath(html_file)
        with open(full_path, "w") as f:
            f.write(html_content)

        if auto_open:
            # Open directly in browser (no server needed)
            webbrowser.open(f"file://{full_path}")
            print(f"Visualization opened: file://{full_path}")
        else:
            print(f"Visualization file created: {full_path}")
            print(f"Open this file directly in your browser")

    def visualize_observable(self, auto_open: bool = True) -> None:
        """Create Observable-style D3 collapsible tree visualization and open in browser"""
        # Create standalone HTML with embedded JSON data
        json_data = self.to_json()
        html_content = self._create_observable_template(json_data)
        html_file = "htn_observable_tree.html"

        # Write to current directory
        full_path = os.path.abspath(html_file)
        with open(full_path, "w") as f:
            f.write(html_content)

        if auto_open:
            # Open directly in browser (no server needed)
            webbrowser.open(f"file://{full_path}")
            print(f"Observable-style visualization opened: file://{full_path}")
        else:
            print(f"Observable-style visualization file created: {full_path}")
            print(f"Open this file directly in your browser")

    def _create_html_template(self, json_data: str = None) -> str:
        """Create HTML template with D3.js visualization and embedded data"""
        from create_fixed_html import create_fixed_html

        return create_fixed_html(json_data or "null")

    def _create_observable_template(self, json_data: str = None) -> str:
        """Create Observable-style HTML template with D3.js visualization and embedded data"""
        from create_observable_html import create_observable_html

        return create_observable_html(json_data or "null")


if __name__ == "__main__":
    # Example usage

    example_traces = """
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan ALL BEGIN  Goals:(travel-to(park))
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan BEGIN      Find next plan
0903 22:48:40 =0.0000 HtnPlanner::FindPlan            SOLVE      nodeID:0 task:'travel-to(park)' remaining:'()'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                       nodeID:0 3 methods unify with 'travel-to(park)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan            METHOD     nodeID:0 resolve next method 'travel-to(?q) => if(at(?p), first(walking-distance(?p,?q))), do(m1_travel-to(?q), walk(?p,?q))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                       nodeID:0 substituted condition:'(at(?p), first(walking-distance(?p,park)))' with unifier '(?q = park)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan            HIGHESTMEM total:54108, stackSize:488, term strings:1868, term other:48944, shared rules: 2664
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan            HIGHESTMEM total:59659, Resolver:5551, term strings:1925, term other:49184, shared rules: 2664
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                       1 condition alternatives for method 'travel-to(?q) => if(at(?p), first(walking-distance(?p,?q))), do(m1_travel-to(?q), walk(?p,?q))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       nodeID:0 condition:'(?p = downtown)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       PUSH       nodeID:1 parentID:0
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       SOLVE      nodeID:1 task:'m1_travel-to(park)' remaining:'(walk(downtown,park))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       OPERATOR   nodeID:1 Operator 'm1_travel-to(?q)' unifies with 'm1_travel-to(park)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  isHidden: 0, deletes:'()', adds:'()'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  PUSH       nodeID:2 parentID:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  SOLVE      nodeID:2 task:'walk(downtown,park)' remaining:'()'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  OPERATOR   nodeID:2 Operator 'walk(?here,?there)' unifies with 'walk(downtown,park)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             isHidden: 0, deletes:'(at(downtown))', adds:'(at(park))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             PUSH       nodeID:3 parentID:2
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                             SUCCESS    nodeID:3 no tasks remain. Memory: Current:55949, Highest:59659, Budget:1000000
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             POP        nodeID:3 returnValue:1
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan END        Solution:'(m1_travel-to(park), walk(downtown,park))', Budget:1000000, HighestMemory:59659, ElapsedTime0.001097208
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan BEGIN      Find next plan
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  POP        nodeID:2 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       POP        nodeID:1 returnValue:1
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan            METHOD     nodeID:0 resolve next method 'travel-to(?y) => if(first(at(?x),at-taxi-stand(?t,?x),distance(?x,?y,?d),have-taxi-fare(?d))), do(m3_travel-to(?y), hail(?t,?x), ride(?t,?x,?y), pay-driver(+(1.50,?d)))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                       nodeID:0 substituted condition:'(first(at(?x),at-taxi-stand(?t,?x),distance(?x,park,?d),have-taxi-fare(?d)))' with unifier '(?y = park)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan            HIGHESTMEM total:63316, Resolver:8375, term strings:1925, term other:49784, shared rules: 2664
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                       1 condition alternatives for method 'travel-to(?y) => if(first(at(?x),at-taxi-stand(?t,?x),distance(?x,?y,?d),have-taxi-fare(?d))), do(m3_travel-to(?y), hail(?t,?x), ride(?t,?x,?y), pay-driver(+(1.50,?d)))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       nodeID:0 condition:'(?x = downtown, ?t = taxi1, ?d = 2)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       PUSH       nodeID:4 parentID:0
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                       SOLVE      nodeID:4 task:'m3_travel-to(park)' remaining:'(hail(taxi1,downtown), ride(taxi1,downtown,park), pay-driver(+(1.50,2)))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       OPERATOR   nodeID:4 Operator 'm3_travel-to(?y)' unifies with 'm3_travel-to(park)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  isHidden: 0, deletes:'()', adds:'()'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  PUSH       nodeID:5 parentID:4
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                  SOLVE      nodeID:5 task:'hail(taxi1,downtown)' remaining:'(ride(taxi1,downtown,park), pay-driver(+(1.50,2)))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                  OPERATOR   nodeID:5 Operator 'hail(?vehicle,?location)' unifies with 'hail(taxi1,downtown)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             isHidden: 0, deletes:'()', adds:'(at(taxi1,downtown))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             PUSH       nodeID:6 parentID:5
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             SOLVE      nodeID:6 task:'ride(taxi1,downtown,park)' remaining:'(pay-driver(+(1.50,2)))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             OPERATOR   nodeID:6 Operator 'ride(?vehicle,?a,?b)' unifies with 'ride(taxi1,downtown,park)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                        isHidden: 0, deletes:'(at(downtown), at(taxi1,downtown))', adds:'(at(park), at(taxi1,park))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                        PUSH       nodeID:7 parentID:6
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                        SOLVE      nodeID:7 task:'pay-driver(3.500000000)' remaining:'()'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                   nodeID:7 1 methods unify with 'pay-driver(3.500000000)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                        METHOD     nodeID:7 resolve next method 'pay-driver(?fare) => if(have-cash(?m), >=(?m,?fare)), do(m1_pay-driver(?fare), set-cash(?m,-(?m,?fare)))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                   nodeID:7 substituted condition:'(have-cash(?m), >=(?m,3.500000000))' with unifier '(?fare = 3.500000000)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                   1 condition alternatives for method 'pay-driver(?fare) => if(have-cash(?m), >=(?m,?fare)), do(m1_pay-driver(?fare), set-cash(?m,-(?m,?fare)))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                   nodeID:7 condition:'(?m = 12)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                   PUSH       nodeID:8 parentID:7
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                   SOLVE      nodeID:8 task:'m1_pay-driver(3.500000000)' remaining:'(set-cash(12,-(12,3.500000000)))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                   OPERATOR   nodeID:8 Operator 'm1_pay-driver(?fare)' unifies with 'm1_pay-driver(3.500000000)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                              isHidden: 0, deletes:'()', adds:'()'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                              PUSH       nodeID:9 parentID:8
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                              SOLVE      nodeID:9 task:'set-cash(12,8.500000000)' remaining:'()'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                              OPERATOR   nodeID:9 Operator 'set-cash(?old,?new)' unifies with 'set-cash(12,8.500000000)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                                         isHidden: 0, deletes:'(have-cash(12))', adds:'(have-cash(8.500000000))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                                         PUSH       nodeID:10 parentID:9
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                                         SUCCESS    nodeID:10 no tasks remain. Memory: Current:61219, Highest:63316, Budget:1000000
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                                         POP        nodeID:10 returnValue:1
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan END        Solution:'(m3_travel-to(park), hail(taxi1,downtown), ride(taxi1,downtown,park), m1_pay-driver(3.500000000), set-cash(12,8.500000000))', Budget:1000000, HighestMemory:63316, ElapsedTime0.001422625
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan BEGIN      Find next plan
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                              POP        nodeID:9 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                   POP        nodeID:8 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                        POP        nodeID:7 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             POP        nodeID:6 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  POP        nodeID:5 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       POP        nodeID:4 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan            METHOD     nodeID:0 resolve next method 'travel-to(?y) => if(at(?x), bus-route(?bus,?x,?y)), do(m3_travel-to(?y), wait-for(?bus,?x), pay-driver(1.00), ride(?bus,?x,?y))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       nodeID:0 substituted condition:'(at(?x), bus-route(?bus,?x,park))' with unifier '(?y = park)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       1 condition alternatives for method 'travel-to(?y) => if(at(?x), bus-route(?bus,?x,?y)), do(m3_travel-to(?y), wait-for(?bus,?x), pay-driver(1.00), ride(?bus,?x,?y))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                       nodeID:0 condition:'(?x = downtown, ?bus = bus1)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       PUSH       nodeID:11 parentID:0
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       SOLVE      nodeID:11 task:'m3_travel-to(park)' remaining:'(wait-for(bus1,downtown), pay-driver(1.00), ride(bus1,downtown,park))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                       OPERATOR   nodeID:11 Operator 'm3_travel-to(?y)' unifies with 'm3_travel-to(park)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  isHidden: 0, deletes:'()', adds:'()'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                  PUSH       nodeID:12 parentID:11
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                  SOLVE      nodeID:12 task:'wait-for(bus1,downtown)' remaining:'(pay-driver(1.00), ride(bus1,downtown,park))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  OPERATOR   nodeID:12 Operator 'wait-for(?bus,?location)' unifies with 'wait-for(bus1,downtown)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             isHidden: 0, deletes:'()', adds:'(at(bus1,downtown))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                             PUSH       nodeID:13 parentID:12
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                             SOLVE      nodeID:13 task:'pay-driver(1.00)' remaining:'(ride(bus1,downtown,park))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                        nodeID:13 1 methods unify with 'pay-driver(1.00)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                             METHOD     nodeID:13 resolve next method 'pay-driver(?fare) => if(have-cash(?m), >=(?m,?fare)), do(m1_pay-driver(?fare), set-cash(?m,-(?m,?fare)))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                        nodeID:13 substituted condition:'(have-cash(?m), >=(?m,1.00))' with unifier '(?fare = 1.00)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                        1 condition alternatives for method 'pay-driver(?fare) => if(have-cash(?m), >=(?m,?fare)), do(m1_pay-driver(?fare), set-cash(?m,-(?m,?fare)))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                        nodeID:13 condition:'(?m = 12)'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                        PUSH       nodeID:14 parentID:13
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                        SOLVE      nodeID:14 task:'m1_pay-driver(1.00)' remaining:'(set-cash(12,-(12,1.00)), ride(bus1,downtown,park))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                        OPERATOR   nodeID:14 Operator 'm1_pay-driver(?fare)' unifies with 'm1_pay-driver(1.00)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                   isHidden: 0, deletes:'()', adds:'()'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                   PUSH       nodeID:15 parentID:14
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                   SOLVE      nodeID:15 task:'set-cash(12,11.000000000)' remaining:'(ride(bus1,downtown,park))'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                   OPERATOR   nodeID:15 Operator 'set-cash(?old,?new)' unifies with 'set-cash(12,11.000000000)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                              isHidden: 0, deletes:'(have-cash(12))', adds:'(have-cash(11.000000000))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                              PUSH       nodeID:16 parentID:15
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                              SOLVE      nodeID:16 task:'ride(bus1,downtown,park)' remaining:'()'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                              OPERATOR   nodeID:16 Operator 'ride(?vehicle,?a,?b)' unifies with 'ride(bus1,downtown,park)'
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                                         isHidden: 0, deletes:'(at(downtown), at(bus1,downtown))', adds:'(at(park), at(bus1,park))'
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                                         PUSH       nodeID:17 parentID:16
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan                                                                                         SUCCESS    nodeID:17 no tasks remain. Memory: Current:61751, Highest:63316, Budget:1000000
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                                         POP        nodeID:17 returnValue:1
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan END        Solution:'(m3_travel-to(park), wait-for(bus1,downtown), m1_pay-driver(1.00), set-cash(12,11.000000000), ride(bus1,downtown,park))', Budget:1000000, HighestMemory:63316, ElapsedTime0.000762959
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan BEGIN      Find next plan
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                              POP        nodeID:16 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                                   POP        nodeID:15 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                                        POP        nodeID:14 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                             POP        nodeID:13 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                                  POP        nodeID:12 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan                       POP        nodeID:11 returnValue:1
0903 22:48:40 =0.0000 HtnPlanner::FindPlan            POP        nodeID:0 returnValue:1
0903 22:48:40 ^0.0000 HtnPlanner::FindPlan ALL END    Solution:'[ { (m1_travel-to(park), walk(downtown,park)) } { (m3_travel-to(park), hail(taxi1,downtown), ride(taxi1,downtown,park), m1_pay-driver(3.500000000), set-cash(12,8.500000000)) } { (m3_travel-to(park), wait-for(bus1,downtown), m1_pay-driver(1.00), set-cash(12,11.000000000), ride(bus1,downtown,park)) } ]', Budget:1000000, HighestMemory:63316        """

    example_traces = example_traces.strip().split("\n")
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
