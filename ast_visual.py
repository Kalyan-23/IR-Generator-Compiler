"""
ast_visual.py — Visual AST Tree Renderer
------------------------------------------
Builds a proper graphical tree from the AST using pure SVG.
No external libraries needed — just math and SVG strings.

The layout algorithm:
  1. Post-order pass to compute subtree widths
  2. Pre-order pass to assign x/y positions
  3. Render edges (lines) first, then nodes on top

Node types get different colors so you can tell them apart at a glance.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
from Parser import (
    ASTNode, AssignNode, BinOpNode, UnaryOpNode, NumberNode, IdentNode
)


# ── Layout constants ───────────────────────────────────────────────────────────
NODE_R    = 26      # circle radius
H_GAP     = 18      # minimum horizontal gap between sibling nodes
V_GAP     = 72      # vertical gap between levels
FONT_SIZE = 12      # label font size inside nodes
PAD       = 36      # canvas padding on all sides


# ── Node colors by type ────────────────────────────────────────────────────────
COLORS = {
    "assign": {"fill": "#1e3a5f", "stroke": "#5ba4f5", "text": "#93c5fd"},
    "binop":  {"fill": "#2d1b4e", "stroke": "#a78bfa", "text": "#c4b5fd"},
    "unary":  {"fill": "#3b1f3b", "stroke": "#f472b6", "text": "#f9a8d4"},
    "number": {"fill": "#1a3a2a", "stroke": "#38e8b0", "text": "#6ee7b7"},
    "ident":  {"fill": "#2a2a1a", "stroke": "#fbbf24", "text": "#fde68a"},
}


# ── Internal tree node ─────────────────────────────────────────────────────────

class LayoutNode:
    def __init__(self, label: str, kind: str, children: List["LayoutNode"] = None):
        self.label    = label
        self.kind     = kind
        self.children = children or []
        self.x        = 0.0
        self.y        = 0.0
        self.width    = 0.0   # subtree width (computed)


# ── Build layout tree from AST ─────────────────────────────────────────────────

def _build(node: ASTNode) -> LayoutNode:
    """Convert AST node into a LayoutNode tree."""

    if isinstance(node, AssignNode):
        return LayoutNode(
            label    = "=",
            kind     = "assign",
            children = [LayoutNode(label=node.target, kind="ident"), _build(node.expr)],
        )
    if isinstance(node, BinOpNode):
        return LayoutNode(
            label    = node.op,
            kind     = "binop",
            children = [_build(node.left), _build(node.right)],
        )
    if isinstance(node, UnaryOpNode):
        return LayoutNode(
            label    = f"-",
            kind     = "unary",
            children = [_build(node.operand)],
        )
    if isinstance(node, NumberNode):
        return LayoutNode(label=node.value, kind="number")
    if isinstance(node, IdentNode):
        return LayoutNode(label=node.name,  kind="ident")

    return LayoutNode(label="?", kind="ident")


# ── Layout algorithm ───────────────────────────────────────────────────────────

def _compute_width(node: LayoutNode) -> float:
    """Bottom-up: compute minimum subtree width for each node."""
    if not node.children:
        node.width = NODE_R * 2 + H_GAP
        return node.width

    total = sum(_compute_width(c) for c in node.children)
    # no extra gap needed between the siblings, it's already in their widths
    node.width = max(total, NODE_R * 2 + H_GAP)
    return node.width


def _assign_positions(node: LayoutNode, x_left: float, depth: int):
    """Top-down: assign x,y to each node given the left boundary of its subtree."""
    node.x = x_left + node.width / 2
    node.y = PAD + depth * V_GAP

    if not node.children:
        return

    cx = x_left
    for child in node.children:
        _assign_positions(child, cx, depth + 1)
        cx += child.width


# ── SVG Renderer ───────────────────────────────────────────────────────────────

def _collect(node: LayoutNode, nodes: List, edges: List, parent: Optional[LayoutNode] = None):
    """Collect all nodes and edges into flat lists for rendering."""
    if parent:
        edges.append((parent.x, parent.y, node.x, node.y))
    nodes.append(node)
    for child in node.children:
        _collect(child, nodes, edges, node)


def _max_xy(node: LayoutNode) -> Tuple[float, float]:
    """Find canvas size needed."""
    mx, my = node.x, node.y
    for c in node.children:
        cx, cy = _max_xy(c)
        mx = max(mx, cx)
        my = max(my, cy)
    return mx, my


def _wrap_label(label: str, max_chars: int = 6) -> str:
    """Shorten long labels so they fit in the circle."""
    return label if len(label) <= max_chars else label[:5] + "…"


def render_ast_svg(stmts: List[ASTNode]) -> str:
    """
    Render all statements as a single SVG tree.
    Multiple statements are laid out side by side with a gap.
    Returns an SVG string.
    """
    if not stmts:
        return '<svg width="200" height="60"><text x="10" y="30" fill="#5a6a82">No input</text></svg>'

    # build layout trees for each statement
    roots: List[LayoutNode] = [_build(s) for s in stmts]

    # compute widths
    for r in roots:
        _compute_width(r)

    # place roots side by side
    cursor = PAD
    for r in roots:
        _assign_positions(r, cursor, 0)
        cursor += r.width + PAD   # gap between trees

    # find canvas size
    total_w = cursor
    total_h = PAD
    for r in roots:
        _, my = _max_xy(r)
        total_h = max(total_h, my)
    total_h += NODE_R + PAD

    # collect all nodes and edges
    all_nodes: List[LayoutNode] = []
    all_edges: List[Tuple]      = []
    for r in roots:
        _collect(r, all_nodes, all_edges, None)

    # --- build SVG ---
    parts = [
        f'<svg width="{int(total_w)}" height="{int(total_h)}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background:#0e1117; border-radius:10px; display:block;">'
    ]

    # defs: drop shadow filter
    parts.append("""
    <defs>
      <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="3" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000" flood-opacity="0.5"/>
      </filter>
    </defs>
    """)

    # statement separator labels
    for i, r in enumerate(roots):
        label_x = r.x
        label_y = PAD - 14
        if len(roots) > 1:
            parts.append(
                f'<text x="{label_x:.1f}" y="{label_y:.1f}" '
                f'text-anchor="middle" fill="#5a6a82" '
                f'font-family="IBM Plex Mono,monospace" font-size="10">stmt {i+1}</text>'
            )

    # edges first (so nodes render on top)
    for x1, y1, x2, y2 in all_edges:
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#2a3550" stroke-width="2" stroke-linecap="round"/>'
        )

    # nodes
    for n in all_nodes:
        c      = COLORS.get(n.kind, COLORS["ident"])
        lbl    = _wrap_label(n.label)
        nx, ny = n.x, n.y

        # glow ring for operator nodes
        if n.kind in ("binop", "unary", "assign"):
            parts.append(
                f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{NODE_R + 4}" '
                f'fill="none" stroke="{c["stroke"]}" stroke-width="1" opacity="0.25"/>'
            )

        # main circle
        parts.append(
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{NODE_R}" '
            f'fill="{c["fill"]}" stroke="{c["stroke"]}" stroke-width="2" '
            f'filter="url(#shadow)"/>'
        )

        # label — handle multi-line for "= varname"
        if "\n" in lbl or (n.kind == "assign" and " " in n.label):
            parts_lbl = n.label.split(" ", 1) if n.kind == "assign" else [lbl]
            if len(parts_lbl) == 2:
                parts.append(
                    f'<text x="{nx:.1f}" y="{ny - 5:.1f}" '
                    f'text-anchor="middle" fill="{c["text"]}" '
                    f'font-family="IBM Plex Mono,monospace" font-size="{FONT_SIZE}" font-weight="bold">'
                    f'{parts_lbl[0]}</text>'
                )
                parts.append(
                    f'<text x="{nx:.1f}" y="{ny + 9:.1f}" '
                    f'text-anchor="middle" fill="{c["text"]}" '
                    f'font-family="IBM Plex Mono,monospace" font-size="{FONT_SIZE - 1}">'
                    f'{_wrap_label(parts_lbl[1], 5)}</text>'
                )
            else:
                parts.append(
                    f'<text x="{nx:.1f}" y="{ny + 4:.1f}" '
                    f'text-anchor="middle" fill="{c["text"]}" '
                    f'font-family="IBM Plex Mono,monospace" font-size="{FONT_SIZE}" font-weight="bold">'
                    f'{lbl}</text>'
                )
        else:
            parts.append(
                f'<text x="{nx:.1f}" y="{ny + 4:.1f}" '
                f'text-anchor="middle" fill="{c["text"]}" '
                f'font-family="IBM Plex Mono,monospace" font-size="{FONT_SIZE}" font-weight="bold">'
                f'{lbl}</text>'
            )

    parts.append('</svg>')
    return "\n".join(parts)


# ── Text-based tree (kept for copy-friendly output) ────────────────────────────

def render_ast_text(stmts: List[ASTNode]) -> str:
    """Plain unicode box-drawing tree — for the 'copy text' section."""
    from Parser import program_to_text
    return program_to_text(stmts)
