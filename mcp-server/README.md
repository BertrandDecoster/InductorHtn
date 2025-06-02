# InductorHTN MCP Server

An MCP (Model Context Protocol) server that enables AI assistants to interact with InductorHTN REPL sessions. This server maintains persistent REPL processes and provides structured access to HTN planning capabilities.

## Features

- **Persistent Sessions**: Maintain multiple concurrent REPL sessions
- **Interactive Queries**: Execute Prolog queries and HTN planning operations
- **State Management**: Track session state and handle errors gracefully
- **Async Design**: Non-blocking operations for better performance

## Installation

1. Ensure InductorHTN is built:
```bash
cd ..
mkdir build && cd build
cmake -G "Unix Makefiles" ../src
cmake --build ./ --config Release
```

2. Install the MCP server:
```bash
cd mcp-server
pip install -e .
```

## Usage

### Starting the Server

```bash
# Use default path (./build/Release/indhtn)
indhtn-mcp

# Or specify custom path
indhtn-mcp /path/to/indhtn
```

### Available Tools

The server exposes the following tools via MCP:

#### `indhtn_start_session`
Start a new REPL session with HTN/Prolog files.

**Parameters:**
- `files`: List of .htn or .pl files to load
- `workingDir`: Optional working directory

**Returns:**
- `sessionId`: Unique session identifier
- `loadResults`: Compilation output
- `status`: Session status

#### `indhtn_query`
Execute a Prolog query in a session.

**Parameters:**
- `sessionId`: Session ID from start_session
- `query`: Prolog query (e.g., "at(?where).")
- `timeout`: Optional timeout in seconds

**Returns:**
- `success`: Whether query succeeded
- `output`: Query results

#### `indhtn_find_plans`
Find HTN plans for a goal.

**Parameters:**
- `sessionId`: Session ID
- `goal`: HTN goal (e.g., "travel-to(park)")
- `maxPlans`: Optional limit on plans

**Returns:**
- `success`: Whether planning succeeded
- `plans`: List of action sequences
- `planCount`: Total number of plans found

#### `indhtn_apply_plan`
Apply an HTN plan to update the current state.

**Parameters:**
- `sessionId`: Session ID
- `goal`: HTN goal to apply

**Returns:**
- `success`: Whether application succeeded
- `actionsApplied`: List of actions executed
- `newState`: Updated state

#### `indhtn_reset`
Reset a session, reloading all files.

**Parameters:**
- `sessionId`: Session ID

#### `indhtn_toggle_trace`
Toggle trace mode for debugging.

**Parameters:**
- `sessionId`: Session ID

**Returns:**
- `traceEnabled`: New trace status

#### `indhtn_end_session`
End a session and clean up resources.

**Parameters:**
- `sessionId`: Session ID

## Configuration

The server can be configured via environment variables:

- `INDHTN_PATH`: Path to indhtn executable (default: ./build/Release/indhtn)
- `INDHTN_MAX_SESSIONS`: Maximum concurrent sessions (default: 10)
- `INDHTN_LOG_LEVEL`: Logging level (default: INFO)

## Example Usage with Claude

Once the MCP server is running and configured in Claude Desktop, you can:

1. Start a session:
```
Use indhtn_start_session with files ["Examples/Taxi.htn"]
```

2. Query the knowledge base:
```
Use indhtn_query with sessionId "..." and query "at(?where)."
```

3. Find plans:
```
Use indhtn_find_plans with sessionId "..." and goal "travel-to(suburb)"
```

4. Apply plans to see state changes:
```
Use indhtn_apply_plan with sessionId "..." and goal "travel-to(suburb)"
```

## Architecture

The server consists of three main components:

1. **Session Manager**: Handles multiple REPL processes
2. **MCP Handler**: Translates between MCP protocol and REPL commands
3. **Output Parser**: Structures REPL output into JSON responses

## Development

To run tests:
```bash
python -m pytest tests/
```

To enable debug logging:
```bash
INDHTN_LOG_LEVEL=DEBUG indhtn-mcp
```

## Troubleshooting

### REPL Process Hangs
The server includes timeout handling and recovery mechanisms. If a query times out, the server will attempt to recover the session.

### Memory Issues
Each session runs in a separate process. The server limits concurrent sessions to prevent resource exhaustion.

### File Not Found
Ensure file paths are relative to the working directory specified in start_session, or use absolute paths.