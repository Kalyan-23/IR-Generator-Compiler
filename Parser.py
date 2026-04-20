"""
parser.py — Recursive-Descent Parser + AST
--------------------------------------------
Grammar (precedence built-in):

  program   → statement* EOF
  statement → (ID ASSIGN)? expr SEMI?
  expr      → term   ((+ | -) term)*
  term      → unary  ((* | /) unary)*
  unary     → - unary | factor          ← KEY FIX for -c in b*-c
  factor    → ( expr ) | NUMBER | ID

The unary level sits between term and factor.
This means  b * -c  parses as  b * (-c)  correctly.
Without this level, the parser would crash or misparse.

AST node types: NumberNode, IdentNode, UnaryOpNode, BinOpNode, AssignNode
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from Lexer import Token, tokenize, LexerError


# ── AST nodes ──────────────────────────────────────────────────────────────────

@dataclass
class ASTNode:
    pass

@dataclass
class NumberNode(ASTNode):
    value: str
    def __str__(self): return self.value

@dataclass
class IdentNode(ASTNode):
    name: str
    def __str__(self): return self.name

@dataclass
class UnaryOpNode(ASTNode):
    op: str          # "-"
    operand: ASTNode
    def __str__(self): return f"(-{self.operand})"

@dataclass
class BinOpNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode
    def __str__(self): return f"({self.left} {self.op} {self.right})"

@dataclass
class AssignNode(ASTNode):
    target: str
    expr: ASTNode
    def __str__(self): return f"{self.target} = {self.expr}"


# ── Text-based tree printer ────────────────────────────────────────────────────

def ast_to_text(node: ASTNode, prefix="", is_last=True) -> str:
    """Renders the AST as a unicode box-drawing tree."""
    branch      = "└── " if is_last else "├── "
    child_pref  = prefix + ("    " if is_last else "│   ")
    lines = []

    if isinstance(node, AssignNode):
        lines.append(prefix + branch + "[=]")
        lines.append(ast_to_text(IdentNode(node.target), child_pref, False))
        lines.append(ast_to_text(node.expr, child_pref, True))

    elif isinstance(node, BinOpNode):
        lines.append(prefix + branch + f"[{node.op}]")
        lines.append(ast_to_text(node.left,  child_pref, False))
        lines.append(ast_to_text(node.right, child_pref, True))

    elif isinstance(node, UnaryOpNode):
        lines.append(prefix + branch + f"[unary {node.op}]")
        lines.append(ast_to_text(node.operand, child_pref, True))

    elif isinstance(node, NumberNode):
        lines.append(prefix + branch + f"NUM  {node.value}")

    elif isinstance(node, IdentNode):
        lines.append(prefix + branch + f"VAR  {node.name}")

    return "\n".join(lines)


def program_to_text(stmts: List[ASTNode]) -> str:
    """Full program tree as string."""
    lines = ["Program"]
    for i, s in enumerate(stmts):
        lines.append(ast_to_text(s, "", i == len(stmts) - 1))
    return "\n".join(lines)


# ── Parser ─────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, msg, token=None):
        loc = f" at line {token.line}, col {token.col}" if token else ""
        super().__init__(msg + loc)
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos    = 0

    @property
    def _cur(self) -> Token:
        return self._tokens[self._pos]

    def _eat(self, expected: str) -> Token:
        tok = self._cur
        if tok.type != expected:
            raise ParseError(
                f"Expected {expected!r} but got {tok.type!r} ({tok.value!r})", tok
            )
        self._pos += 1
        return tok

    def _match(self, *types) -> bool:
        return self._cur.type in types

    # ── grammar rules ──────────────────────────────────────────────────────────

    def parse_program(self) -> List[ASTNode]:
        stmts = []
        while not self._match("EOF"):
            stmts.append(self._stmt())
        return stmts

    def _stmt(self) -> ASTNode:
        # peek ahead to decide assignment vs bare expression
        if self._cur.type == "ID" and self._pos + 1 < len(self._tokens) \
                and self._tokens[self._pos + 1].type == "ASSIGN":
            name = self._eat("ID").value
            self._eat("ASSIGN")
            expr = self._expr()
            if self._match("SEMI"):
                self._pos += 1
            return AssignNode(target=name, expr=expr)
        else:
            expr = self._expr()
            if self._match("SEMI"):
                self._pos += 1
            return expr

    def _expr(self) -> ASTNode:
        """expr → term ((+ | -) term)*"""
        left = self._term()
        while self._match("PLUS", "MINUS"):
            op = self._cur.value
            self._pos += 1
            left = BinOpNode(op, left, self._term())
        return left

    def _term(self) -> ASTNode:
        """term → unary ((* | /) unary)*"""
        left = self._unary()
        while self._match("MUL", "DIV"):
            op = self._cur.value
            self._pos += 1
            left = BinOpNode(op, left, self._unary())
        return left

    def _unary(self) -> ASTNode:
        """
        unary → - unary | factor

        This is the fix. Without this level, b * -c crashes because
        the minus in -c gets seen by _term which doesn't expect it.
        Here we catch unary minus before reaching factor.
        Recursive so --c works too.
        """
        if self._match("MINUS"):
            self._pos += 1
            return UnaryOpNode("-", self._unary())
        return self._factor()

    def _factor(self) -> ASTNode:
        """factor → ( expr ) | NUMBER | ID"""
        tok = self._cur

        if tok.type == "LPAREN":
            self._pos += 1
            expr = self._expr()
            self._eat("RPAREN")
            return expr

        if tok.type == "NUMBER":
            self._pos += 1
            return NumberNode(tok.value)

        if tok.type == "ID":
            self._pos += 1
            return IdentNode(tok.value)

        raise ParseError(f"Unexpected token {tok.type!r} ({tok.value!r})", tok)


# ── public API ─────────────────────────────────────────────────────────────────

def parse(source: str):
    """Tokenize + parse. Returns (stmts, tokens). Raises on error."""
    tokens = tokenize(source)
    stmts  = Parser(tokens).parse_program()
    return stmts, tokens
