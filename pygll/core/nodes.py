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
    children: dict[PackedNodeKey, PackedNode] = dataclasses.field(compare=False,
                                                                  default_factory=dict)

    @property
    def key(self) -> IntermediateNodeKey:
        return IntermediateNodeKey(self.slot,
                                   self.left_extent,
                                   self.right_extent)


@dataclasses.dataclass(frozen=True, slots=True)
class IntermediateNodeKey:
    slot: GrammarSlot
    left_extent: int
    right_extent: int

    def __str__(self):
        return f'INodeKey[{self.slot} | {self.left_extent}-{self.right_extent}]'


##############################################################################
##############################################################################
# Grammar Slots, GSS, and Descriptors
##############################################################################


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
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

    @classmethod
    def full_nonterminal(cls, nonterminal: str, alpha: bool, beta: bool):
        return cls(
            nonterminal=nonterminal,
            alternate=-1,
            position=-1,
            alpha_is_special=alpha,
            beta_is_special=beta
        )

    def __eq__(self, other):
        if not isinstance(other, GrammarSlot):
            return False
        if (self.alternate < 0) != (other.alternate < 0):
            return False
        if self.alternate < 0:
            return self.nonterminal == other.nonterminal
        return (
            self.nonterminal == other.nonterminal and
            self.alternate == other.alternate and
            self.position == other.position
        )

    def __hash__(self):
        if self.alternate < 0:
            return hash(self.nonterminal)
        return hash((self.nonterminal, self.alternate, self.position))

    def __str__(self):
        if self.alternate < 0:
            return self.nonterminal
        return f'{self.nonterminal}.{self.alternate}@{self.position}'


@dataclasses.dataclass(frozen=True, slots=True)
class GSSNodeReference:
    slot: GrammarSlot
    position: int

    def __str__(self):
        return f'node<{self.slot!s}, {self.position}>'


@dataclasses.dataclass(frozen=True, slots=True)
class Descriptor:
    slot: GrammarSlot | None    # None for initial slot
    stack: GSSNodeReference
    position: int
    node: Node

    def __str__(self):
        return (
            f'state[{self.slot!s} | {self.stack!s} | {self.position} | <node ...>]'
        )
