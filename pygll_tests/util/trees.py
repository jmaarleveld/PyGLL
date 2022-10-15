from pygll.core.nodes import (PackedNode, PackedNodeKey,
                              IntermediateNode, IntermediateNodeKey,
                              TerminalNode, TerminalNodeKey,
                              GrammarSlot)


def slot(nonterminal: str, alternate: int, position: int) -> GrammarSlot:
    return GrammarSlot(nonterminal, alternate, position, False, False)


def terminal(symbol: str, left: int, right: int) -> TerminalNode:
    return TerminalNode(left, right, symbol)



