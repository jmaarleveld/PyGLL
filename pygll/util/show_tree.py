##############################################################################
##############################################################################
# Imports
##############################################################################

from ..core import base as _base

try:
    import graphviz
except ImportError:
    raise RuntimeError('Tree visualization requires graphviz')


##############################################################################
##############################################################################
# Internal Debugging
##############################################################################


def show_tree(tree: _base.Node):
    dot = graphviz.Digraph()
    _show_recursive_raw(tree, dot, None, set(), set())
    dot.render('graph.gv', view=True)


def _show_recursive_raw(node: _base.Node,
                        dot: graphviz.Digraph,
                        parent: str | None,
                        edges: set[tuple[str, str]],
                        seen: set[int],
                        edge_label=''):
    if id(node) in seen:
        key = str(id(node))
        if parent is not None and (parent, key) not in edges:
            dot.edge(parent, key, label=edge_label)
            edges.add((parent, key))
        return
    seen.add(id(node))
    match node:
        case _base.IntermediateNode(left_extent=left,
                                    right_extent=right,
                                    slot=slot,
                                    children=children):
            key = str(id(node))
            if slot.alternate < 0:
                label = f'NNode<{slot.nonterminal}, {left}, {right}>'
            else:
                label = f'INode<{slot}, {left}, {right}>'
            dot.attr('node', shape='rectangle')
            dot.node(key, label)
            if parent is not None and (parent, key) not in edges:
                edges.add((parent, key))
                dot.edge(parent, key, label=edge_label)
            for child in children.values():
                _show_recursive_raw(child, dot, key, edges, seen)
        case _base.TerminalNode(left_extent=left,
                                right_extent=right,
                                symbol=symbol):
            key = str(id(node))
            label = f'TNode<{symbol}, {left}, {right}>'
            dot.attr('node', shape='oval')
            dot.node(key, label)
            if (parent, key) not in edges:
                edges.add((parent, key))
                dot.edge(parent, key, label=edge_label)
        case _base.PackedNode(left_extent=_,
                              right_extent=_,
                              split=split,
                              slot=slot,
                              left=left,
                              right=right):
            key = str(id(node))
            label = f'PNode<{slot}, {split}>'
            dot.attr('node', shape='oval')
            dot.node(key, label)
            if (parent, key) not in edges:
                edges.add((parent, key))
                dot.edge(parent, key, label=edge_label)
            if left is not None:
                _show_recursive_raw(left, dot, key, edges, seen, edge_label='left')
            _show_recursive_raw(right, dot, key, edges, seen, edge_label='right')
        case _:
            raise ValueError(node)

