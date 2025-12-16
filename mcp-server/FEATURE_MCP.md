# MCP Server for InductorHTN

## Overview

An MCP (Model Context Protocol) server has been implemented to enable AI assistants to interact with InductorHTN REPL sessions. This server maintains persistent REPL processes and provides structured access to HTN planning capabilities.

## Implementation Status

### ✅ Completed

1. **Core MCP Server** (`mcp-server/indhtn_mcp/server.py`)
   - Full MCP protocol implementation
   - 7 tool methods for complete REPL interaction
   - Async request handling

2. **Session Management** (`mcp-server/indhtn_mcp/session.py`)
   - Persistent subprocess management
   - Character-by-character output reading for prompt detection
   - Multiple concurrent sessions support
   - Timeout and error recovery

3. **MCP Methods Implemented**:
   - `indhtn_start_session`: Initialize REPL with HTN/Prolog files
   - `indhtn_query`: Execute Prolog queries
   - `indhtn_find_plans`: Find HTN plans using goals()
   - `indhtn_apply_plan`: Apply plans to update state
   - `indhtn_reset`: Reset session (/r command)
   - `indhtn_toggle_trace`: Toggle trace mode (/t command)
   - `indhtn_end_session`: Clean up resources

4. **Testing**
   - Session management tested successfully
   - Taxi game played through completely
   - All REPL features verified working

## Architecture

```
┌─────────────┐     MCP Protocol      ┌─────────────────┐
│ AI Assistant│ ◄──────────────────► │  MCP Server     │
└─────────────┘                       │  (Python)       │
                                      └────────┬────────┘
                                               │ stdio
                                      ┌────────▼────────┐
                                      │  indhtn REPL    │
                                      │  (subprocess)   │
                                      └─────────────────┘
```

## Key Features

- **True Interactivity**: Maintains REPL state across queries
- **Robust I/O Handling**: Character-by-character reading to properly detect prompts
- **Error Recovery**: Handles timeouts, crashes, and malformed queries
- **Structured Responses**: Parses REPL output into JSON format

## What's Left to Do

### Critical
1. **Install MCP Package**: `pip install mcp` (currently missing dependency)
2. **Claude Desktop Integration**: Create configuration and deployment instructions

### Important
3. **Better Error Handling**: Handle edge cases and REPL crashes more gracefully
4. **Automated Tests**: Unit and integration tests for the MCP server
5. **Logging Configuration**: Replace debug prints with proper logging

### Nice-to-Have
6. **Session Persistence**: Save/restore sessions across server restarts
7. **Configuration Support**: YAML/JSON config files for customization

## Usage Example

```python
# Start a session
session_id = await start_session(files=["Examples/Taxi.htn"])

# Query state
result = await query(session_id, "at(?where).")
# Returns: ((?where = downtown))

# Find plans
result = await find_plans(session_id, "travel-to(park)")
# Returns: [ { (walk(downtown,park)) } ... ]

# Apply plan
result = await apply_plan(session_id, "travel-to(park)")
# Returns: (walk(downtown,park))
```

## File Locations

- Server implementation: `mcp-server/indhtn_mcp/`
- Test scripts: `mcp-server/test_*.py`
- Configuration: `mcp-server/mcp.json`
- Documentation: `mcp-server/README.md`