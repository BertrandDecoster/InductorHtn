"""
HTN Parser for Syntax Linting
Parses HTN/Prolog files to enable syntax checking and semantic analysis.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Tuple
from enum import Enum, auto


class TokenType(Enum):
    """Token types for HTN/Prolog lexer"""
    # Literals
    ATOM = auto()           # lowercase identifier or quoted string
    VARIABLE = auto()       # ?varname (custom) or Uppercase (prolog)
    NUMBER = auto()         # integer or float
    STRING = auto()         # "quoted string"

    # Delimiters
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    COMMA = auto()          # ,
    PERIOD = auto()         # .

    # Operators
    RULE_OP = auto()        # :-
    PIPE = auto()           # |

    # Keywords (HTN-specific)
    IF = auto()             # if
    DO = auto()             # do
    DEL = auto()            # del
    ADD = auto()            # add
    ELSE = auto()           # else
    ALLOF = auto()          # allOf
    ANYOF = auto()          # anyOf
    HIDDEN = auto()         # hidden
    TRY = auto()            # try
    FIRST = auto()          # first
    GOALS = auto()          # goals

    # Special
    COMMENT = auto()        # % comment
    NEWLINE = auto()        # for tracking line numbers
    WHITESPACE = auto()     # spaces/tabs
    EOF = auto()            # end of file
    ERROR = auto()          # lexer error


@dataclass
class Token:
    """A token from the lexer"""
    type: TokenType
    value: str
    line: int
    col: int
    length: int = 0

    def __post_init__(self):
        if self.length == 0:
            self.length = len(self.value)


@dataclass
class Diagnostic:
    """A diagnostic message (error/warning)"""
    line: int
    col: int
    length: int
    severity: str  # 'error', 'warning', 'info'
    message: str
    code: str = ""  # error code like "HTN001"

    def to_dict(self):
        return {
            'line': self.line,
            'col': self.col,
            'length': self.length,
            'severity': self.severity,
            'message': self.message,
            'code': self.code
        }


@dataclass
class Term:
    """A parsed term (atom, variable, or compound)"""
    name: str
    args: List['Term'] = field(default_factory=list)
    line: int = 0
    col: int = 0
    is_variable: bool = False
    is_list: bool = False

    def __repr__(self):
        if self.is_list:
            return f"[{', '.join(str(a) for a in self.args)}]"
        if not self.args:
            return self.name
        return f"{self.name}({', '.join(str(a) for a in self.args)})"

    def get_variables(self) -> Set[str]:
        """Get all variable names in this term"""
        vars = set()
        if self.is_variable:
            vars.add(self.name)
        for arg in self.args:
            vars.update(arg.get_variables())
        return vars


@dataclass
class Rule:
    """A parsed rule (method, operator, or fact)"""
    head: Term
    body: List[Term] = field(default_factory=list)
    line: int = 0

    # HTN-specific fields
    is_method: bool = False      # has if/do
    is_operator: bool = False    # has del/add
    is_fact: bool = False        # no body
    has_else: bool = False
    has_allof: bool = False
    has_anyof: bool = False
    has_hidden: bool = False

    # Extracted clauses
    if_clause: Optional[Term] = None
    do_clause: Optional[Term] = None
    del_clause: Optional[Term] = None
    add_clause: Optional[Term] = None


class HtnLexer:
    """Tokenizer for HTN/Prolog syntax"""

    HTN_KEYWORDS = {
        'if': TokenType.IF,
        'do': TokenType.DO,
        'del': TokenType.DEL,
        'add': TokenType.ADD,
        'else': TokenType.ELSE,
        'allOf': TokenType.ALLOF,
        'anyOf': TokenType.ANYOF,
        'hidden': TokenType.HIDDEN,
        'try': TokenType.TRY,
        'first': TokenType.FIRST,
        'goals': TokenType.GOALS,
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.errors: List[Diagnostic] = []

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source"""
        while self.pos < len(self.source):
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens

    def _peek(self, offset=0) -> str:
        """Peek at character at current position + offset"""
        pos = self.pos + offset
        if pos >= len(self.source):
            return '\0'
        return self.source[pos]

    def _advance(self) -> str:
        """Advance position and return current character"""
        ch = self._peek()
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _add_token(self, token_type: TokenType, value: str, start_line: int, start_col: int):
        """Add a token to the list"""
        self.tokens.append(Token(token_type, value, start_line, start_col, len(value)))

    def _scan_token(self):
        """Scan the next token"""
        start_line = self.line
        start_col = self.col
        ch = self._advance()

        # Whitespace
        if ch in ' \t\r':
            return  # Skip whitespace

        # Newline
        if ch == '\n':
            return  # Skip newlines (already tracked in _advance)

        # Single-line comment (%)
        if ch == '%':
            comment = '%'
            while self._peek() != '\n' and self._peek() != '\0':
                comment += self._advance()
            # Comments are skipped for parsing but could be kept for preservation
            return

        # Multi-line comment (/* */)
        if ch == '/' and self._peek() == '*':
            self._advance()  # consume *
            while not (self._peek() == '*' and self._peek(1) == '/'):
                if self._peek() == '\0':
                    self.errors.append(Diagnostic(
                        start_line, start_col, 2, 'error',
                        "Unterminated multi-line comment",
                        'SYN015'
                    ))
                    return
                self._advance()
            self._advance()  # consume *
            self._advance()  # consume /
            return

        # Single character tokens
        if ch == '(':
            self._add_token(TokenType.LPAREN, '(', start_line, start_col)
            return
        if ch == ')':
            self._add_token(TokenType.RPAREN, ')', start_line, start_col)
            return
        if ch == '[':
            self._add_token(TokenType.LBRACKET, '[', start_line, start_col)
            return
        if ch == ']':
            self._add_token(TokenType.RBRACKET, ']', start_line, start_col)
            return
        if ch == ',':
            self._add_token(TokenType.COMMA, ',', start_line, start_col)
            return
        if ch == '.':
            self._add_token(TokenType.PERIOD, '.', start_line, start_col)
            return
        if ch == '|':
            self._add_token(TokenType.PIPE, '|', start_line, start_col)
            return

        # :- rule operator
        if ch == ':':
            if self._peek() == '-':
                self._advance()
                self._add_token(TokenType.RULE_OP, ':-', start_line, start_col)
                return
            # Lone colon - error
            self.errors.append(Diagnostic(
                start_line, start_col, 1, 'error',
                "Unexpected ':' - did you mean ':-'?",
                'SYN001'
            ))
            return

        # String literal
        if ch == '"':
            self._scan_string(start_line, start_col)
            return

        # Single-quoted atom
        if ch == "'":
            self._scan_quoted_atom(start_line, start_col)
            return

        # Custom variable (?varname)
        if ch == '?':
            self._scan_custom_variable(start_line, start_col)
            return

        # Number (including negative)
        if ch.isdigit() or (ch == '-' and self._peek().isdigit()):
            self._scan_number(ch, start_line, start_col)
            return

        # Identifier (atom or Prolog variable)
        if ch.isalpha() or ch == '_':
            self._scan_identifier(ch, start_line, start_col)
            return

        # Operators that could be part of atoms (like >=, =<, etc.)
        if ch in '=<>!+-*/\\':
            self._scan_operator(ch, start_line, start_col)
            return

        # Unknown character
        self.errors.append(Diagnostic(
            start_line, start_col, 1, 'error',
            f"Unexpected character: '{ch}'",
            'SYN002'
        ))

    def _scan_string(self, start_line: int, start_col: int):
        """Scan a double-quoted string"""
        value = '"'
        while self._peek() != '"' and self._peek() != '\0':
            if self._peek() == '\n':
                # Unterminated string
                self.errors.append(Diagnostic(
                    start_line, start_col, len(value), 'error',
                    "Unterminated string literal",
                    'SYN003'
                ))
                self._add_token(TokenType.ERROR, value, start_line, start_col)
                return
            if self._peek() == '\\':
                value += self._advance()  # escape char
                if self._peek() != '\0':
                    value += self._advance()  # escaped char
            else:
                value += self._advance()

        if self._peek() == '\0':
            self.errors.append(Diagnostic(
                start_line, start_col, len(value), 'error',
                "Unterminated string literal",
                'SYN003'
            ))
            self._add_token(TokenType.ERROR, value, start_line, start_col)
            return

        value += self._advance()  # closing quote
        self._add_token(TokenType.STRING, value, start_line, start_col)

    def _scan_quoted_atom(self, start_line: int, start_col: int):
        """Scan a single-quoted atom"""
        value = "'"
        while self._peek() != "'" and self._peek() != '\0':
            if self._peek() == '\n':
                self.errors.append(Diagnostic(
                    start_line, start_col, len(value), 'error',
                    "Unterminated quoted atom",
                    'SYN004'
                ))
                self._add_token(TokenType.ERROR, value, start_line, start_col)
                return
            if self._peek() == '\\':
                value += self._advance()
                if self._peek() != '\0':
                    value += self._advance()
            else:
                value += self._advance()

        if self._peek() == '\0':
            self.errors.append(Diagnostic(
                start_line, start_col, len(value), 'error',
                "Unterminated quoted atom",
                'SYN004'
            ))
            self._add_token(TokenType.ERROR, value, start_line, start_col)
            return

        value += self._advance()  # closing quote
        self._add_token(TokenType.ATOM, value, start_line, start_col)

    def _scan_custom_variable(self, start_line: int, start_col: int):
        """Scan a ?variable"""
        value = '?'

        # First char after ? must be letter or underscore
        if not (self._peek().isalpha() or self._peek() == '_'):
            self.errors.append(Diagnostic(
                start_line, start_col, 1, 'error',
                "Variable name must start with letter or underscore after '?'",
                'SYN005'
            ))
            self._add_token(TokenType.ERROR, value, start_line, start_col)
            return

        while self._peek().isalnum() or self._peek() == '_':
            value += self._advance()

        self._add_token(TokenType.VARIABLE, value, start_line, start_col)

    def _scan_number(self, first_char: str, start_line: int, start_col: int):
        """Scan a number"""
        value = first_char
        has_dot = False

        while True:
            ch = self._peek()
            if ch.isdigit():
                value += self._advance()
            elif ch == '.' and not has_dot and self._peek(1).isdigit():
                has_dot = True
                value += self._advance()  # .
            else:
                break

        self._add_token(TokenType.NUMBER, value, start_line, start_col)

    def _scan_identifier(self, first_char: str, start_line: int, start_col: int):
        """Scan an identifier (atom or Prolog variable)"""
        value = first_char

        # Allow alphanumeric, underscore, and hyphen in identifiers
        while self._peek().isalnum() or self._peek() in '_-':
            value += self._advance()

        # Check if it's an HTN keyword
        if value in self.HTN_KEYWORDS:
            self._add_token(self.HTN_KEYWORDS[value], value, start_line, start_col)
            return

        # Check if it's a Prolog-style variable (starts with uppercase or _)
        if first_char.isupper() or first_char == '_':
            self._add_token(TokenType.VARIABLE, value, start_line, start_col)
        else:
            self._add_token(TokenType.ATOM, value, start_line, start_col)

    def _scan_operator(self, first_char: str, start_line: int, start_col: int):
        """Scan an operator that could be part of an atom"""
        value = first_char

        # Multi-character operators
        op_chars = '=<>!+-*/\\'
        while self._peek() in op_chars:
            value += self._advance()

        # Common operators are treated as atoms
        self._add_token(TokenType.ATOM, value, start_line, start_col)


class HtnParser:
    """Parser for HTN/Prolog syntax"""

    def __init__(self, source: str):
        self.source = source
        self.lexer = HtnLexer(source)
        self.tokens: List[Token] = []
        self.pos = 0
        self.errors: List[Diagnostic] = []
        self.rules: List[Rule] = []

    def parse(self) -> Tuple[List[Rule], List[Diagnostic]]:
        """Parse the source and return rules and diagnostics"""
        self.tokens = self.lexer.tokenize()
        self.errors.extend(self.lexer.errors)

        while not self._is_at_end():
            try:
                rule = self._parse_rule()
                if rule:
                    self.rules.append(rule)
            except Exception as e:
                # Recover from parse error by skipping to next period
                self._sync_to_period()

        return self.rules, self.errors

    def _peek(self, offset=0) -> Token:
        """Peek at token at current position + offset"""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[pos]

    def _advance(self) -> Token:
        """Advance and return current token"""
        token = self._peek()
        if not self._is_at_end():
            self.pos += 1
        return token

    def _is_at_end(self) -> bool:
        """Check if at end of tokens"""
        return self._peek().type == TokenType.EOF

    def _check(self, *types: TokenType) -> bool:
        """Check if current token is one of the given types"""
        return self._peek().type in types

    def _match(self, *types: TokenType) -> Optional[Token]:
        """If current token matches, advance and return it"""
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, token_type: TokenType, message: str) -> Optional[Token]:
        """Expect a specific token type, report error if not found"""
        if self._check(token_type):
            return self._advance()

        token = self._peek()
        self.errors.append(Diagnostic(
            token.line, token.col, token.length, 'error',
            message,
            'SYN010'
        ))
        return None

    def _sync_to_period(self):
        """Synchronize to the next period for error recovery"""
        while not self._is_at_end():
            if self._peek().type == TokenType.PERIOD:
                self._advance()
                return
            self._advance()

    def _parse_rule(self) -> Optional[Rule]:
        """Parse a single rule (fact, method, or operator)"""
        # Skip any leading issues
        if self._is_at_end():
            return None

        start_line = self._peek().line

        # Check for unexpected tokens
        if self._check(TokenType.PERIOD):
            self._advance()
            return None

        # Parse head
        head = self._parse_term()
        if not head:
            self._sync_to_period()
            return None

        # Check for fact (just head followed by period)
        if self._match(TokenType.PERIOD):
            return Rule(head=head, line=start_line, is_fact=True)

        # Expect :-
        if not self._expect(TokenType.RULE_OP, f"Expected ':-' or '.' after '{head.name}'"):
            self._sync_to_period()
            return None

        # Parse body
        rule = Rule(head=head, line=start_line)
        self._parse_body(rule)

        # Expect period
        if not self._expect(TokenType.PERIOD, "Expected '.' at end of rule"):
            self._sync_to_period()

        return rule

    def _parse_body(self, rule: Rule):
        """Parse the body of a rule and classify it"""
        while not self._check(TokenType.PERIOD, TokenType.EOF):
            token = self._peek()

            # Check for HTN keywords
            if token.type == TokenType.ELSE:
                self._advance()
                rule.has_else = True
                self._match(TokenType.COMMA)
                continue

            if token.type == TokenType.ALLOF:
                self._advance()
                rule.has_allof = True
                self._match(TokenType.COMMA)
                continue

            if token.type == TokenType.ANYOF:
                self._advance()
                rule.has_anyof = True
                self._match(TokenType.COMMA)
                continue

            if token.type == TokenType.HIDDEN:
                self._advance()
                rule.has_hidden = True
                self._match(TokenType.COMMA)
                continue

            # Parse term
            term = self._parse_term()
            if not term:
                break

            rule.body.append(term)

            # Classify based on term
            if term.name == 'if':
                rule.is_method = True
                rule.if_clause = term
            elif term.name == 'do':
                rule.is_method = True
                rule.do_clause = term
            elif term.name == 'del':
                rule.is_operator = True
                rule.del_clause = term
            elif term.name == 'add':
                rule.is_operator = True
                rule.add_clause = term

            # Skip comma between terms
            self._match(TokenType.COMMA)

    def _parse_term(self) -> Optional[Term]:
        """Parse a term (atom, variable, number, or compound)"""
        token = self._peek()

        # Variable
        if token.type == TokenType.VARIABLE:
            self._advance()
            return Term(name=token.value, line=token.line, col=token.col, is_variable=True)

        # Number
        if token.type == TokenType.NUMBER:
            self._advance()
            return Term(name=token.value, line=token.line, col=token.col)

        # String
        if token.type == TokenType.STRING:
            self._advance()
            return Term(name=token.value, line=token.line, col=token.col)

        # List
        if token.type == TokenType.LBRACKET:
            return self._parse_list()

        # Atom or compound term (or HTN keyword used as functor)
        if token.type in (TokenType.ATOM, TokenType.IF, TokenType.DO,
                          TokenType.DEL, TokenType.ADD, TokenType.TRY,
                          TokenType.FIRST, TokenType.GOALS):
            self._advance()
            name = token.value

            # Check for arguments
            if self._check(TokenType.LPAREN):
                args = self._parse_args()
                return Term(name=name, args=args, line=token.line, col=token.col)

            return Term(name=name, line=token.line, col=token.col)

        # Check for mismatched bracket
        if token.type == TokenType.LBRACKET:
            self.errors.append(Diagnostic(
                token.line, token.col, 1, 'error',
                "Unexpected '[' - use '(' for function arguments",
                'SYN011'
            ))
            self._advance()
            return None

        # Extra closing paren
        if token.type == TokenType.RPAREN:
            self.errors.append(Diagnostic(
                token.line, token.col, 1, 'error',
                "Unbalanced parentheses - extra ')'",
                'SYN013'
            ))
            self._advance()
            return None

        # Unexpected token
        if not self._check(TokenType.PERIOD, TokenType.EOF, TokenType.COMMA):
            self.errors.append(Diagnostic(
                token.line, token.col, token.length, 'error',
                f"Unexpected token: {token.value}",
                'SYN012'
            ))
            self._advance()

        return None

    def _parse_args(self) -> List[Term]:
        """Parse comma-separated arguments in parentheses"""
        args = []

        if not self._match(TokenType.LPAREN):
            return args

        paren_depth = 1
        start_token = self.tokens[self.pos - 1]

        # Handle empty parens
        if self._check(TokenType.RPAREN):
            self._advance()
            return args

        while not self._is_at_end():
            term = self._parse_term()
            if term:
                args.append(term)

            if self._check(TokenType.RPAREN):
                self._advance()
                return args

            if not self._match(TokenType.COMMA):
                # Check for missing closing paren
                if self._check(TokenType.PERIOD, TokenType.EOF):
                    self.errors.append(Diagnostic(
                        start_token.line, start_token.col, 1, 'error',
                        "Unbalanced parentheses - missing ')'",
                        'SYN013'
                    ))
                    return args
                # Unexpected token
                break

        return args

    def _parse_list(self) -> Term:
        """Parse a list [a, b, c] or [H|T]"""
        start = self._advance()  # consume [
        elements = []

        if self._check(TokenType.RBRACKET):
            self._advance()
            return Term(name='[]', line=start.line, col=start.col, is_list=True)

        while not self._is_at_end():
            term = self._parse_term()
            if term:
                elements.append(term)

            if self._check(TokenType.RBRACKET):
                self._advance()
                return Term(name='.', args=elements, line=start.line, col=start.col, is_list=True)

            if self._match(TokenType.PIPE):
                # [H|T] syntax
                tail = self._parse_term()
                if tail:
                    elements.append(tail)
                if not self._match(TokenType.RBRACKET):
                    self.errors.append(Diagnostic(
                        start.line, start.col, 1, 'error',
                        "Unbalanced brackets - missing ']'",
                        'SYN014'
                    ))
                return Term(name='.', args=elements, line=start.line, col=start.col, is_list=True)

            if not self._match(TokenType.COMMA):
                break

        self.errors.append(Diagnostic(
            start.line, start.col, 1, 'error',
            "Unbalanced brackets - missing ']'",
            'SYN014'
        ))
        return Term(name='.', args=elements, line=start.line, col=start.col, is_list=True)


def parse_htn(source: str) -> Tuple[List[Rule], List[Diagnostic]]:
    """Convenience function to parse HTN source"""
    parser = HtnParser(source)
    return parser.parse()
