"""
lexer.py — Tokenizer
---------------------
Breaks source text into a flat list of tokens.
Pretty standard stuff — just regex matching in priority order.
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    type:  str
    value: str
    line:  int
    col:   int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


# Token patterns — order matters, longer/specific first
_SPEC = [
    ("NUMBER",   r"\d+(\.\d+)?"),
    ("ID",       r"[A-Za-z_]\w*"),
    ("ASSIGN",   r"="),
    ("PLUS",     r"\+"),
    ("MINUS",    r"-"),
    ("MUL",      r"\*"),
    ("DIV",      r"/"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("SEMI",     r";"),
    ("NEWLINE",  r"\n"),
    ("SKIP",     r"[ \t]+"),
    ("MISMATCH", r"."),
]

_RE = re.compile("|".join(f"(?P<{n}>{p})" for n, p in _SPEC))


class LexerError(Exception):
    def __init__(self, char, line, col):
        super().__init__(f"Unexpected character {char!r} at line {line}, col {col}")
        self.line = line
        self.col  = col


def tokenize(source: str) -> List[Token]:
    """Turn source string into a list of Token objects."""
    tokens = []
    line = 1
    line_start = 0

    for mo in _RE.finditer(source):
        kind  = mo.lastgroup
        value = mo.group()
        col   = mo.start() - line_start + 1

        if kind == "NEWLINE":
            line += 1
            line_start = mo.end()
        elif kind == "SKIP":
            pass
        elif kind == "MISMATCH":
            raise LexerError(value, line, col)
        else:
            tokens.append(Token(kind, value, line, col))

    tokens.append(Token("EOF", "", line, 0))
    return tokens