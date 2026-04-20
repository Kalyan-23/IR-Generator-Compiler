"""
codegen.py — Three-Address Code (TAC) Generator
-------------------------------------------------
Produces three representations of TAC:

  1. Quadruples  — (op, arg1, arg2, result)
  2. Triples     — index: (op, arg1, arg2)   result is implicit (the index)
  3. Indirect Triples — a separate pointer table that references triple indices

Also does basic CSE: if the same sub-expression was already computed,
we reuse the existing temp instead of emitting a duplicate instruction.

All three forms are generated from the same internal list of TAC records.
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional
from Parser import ASTNode, AssignNode, BinOpNode, UnaryOpNode, NumberNode, IdentNode


# ── Internal TAC record ────────────────────────────────────────────────────────

class TACRecord:
    def __init__(self, op: str, arg1: str, arg2: str = "", result: str = ""):
        self.op     = op      # "+", "-", "*", "/", "=", "uminus"
        self.arg1   = arg1
        self.arg2   = arg2
        self.result = result  # temp or variable name

    def __repr__(self):
        return f"TACRecord({self.op!r}, {self.arg1!r}, {self.arg2!r}, {self.result!r})"


# ── TAC Generator ─────────────────────────────────────────────────────────────

class TACGen:
    def __init__(self):
        self._counter = 0
        self.records: List[TACRecord] = []
        self.steps:   List[Dict]      = []
        self._cse:    Dict[str, str]  = {}   # expr_key → temp_name

    def _tmp(self) -> str:
        self._counter += 1
        return f"t{self._counter}"

    def _emit(self, rec: TACRecord, note: str = "", cse: bool = False):
        self.records.append(rec)
        self.steps.append({
            "op":     rec.op,
            "arg1":   rec.arg1,
            "arg2":   rec.arg2,
            "result": rec.result,
            "note":   note,
            "cse":    cse,
        })

    def _key(self, op: str, a: str, b: str = "") -> str:
        # sort commutative ops so a+b and b+a share the same key
        if op in ("+", "*") and a > b:
            a, b = b, a
        return f"{op}|{a}|{b}"

    def _visit(self, node: ASTNode) -> str:
        """Walk AST, emit TAC records, return name of result operand."""

        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, IdentNode):
            return node.name

        if isinstance(node, UnaryOpNode):
            operand = self._visit(node.operand)
            k = self._key("uminus", operand)
            if k in self._cse:
                self._note_cse(self._cse[k], f"uminus {operand}")
                return self._cse[k]
            t = self._tmp()
            self._cse[k] = t
            self._emit(TACRecord("uminus", operand, "", t),
                       f"Negate {operand} → {t}")
            return t

        if isinstance(node, BinOpNode):
            left  = self._visit(node.left)
            right = self._visit(node.right)
            k = self._key(node.op, left, right)
            if k in self._cse:
                self._note_cse(self._cse[k], f"{left} {node.op} {right}")
                return self._cse[k]
            t = self._tmp()
            self._cse[k] = t
            self._emit(TACRecord(node.op, left, right, t),
                       f"Compute {left} {node.op} {right} → {t}")
            return t

        if isinstance(node, AssignNode):
            rhs = self._visit(node.expr)
            if rhs != node.target:
                self._emit(TACRecord("=", rhs, "", node.target),
                           f"Assign {rhs} → {node.target}")
            return node.target

        raise RuntimeError(f"Unknown AST node: {type(node)}")

    def _note_cse(self, reused: str, expr: str):
        """Log a CSE reuse (no actual instruction emitted)."""
        self.steps.append({
            "op": "CSE", "arg1": expr, "arg2": "", "result": reused,
            "note": f"CSE: reuse {reused} (already computed)",
            "cse": True,
        })

    def generate(self, stmts: List[ASTNode]):
        """Generate TAC for all statements. Returns self for chaining."""
        self._counter = 0
        self.records  = []
        self.steps    = []
        self._cse     = {}
        for stmt in stmts:
            self._visit(stmt)
            self.steps.append({"op":"SEP","arg1":"","arg2":"","result":"",
                                "note":"─── next statement ───","cse":False})
        return self


# ── Format as Quadruples ───────────────────────────────────────────────────────

def as_quadruples(records: List[TACRecord]) -> List[Tuple]:
    """
    Quadruple form: (op, arg1, arg2, result)
    Each instruction is a 4-tuple. Empty fields stay as '-'.
    """
    out = []
    for r in records:
        op     = r.op
        arg1   = r.arg1   or "-"
        arg2   = r.arg2   or "-"
        result = r.result or "-"
        out.append((op, arg1, arg2, result))
    return out


# ── Format as Triples ──────────────────────────────────────────────────────────

def as_triples(records: List[TACRecord]) -> List[Tuple]:
    """
    Triple form: (index, op, arg1, arg2)
    The result is NOT stored explicitly — it's identified by the index.
    So instead of a result field, references to earlier results use (i).
    """
    # first pass: assign index to each record
    idx_map: Dict[str, str] = {}   # result_name → "(index)"
    out = []

    for i, r in enumerate(records):
        # replace arg references with (index) if they were previously computed
        a1 = idx_map.get(r.arg1, r.arg1) if r.arg1 else "-"
        a2 = idx_map.get(r.arg2, r.arg2) if r.arg2 else "-"

        out.append((i, r.op, a1, a2))

        # map result to this index for future references
        if r.result and r.result.startswith("t"):
            idx_map[r.result] = f"({i})"
        elif r.result:
            idx_map[r.result] = f"({i})"

    return out


# ── Format as Indirect Triples ─────────────────────────────────────────────────

def as_indirect_triples(records: List[TACRecord]) -> Tuple[List[Tuple], List[Tuple]]:
    """
    Indirect triples = triples table + a pointer/index table.
    The pointer table maps execution order → triple index.
    This makes it easy to reorder or delete instructions (just update pointers).

    Returns (triples_table, pointer_table).
    triples_table : [(index, op, arg1, arg2), ...]
    pointer_table : [(ptr_index, triple_index), ...]
    """
    triples = as_triples(records)

    # pointer table just maps execution order → triple index
    # (in this simple version they match, but in optimized code they can differ)
    pointer_table = [(i, t[0]) for i, t in enumerate(triples)]

    return triples, pointer_table


# ── Convenience wrapper ────────────────────────────────────────────────────────

def generate_tac(stmts: List[ASTNode]) -> TACGen:
    """Generate TAC and return the TACGen object (has .records and .steps)."""
    gen = TACGen()
    gen.generate(stmts)
    return gen