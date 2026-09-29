# HTN (InductorHTN) Syntax — VS Code extension

Syntax highlighting for InductorHTN `.htn` rulesets. `.htn` is Prolog syntax with an HTN layer
on top, so this grammar colors `%` / `/* */` comments, `?var` / `_var` variables, clause/predicate
heads, the HTN keywords (`if do del add else anyOf allOf hidden parallel try first increase
decrease`), Prolog builtins, operators, and numbers.

Following the convention used by the PDDL and Prolog VS Code extensions, the grammar only assigns
**TextMate scopes** — your active color theme decides the actual colors. The recommended dark
colors below are documentation, not forced.

## Token taxonomy

| Category | Examples | TextMate scope | Recommended dark color |
|---|---|---|---|
| Line comment | `% ...` | `comment.line.percentage.htn` | `#6A9955` green, italic |
| Block comment | `/* ... */` | `comment.block.htn` | `#6A9955` green, italic |
| Variable | `?from`, `?h`, `_x` | `variable.parameter.htn` | `#9CDCFE` light blue |
| Rule / head name | `travel` in `travel(?a) :-` | `entity.name.function.htn` | `#DCDCAA` yellow |
| HTN keyword | `if do del add else anyOf allOf hidden parallel try first increase decrease` | `keyword.control.htn` | `#C586C0` purple |
| Prolog builtin | `not and findall forall is assert retract write …` | `support.function.builtin.htn` | `#4EC9B0` teal |
| Rule operator | `:-` | `keyword.operator.rule.htn` | `#FF5555` bright red, bold |
| Comparison / arith / cut | `\== == =< >= < > = + - * / !` | `keyword.operator.htn` | `#D4D4D4` gray |
| Number | `42`, `3.14` | `constant.numeric.htn` | `#B5CEA8` light green |
| String | `"..."` | `string.quoted.double.htn` | `#CE9178` orange |

> TextMate cannot tell a clause head from a body call on a single line (a known limitation shared
> by the Prolog extensions), so every `name(` is scoped as `entity.name.function.htn`. This reads
> well in practice: predicate names stand out, bare atoms stay default.

## Install

**Quick (symlink into your extensions folder):**

```bash
ln -s "$(pwd)/editors/vscode-htn" ~/.vscode/extensions/htn-syntax
```

Then reload VS Code (`Cmd+Shift+P` → "Developer: Reload Window"). Open any `.htn` file.

**Develop:** open `editors/vscode-htn` in VS Code and press `F5` to launch an Extension
Development Host with the extension loaded.

**Package as `.vsix`** (optional): `npm i -g @vscode/vsce && vsce package`, then
`code --install-extension htn-syntax-0.1.0.vsix`.

## Force the exact dark colors (optional)

The grammar defers to your theme. If you want the recommended colors regardless of theme, drop
this into your VS Code `settings.json`:

```jsonc
"editor.tokenColorCustomizations": {
  "textMateRules": [
    { "scope": "comment.line.percentage.htn",   "settings": { "foreground": "#6A9955", "fontStyle": "italic" } },
    { "scope": "comment.block.htn",             "settings": { "foreground": "#6A9955", "fontStyle": "italic" } },
    { "scope": "variable.parameter.htn",        "settings": { "foreground": "#9CDCFE" } },
    { "scope": "entity.name.function.htn",      "settings": { "foreground": "#DCDCAA" } },
    { "scope": "keyword.control.htn",           "settings": { "foreground": "#C586C0" } },
    { "scope": "support.function.builtin.htn",  "settings": { "foreground": "#4EC9B0" } },
    { "scope": "keyword.operator.rule.htn",     "settings": { "foreground": "#FF5555", "fontStyle": "bold" } },
    { "scope": "keyword.operator.htn",          "settings": { "foreground": "#D4D4D4" } },
    { "scope": "constant.numeric.htn",          "settings": { "foreground": "#B5CEA8" } },
    { "scope": "string.quoted.double.htn",      "settings": { "foreground": "#CE9178" } }
  ]
}
```

## Verify scopes

Open a `.htn` file, run `Cmd+Shift+P` → **"Developer: Inspect Editor Tokens and Scopes"**, and click
a token. `?w1` should report `variable.parameter.htn`; `parallel` should report `keyword.control.htn`.
