// Registers the `.htn` language in Monaco: a Monarch tokenizer that mirrors the
// VS Code TextMate grammar in editors/vscode-htn/, plus an `htn-dark` theme that
// colors the token types per the documented dark palette. Keep the keyword and
// builtin lists in lockstep with syntaxes/htn.tmLanguage.json so both editors agree.

const HTN_KEYWORDS = [
  'if', 'do', 'del', 'add', 'else', 'anyOf', 'allOf',
  'hidden', 'parallel', 'try', 'first', 'increase', 'decrease',
]

const HTN_BUILTINS = [
  'not', 'and', 'or', 'forall', 'findall', 'count', 'distinct', 'sortBy',
  'is', 'assert', 'retract', 'retractall', 'write', 'writeln', 'print', 'nl',
  'max', 'min', 'sum', 'abs', 'float', 'integer',
  'atom_chars', 'atom_concat', 'downcase_atom', 'atomic',
]

let registered = false

export function registerHtn(monaco) {
  if (registered) return
  registered = true

  monaco.languages.register({ id: 'htn', extensions: ['.htn'], aliases: ['HTN', 'htn'] })

  monaco.languages.setLanguageConfiguration('htn', {
    comments: { lineComment: '%', blockComment: ['/*', '*/'] },
    brackets: [['(', ')'], ['[', ']']],
    autoClosingPairs: [
      { open: '(', close: ')' },
      { open: '[', close: ']' },
      { open: '"', close: '"' },
    ],
    surroundingPairs: [
      { open: '(', close: ')' },
      { open: '[', close: ']' },
      { open: '"', close: '"' },
    ],
  })

  monaco.languages.setMonarchTokensProvider('htn', {
    defaultToken: '',
    keywords: HTN_KEYWORDS,
    builtins: HTN_BUILTINS,
    tokenizer: {
      root: [
        [/%.*$/, 'comment'],
        [/\/\*/, 'comment', '@comment'],
        [/[?_][A-Za-z0-9_]*/, 'variable'],
        [/-?\d+(\.\d+)?/, 'number'],
        [/"/, 'string', '@string'],
        [/:-/, 'operator.rule'],
        // Identifier followed by `(` => keyword / builtin / rule-head (function).
        [/[a-z][A-Za-z0-9_]*(?=\s*\()/, {
          cases: { '@keywords': 'keyword', '@builtins': 'predefined', '@default': 'type' },
        }],
        // Bare identifier (atom, or a keyword/builtin used without parens like `else`).
        [/[a-z][A-Za-z0-9_]*/, {
          cases: { '@keywords': 'keyword', '@builtins': 'predefined', '@default': 'identifier' },
        }],
        [/\\==|=<|>=|==|\\=|<|>|=|\+|\*|\/|!|-/, 'operator'],
      ],
      comment: [
        [/[^/*]+/, 'comment'],
        [/\*\//, 'comment', '@pop'],
        [/[/*]/, 'comment'],
      ],
      string: [
        [/[^"\\]+/, 'string'],
        [/\\./, 'string.escape'],
        [/"/, 'string', '@pop'],
      ],
    },
  })

  monaco.editor.defineTheme('htn-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
      { token: 'variable', foreground: '9CDCFE' },
      { token: 'type', foreground: 'DCDCAA' },
      { token: 'keyword', foreground: 'C586C0' },
      { token: 'predefined', foreground: '4EC9B0' },
      { token: 'operator.rule', foreground: 'FF5555', fontStyle: 'bold' },
      { token: 'operator', foreground: 'D4D4D4' },
      { token: 'number', foreground: 'B5CEA8' },
      { token: 'string', foreground: 'CE9178' },
    ],
    colors: {},
  })
}
