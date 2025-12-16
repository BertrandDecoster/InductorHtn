"""MCP Server implementation for InductorHTN REPL"""

import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from typing import List, Optional, Any

# Add gui/backend to path for htn_linter import (only once at module load)
_gui_backend_path = str(Path(__file__).parent.parent.parent / "gui" / "backend")
if _gui_backend_path not in sys.path:
    sys.path.insert(0, _gui_backend_path)

# Try to import htn_linter, provide clear error if unavailable
try:
    from htn_linter import lint_htn
    _LINTER_AVAILABLE = True
except ImportError as e:
    _LINTER_AVAILABLE = False
    _LINTER_IMPORT_ERROR = str(e)
    lint_htn = None

# Try to import htn_parser, provide clear error if unavailable
try:
    from htn_parser import parse_htn
    _PARSER_AVAILABLE = True
except ImportError as e:
    _PARSER_AVAILABLE = False
    _PARSER_IMPORT_ERROR = str(e)
    parse_htn = None

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    TextContent,
    EmptyContent,
    error_response
)

from .session import SessionManager

logger = logging.getLogger(__name__)


class IndHTNMCPServer:
    """MCP Server for InductorHTN REPL interaction"""
    
    def __init__(self, indhtn_path: str = "./build/Release/indhtn"):
        self.indhtn_path = Path(indhtn_path).resolve()
        if not self.indhtn_path.exists():
            raise FileNotFoundError(f"InductorHTN executable not found at {self.indhtn_path}")
            
        self.session_manager = SessionManager(str(self.indhtn_path))
        self.server = Server("indhtn-repl")
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Register all MCP tool handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """Return the list of available tools"""
            return [
                Tool(
                    name="indhtn_start_session",
                    description="Start a new InductorHTN REPL session with specified files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of .htn or .pl files to load"
                            },
                            "workingDir": {
                                "type": "string",
                                "description": "Working directory for file resolution"
                            }
                        },
                        "required": ["files"]
                    }
                ),
                Tool(
                    name="indhtn_query",
                    description="Execute a Prolog query in the REPL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "Session ID from start_session"
                            },
                            "query": {
                                "type": "string",
                                "description": "Prolog query (e.g., 'at(?where).')"
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Timeout in seconds",
                                "default": 10
                            }
                        },
                        "required": ["sessionId", "query"]
                    }
                ),
                Tool(
                    name="indhtn_find_plans",
                    description="Find HTN plans for a goal using goals() query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "Session ID"
                            },
                            "goal": {
                                "type": "string",
                                "description": "HTN goal (e.g., 'travel-to(park)')"
                            },
                            "maxPlans": {
                                "type": "integer",
                                "description": "Maximum number of plans to return"
                            }
                        },
                        "required": ["sessionId", "goal"]
                    }
                ),
                Tool(
                    name="indhtn_apply_plan",
                    description="Apply an HTN plan and update the state using apply() query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "Session ID"
                            },
                            "goal": {
                                "type": "string",
                                "description": "HTN goal to apply"
                            }
                        },
                        "required": ["sessionId", "goal"]
                    }
                ),
                Tool(
                    name="indhtn_reset",
                    description="Reset the REPL session, reloading all files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "Session ID"
                            }
                        },
                        "required": ["sessionId"]
                    }
                ),
                Tool(
                    name="indhtn_toggle_trace",
                    description="Toggle trace mode on/off for debugging",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "Session ID"
                            }
                        },
                        "required": ["sessionId"]
                    }
                ),
                Tool(
                    name="indhtn_end_session",
                    description="End a REPL session and clean up resources",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "Session ID to end"
                            }
                        },
                        "required": ["sessionId"]
                    }
                ),
                Tool(
                    name="indhtn_lint",
                    description="Lint HTN/Prolog source code and return structured diagnostics with line numbers, error codes, and severity levels",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "HTN/Prolog source code to lint"
                            }
                        },
                        "required": ["source"]
                    }
                ),
                Tool(
                    name="indhtn_introspect",
                    description="Parse HTN source and return all methods, operators, facts, and predicates with their signatures and locations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "HTN/Prolog source code to analyze"
                            }
                        },
                        "required": ["source"]
                    }
                ),
                Tool(
                    name="indhtn_state_diff",
                    description="Preview what plan would be generated for a goal without applying it",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "Session ID from indhtn_start_session"
                            },
                            "goal": {
                                "type": "string",
                                "description": "HTN goal to plan for (e.g., 'travel-to(park)')"
                            }
                        },
                        "required": ["sessionId", "goal"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool invocations"""
            try:
                if name == "indhtn_start_session":
                    return await self._start_session(arguments)
                elif name == "indhtn_query":
                    return await self._query(arguments)
                elif name == "indhtn_find_plans":
                    return await self._find_plans(arguments)
                elif name == "indhtn_apply_plan":
                    return await self._apply_plan(arguments)
                elif name == "indhtn_reset":
                    return await self._reset(arguments)
                elif name == "indhtn_toggle_trace":
                    return await self._toggle_trace(arguments)
                elif name == "indhtn_end_session":
                    return await self._end_session(arguments)
                elif name == "indhtn_lint":
                    return await self._lint(arguments)
                elif name == "indhtn_introspect":
                    return await self._introspect(arguments)
                elif name == "indhtn_state_diff":
                    return await self._state_diff(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in {name}: {e}", exc_info=True)
                return error_response(str(e))
    
    async def _start_session(self, args: dict) -> List[TextContent]:
        """Start a new REPL session"""
        files = args["files"]
        working_dir = args.get("workingDir")
        
        # Validate files exist
        for file in files:
            file_path = Path(working_dir or ".") / file
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file}")
        
        session_id, compilation_output = await self.session_manager.create_session(files, working_dir)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "sessionId": session_id,
                "loadResults": compilation_output,
                "status": "ready"
            }, indent=2)
        )]
    
    async def _query(self, args: dict) -> List[TextContent]:
        """Execute a Prolog query"""
        session_id = args["sessionId"]
        query = args["query"]
        timeout = args.get("timeout", 10.0)
        
        result = await self.session_manager.execute_query(session_id, query, timeout)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _find_plans(self, args: dict) -> List[TextContent]:
        """Find HTN plans for a goal"""
        session_id = args["sessionId"]
        goal = args["goal"]
        max_plans = args.get("maxPlans")
        
        # Use goals() query format
        query = f"goals({goal})"
        result = await self.session_manager.execute_query(session_id, query)
        
        if result["success"]:
            # Parse plan output
            plans = self._parse_plans(result["output"])
            
            if max_plans and len(plans) > max_plans:
                plans = plans[:max_plans]
                
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "plans": plans,
                    "planCount": len(plans),
                    "raw_output": result["output"]
                }, indent=2)
            )]
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": result.get("message", "Failed to find plans"),
                    "raw_output": result["output"]
                }, indent=2)
            )]
    
    async def _apply_plan(self, args: dict) -> List[TextContent]:
        """Apply an HTN plan to the current state"""
        session_id = args["sessionId"]
        goal = args["goal"]
        
        # Use apply() query format
        query = f"apply({goal})"
        result = await self.session_manager.execute_query(session_id, query)
        
        if result["success"]:
            # Parse application results
            actions, new_state = self._parse_application(result["output"])
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "actionsApplied": actions,
                    "newState": new_state,
                    "raw_output": result["output"]
                }, indent=2)
            )]
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": result.get("message", "Failed to apply plan"),
                    "raw_output": result["output"]
                }, indent=2)
            )]
    
    async def _reset(self, args: dict) -> List[TextContent]:
        """Reset the REPL session"""
        session_id = args["sessionId"]
        
        result = await self.session_manager.execute_query(session_id, "/r")
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "Session reset successfully",
                "output": result["output"]
            }, indent=2)
        )]
    
    async def _toggle_trace(self, args: dict) -> List[TextContent]:
        """Toggle trace mode"""
        session_id = args["sessionId"]
        
        result = await self.session_manager.execute_query(session_id, "/t")
        
        # Check if trace was enabled or disabled
        session = self.session_manager.sessions.get(session_id)
        if session:
            session.trace_enabled = not session.trace_enabled
            trace_status = session.trace_enabled
        else:
            trace_status = None
            
        return [TextContent(
            type="text",
            text=json.dumps({
                "traceEnabled": trace_status,
                "message": f"Trace mode {'enabled' if trace_status else 'disabled'}",
                "output": result["output"]
            }, indent=2)
        )]
    
    async def _end_session(self, args: dict) -> List[TextContent]:
        """End a REPL session"""
        session_id = args["sessionId"]
        
        await self.session_manager.end_session(session_id)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "Session ended successfully",
                "sessionId": session_id
            }, indent=2)
        )]
    
    def _parse_plans(self, output: str) -> List[List[str]]:
        """Parse plan output into structured format"""
        plans = []
        
        # Plans typically come as: [ { (action1, action2, ...) } ]
        # or multiple plans: [ { (plan1) }, { (plan2) } ]
        
        # Simple parsing - can be enhanced based on actual output format
        if "[ {" in output:
            # Find all plan blocks
            import re
            plan_pattern = r'\{\s*\((.*?)\)\s*\}'
            matches = re.findall(plan_pattern, output, re.DOTALL)
            
            for match in matches:
                # Split actions by comma
                actions = [a.strip() for a in match.split(',') if a.strip()]
                if actions:
                    plans.append(actions)
        
        return plans
    
    def _parse_application(self, output: str) -> tuple[List[str], str]:
        """Parse apply() output to extract actions and final state"""
        # This is a simplified parser - enhance based on actual output
        actions = []
        state_lines = []

        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('>>') or line.startswith('yes'):
                # Skip result indicators
                continue
            elif ':-' in line or 'add(' in line or 'del(' in line:
                # Likely an action
                actions.append(line)
            elif line and not line.startswith('?-'):
                # Likely state information
                state_lines.append(line)

        return actions, '\n'.join(state_lines)

    async def _lint(self, args: dict) -> List[TextContent]:
        """Lint HTN source and return structured diagnostics."""
        if not _LINTER_AVAILABLE:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Linter not available: {_LINTER_IMPORT_ERROR}",
                    "diagnostics": [],
                    "error_count": 0,
                    "warning_count": 0
                }, indent=2)
            )]

        source = args.get("source", "")
        diagnostics = lint_htn(source)

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "diagnostics": diagnostics,
                "error_count": len([d for d in diagnostics if d.get("severity") == "error"]),
                "warning_count": len([d for d in diagnostics if d.get("severity") == "warning"])
            }, indent=2)
        )]

    async def _introspect(self, args: dict) -> List[TextContent]:
        """Parse HTN source and return structure information."""
        if not _PARSER_AVAILABLE:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Parser not available: {_PARSER_IMPORT_ERROR}",
                    "methods": [],
                    "operators": [],
                    "facts": [],
                    "method_count": 0,
                    "operator_count": 0,
                    "fact_count": 0
                }, indent=2)
            )]

        source = args.get("source", "")
        rules, diagnostics = parse_htn(source)

        methods = []
        operators = []
        facts = []

        for rule in rules:
            item = {
                "name": rule.head.name,
                "arity": len(rule.head.args),
                "signature": f"{rule.head.name}({', '.join(a.name for a in rule.head.args)})",
                "line": rule.line
            }
            if rule.is_method:
                item["has_else"] = rule.has_else
                item["has_allof"] = rule.has_allof
                item["has_anyof"] = rule.has_anyof
                methods.append(item)
            elif rule.is_operator:
                item["has_hidden"] = rule.has_hidden
                operators.append(item)
            elif rule.is_fact:
                facts.append(item)

        # Convert diagnostics to dicts for JSON
        parse_errors = [d.to_dict() if hasattr(d, 'to_dict') else d for d in diagnostics]

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "methods": methods,
                "operators": operators,
                "facts": facts,
                "method_count": len(methods),
                "operator_count": len(operators),
                "fact_count": len(facts),
                "parse_errors": parse_errors
            }, indent=2)
        )]

    async def _state_diff(self, args: dict) -> List[TextContent]:
        """Get state diff for a goal without applying it."""
        session_id = args.get("sessionId")
        goal = args.get("goal", "")

        if not session_id:
            raise ValueError("sessionId is required")

        if not goal:
            raise ValueError("goal is required")

        result = await self.session_manager.get_state_diff(session_id, goal)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def run(self):
        """Run the MCP server"""
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info(f"Starting InductorHTN MCP Server with executable: {self.indhtn_path}")
        
        # Run the server
        async with self.server:
            options = InitializationOptions(
                server_name="indhtn-repl",
                server_version="1.0.0",
                capabilities=self.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
            await self.server.run(options)


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        indhtn_path = sys.argv[1]
    else:
        # Try common locations
        possible_paths = [
            "./build/Release/indhtn",
            "./build/Debug/indhtn",
            "./indhtn",
            "/usr/local/bin/indhtn"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                indhtn_path = path
                break
        else:
            print("Error: Could not find indhtn executable")
            print("Please provide path as argument: python -m indhtn_mcp.server /path/to/indhtn")
            sys.exit(1)
    
    server = IndHTNMCPServer(indhtn_path)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()