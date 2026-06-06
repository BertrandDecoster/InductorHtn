# Interactive REPL (`indhtn`)

Quick interactive exploration of a ruleset.

```bash
./build/Release/indhtn.exe Examples/Taxi.htn
```

## Commands

| Command | Purpose |
|---------|---------|
| `at(?x).` | Query current facts (e.g. list all `at` facts) |
| `goals(travel-to(park)).` | Find plans **without** applying them |
| `apply(travel-to(park)).` | Find plans **and** apply the state changes |
| `/t` | Toggle tracing (see method decomposition) |
| `/r` | Reset and reload the file |

**Listing all facts:** query each predicate, e.g. `at(?x).`, `have-cash.`.

## When to use it

| Goal | Best tool |
|------|-----------|
| Quick interactive testing | `indhtn` REPL (this tool) |
| List all facts programmatically | Python `GetStateFacts()` — see [`python-bindings.md`](python-bindings.md) |
| Visual state diff | Web IDE — see [`gui.md`](gui.md) |
| AI-driven stepping | MCP server — see [`mcp-server.md`](mcp-server.md) |

For the full crafting/understanding workflow see
[`../reference/authoring-rulesets.md`](../reference/authoring-rulesets.md).
