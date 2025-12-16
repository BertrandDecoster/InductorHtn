---
description: MCP server for AI assistant integration
globs: mcp-server/**
---

# MCP Server

Model Context Protocol server enabling AI assistants to interact with InductorHTN REPL sessions.

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

## File Structure

```
mcp-server/
├── indhtn_mcp/
│   ├── server.py    # MCP protocol implementation
│   └── session.py   # REPL subprocess management
├── mcp.json         # Configuration
└── setup.py         # Package installation
```

## MCP Tools

7 tool methods implemented in `server.py`:

| Tool | Description |
|------|-------------|
| `indhtn_start_session` | Initialize REPL with HTN/Prolog files |
| `indhtn_query` | Execute Prolog queries |
| `indhtn_find_plans` | Find HTN plans using goals() |
| `indhtn_apply_plan` | Apply plans to update state |
| `indhtn_reset` | Reset session (/r command) |
| `indhtn_toggle_trace` | Toggle trace mode (/t command) |
| `indhtn_end_session` | Clean up resources |

## Session Management (session.py)

- Persistent subprocess management
- Character-by-character output reading for prompt detection
- Multiple concurrent sessions support
- Timeout and error recovery

Key class: `SessionManager`
- Creates and tracks REPL subprocess per session
- Handles I/O with proper prompt detection
- Implements timeout handling

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INDHTN_PATH` | `./build/Release/indhtn` | Path to indhtn executable |
| `INDHTN_MAX_SESSIONS` | 10 | Maximum concurrent sessions |
| `INDHTN_LOG_LEVEL` | INFO | Logging level |

## Adding New Tools

1. Add tool definition in `server.py`:
```python
@server.tool()
async def indhtn_new_tool(session_id: str, param: str) -> dict:
    """Tool description."""
    session = session_manager.get_session(session_id)
    result = await session.execute_command(...)
    return {"result": result}
```

2. Register in tool list if needed

## Error Handling

- Session timeouts return error response
- Crashed sessions can be recovered via reset
- All responses include `success` boolean field

## Testing

Test scripts in `mcp-server/test_*.py`:
- Session creation/destruction
- Query execution
- Plan finding and application
