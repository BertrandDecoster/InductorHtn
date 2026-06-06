# Unit Test Runner (`runtests`)

Runs the C++ unit test suite (HTN engine + Prolog engine + parser).

```bash
# Build first
cmake --build ./build --config Release

# Run
./build/Release/runtests.exe        # Windows
./build/runtests                    # macOS (binary lands directly in build/)
```

> **macOS note:** the build places binaries directly in `build/`, not
> `build/Release/`. Use `./build/runtests`.

## Related test entry points

| Suite | How | Page |
|-------|-----|------|
| C++ unit tests | `runtests` (this tool) | — |
| Python HTN test suite | `python htn_test_suite.py` | [`python-bindings.md`](python-bindings.md) |
| Component tests | `python -m htn_components test-all` | [`htn-components.md`](htn-components.md) |
| MCP parity tests | `cd mcp-server && python -m pytest tests/` | [`mcp-server.md`](mcp-server.md) |
| GUI backend tests | `python gui/test_backend.py` | [`gui.md`](gui.md) |
| Documentation lint | `python scripts/docs_lint.py` | — |

See [`../../BUILD.md`](../../BUILD.md) for build configuration details.

## Documentation lint

`scripts/docs_lint.py` mechanically checks that the docs still match the code:
every documented MCP tool, Flask endpoint, Python binding method, and
`htn_components` command must exist in the source, and active docs must cite
**symbol names, not `file:line` numbers** (which rot on every edit). It exits
non-zero on a broken reference — wire it into CI to keep docs honest.
