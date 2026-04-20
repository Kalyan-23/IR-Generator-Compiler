"""
postfix.py — Postfix (Reverse Polish Notation) Converter
----------------------------------------------------------
Walks the AST and emits tokens in postfix order.
Postfix puts operators AFTER their operands, so:
  a + b     →  a b +
  a * (b+c) →  a b c + *

This matches how a stack-based evaluator would process it.
We also track steps for the step-by-step view.
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any
from Parser import ASTNode, AssignNode, BinOpNode, UnaryOpNode, NumberNode, IdentNode


def _walk(node: ASTNode, tokens: List[str], steps: List[Dict[str, Any]]):
    """Recursively visit the AST in post-order and collect postfix tokens."""

    if isinstance(node, NumberNode):
        tokens.append(node.value)
        steps.append({"token": node.value, "type": "operand", "note": f"Push literal {node.value}"})

    elif isinstance(node, IdentNode):
        tokens.append(node.name)
        steps.append({"token": node.name, "type": "operand", "note": f"Push variable {node.name}"})

    elif isinstance(node, UnaryOpNode):
        _walk(node.operand, tokens, steps)
        tokens.append("uminus")
        steps.append({"token": "uminus", "type": "operator", "note": "Apply unary minus"})

    elif isinstance(node, BinOpNode):
        _walk(node.left,  tokens, steps)
        _walk(node.right, tokens, steps)
        tokens.append(node.op)
        steps.append({
            "token": node.op,
            "type": "operator",
            "note": f"Apply operator '{node.op}'"
        })

    elif isinstance(node, AssignNode):
        _walk(node.expr, tokens, steps)
        tokens.append(node.target)
        tokens.append("=")
        steps.append({"token": node.target, "type": "operand",  "note": f"Target variable {node.target}"})
        steps.append({"token": "=",          "type": "operator", "note": "Assign"})



def to_postfix(stmts: List[ASTNode]) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    """
    Convert a list of statements to postfix.
    Returns (postfix_string, token_list, steps).
    """
    all_tokens: List[str]      = []
    all_steps:  List[Dict]     = []

    for stmt in stmts:
        toks: List[str]    = []
        steps: List[Dict]  = []
        _walk(stmt, toks, steps)
        all_tokens.extend(toks)
        all_steps.extend(steps)
        all_steps.append({"token": "", "type": "sep", "note": "─── next statement ───"})

    return " ".join(all_tokens), all_tokens, all_steps