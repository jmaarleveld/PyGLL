##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import dataclasses

##############################################################################
##############################################################################
# Parse Node Classes
##############################################################################


@dataclasses.dataclass(frozen=True, slots=True)
class Node:
    left_extent: int
    right_extent: int


@dataclasses.dataclass(frozen=True, slots=True)
class PackedNode(Node):
    slot: GrammarSlot
    split: int
    left: Node | None
    right: Node

    @property
    def key(self) -> PackedNodeKey:
        return PackedNodeKey(self.slot, self.split)


@dataclasses.dataclass(frozen=True, slots=True)
class PackedNodeKey:
    slot: GrammarSlot
    split: int


@dataclasses.dataclass(frozen=True, slots=True)
class TerminalNode(Node):
    symbol: str

    @property
    def key(self) -> TerminalNodeKey:
        return TerminalNodeKey(self.left_extent,
                               self.right_extent,
                               self.symbol)


@dataclasses.dataclass(frozen=True, slots=True)
class TerminalNodeKey(Node):
    left_extent: int
    right_extent: int
    symbol: str


@dataclasses.dataclass(frozen=True, slots=True)
class InitialNode(Node):
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class IntermediateNode(Node):
    slot: GrammarSlot
    is_nonterminal_node: bool = False
    children: dict[PackedNodeKey, PackedNode] = dataclasses.field(compare=False,
                                                                  default_factory=dict)

    @property
    def key(self) -> IntermediateNodeKey:
        return IntermediateNodeKey(self.slot,
                                   self.is_nonterminal_node,
                                   self.left_extent,
                                   self.right_extent)


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class IntermediateNodeKey:
    slot: GrammarSlot
    is_nonterminal_node: bool
    left_extent: int
    right_extent: int

    def __str__(self):
        position = self.slot.nonterminal if self.is_nonterminal_node else str(self.slot)
        return f'INodeKey[{position} | {self.left_extent}-{self.right_extent}]'

    def __eq__(self, other):
        if not isinstance(other, IntermediateNodeKey):
            return False
        if self.is_nonterminal_node != other.is_nonterminal_node:
            return False
        if self.is_nonterminal_node:
            return (
                    self.slot.nonterminal == other.slot.nonterminal and
                    self.left_extent == other.left_extent and
                    self.right_extent == other.right_extent
            )
        return (
            self.slot == other.slot and
            self.left_extent == other.left_extent and
            self.right_extent == other.right_extent
        )

    def __hash__(self):
        if self.is_nonterminal_node:
            key = (self.slot.nonterminal, self.left_extent, self.right_extent)
        else:
            key = (self.slot, self.left_extent, self.right_extent)
        return hash(key)


##############################################################################
##############################################################################
# Grammar Slots, GSS, and Descriptors
##############################################################################


@dataclasses.dataclass(frozen=True, slots=True)
class GrammarSlot:
    """A grammar slot represents a rule of the form
    A := alpha . beta

    The grammar slot stores the nonterminal, the
    index of the alternate in the grammar,
    and the position of the dot.

    alpha_is_special and beta_is_special are special
    pre-computed attribute used to speed up the get_node_p
    function.

    alpha_is_special is defined as the truth value
    of the following expression:
    len(alpha) == 1 and (alpha[0] is a terminal or non-nullable).

    beta_is_special is defined as the truth
    value of the following expression:
    len(beta) == 0
    """
    nonterminal: str
    alternate: int
    position: int
    alpha_is_special: bool
    beta_is_special: bool

    def __str__(self):
        return f'{self.nonterminal}.{self.alternate}@{self.position}'


@dataclasses.dataclass(frozen=True, slots=True)
class GSSNodeReference:
    slot: GrammarSlot
    position: int

    def __str__(self):
        return f'node<{self.slot!s}, {self.position}>'


@dataclasses.dataclass(frozen=True, slots=True)
class Descriptor:
    slot: GrammarSlot
    stack: GSSNodeReference
    position: int
    node: Node

    def __str__(self):
        return (
            f'state[{self.slot!s} | {self.stack!s} | {self.position} | {self.node}]'
        )
