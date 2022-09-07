##############################################################################
##############################################################################
# Imports
##############################################################################

from ..core import base as _base

try:
    import graphviz
except ImportError:
    graphviz = None

##############################################################################
##############################################################################
# Textual Printing of trees
##############################################################################


def print_tree(node: _base.IntermediateNode):
    _print_recursive(node)


def _print_recursive(node: _base.Node, *, indent=0):
    match node:
        case _base.IntermediateNode(left_extent=_,
                                    right_extent=_,
                                    slot=slot,
                                    children=children):
            _print(f'INode<{slot}>', indent=indent)
            for child in children.values():
                _print('Alternative:', indent=indent + 1)
                _print_recursive(child, indent=indent + 2)
        case _base.TerminalNode(left_extent=_,
                                right_extent=_,
                                symbol=symbol):
            _print(f'TNode<{symbol}>', indent=indent)
        case _base.PackedNode(left_extent=_,
                              right_extent=_,
                              split=_,
                              slot=slot,
                              left=left,
                              right=right):
            _print(f'PNode<{slot}>', indent=indent)
            if left is not None:
                _print('Left:', indent=indent + 1)
                _print_recursive(left, indent=indent + 2)
            _print('Right:', indent=indent + 1)
            _print_recursive(right, indent=indent + 2)
        case _:
            raise ValueError(node)


def _print(line: str, indent: int):
    print('    '*indent + line)


##############################################################################
##############################################################################
# Internal Debugging
##############################################################################


def show_tree_raw(tree: _base.Node):
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
                                    is_nonterminal_node=is_nonterminal,
                                    children=children):
            key = str(id(node))
            if is_nonterminal:
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

