# InductorHTN MCP Server

MCP server for AI assistant integration with InductorHTN.

## Quick Start

### Install
```bash
cd mcp-server
pip install -e .
```

### Run
```bash
# Default path
indhtn-mcp

# Custom path
indhtn-mcp /path/to/indhtn
```

## Environment Variables

```bash
INDHTN_PATH=/path/to/indhtn        # Default: ./build/Release/indhtn
INDHTN_MAX_SESSIONS=10             # Default: 10
INDHTN_LOG_LEVEL=DEBUG             # Default: INFO
```

## Troubleshooting

### Session hangs
Check timeout settings, try reset command.

### File not found
Use absolute paths for HTN files.

### Memory issues
Reduce max sessions or restart server.
