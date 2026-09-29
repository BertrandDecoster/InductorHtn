# optimization-proofs

Proof harness for the validated optimization patterns in
`docs/reference/ruleset-writing.md`. Each pattern is a `(slow, fast)` pair of
`.pl` rulesets that compute the SAME answer; `measure.py` runs the same query
against both and reports the Prolog resolution-step delta
(`GetLastResolutionStepCount()`).

```bash
source .venv/bin/activate
python prototypes/optimization-proofs/measure.py
```

Requires an engine built with resolution tracking (`INDHTN_TRACK_RESOLUTION_STEPS=ON`,
the default). Numbers are engine-specific; re-run to refresh the doc's table.

Note: first-argument indexing is deliberately absent — it measured identical
steps and wall-clock (slow == fast at 8000 facts) on this engine, so it is not a
recommended InductorHTN optimization.
