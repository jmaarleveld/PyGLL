##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import abc
import collections
import dataclasses
import logging
import textwrap

try:
    import graphviz
except ImportError:
    graphviz = None

from . import scanner
from . import gss

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
    #nonterminal: str
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
    #nonterminal: str
    slot: GrammarSlot
    is_nonterminal_node: bool
    left_extent: int
    right_extent: int

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


##############################################################################
##############################################################################
# Parser Base Class
##############################################################################


class AbstractParser(abc.ABC):

    NULL_SLOT = GrammarSlot('$null', 0, 0, False, False)

    def __init__(self, text: str, logger: logging.Logger | None = None):
        # Set up debugging functionality
        self.logger = logger
        if graphviz is not None:
            self.dot = graphviz.Digraph()
        else:
            self.dot = None

        # Actual parsing
        self.scanner = scanner.Scanner(text)
        #self.scanner.register_callback(scanner.ScannerEvent.GetNext,
        #                               self.on_advance_scanner)

        # R -- the set of descriptors which still have to be processed.
        # Descriptors describe the current parser state,
        # and can be used to re-instate the parser to
        # a different state.
        self.todo: collections.deque[Descriptor] = collections.deque()
        # U -- The collection of all previously encountered descriptors.
        # Descriptors which have previously been processed can be skipped
        # layer, so we use this to keep track.
        self.seen_descriptors: set[Descriptor] = set()
        # P -- Collection of previously popped nodes.
        # Every entry (GSSNodeReference, Node) effectively
        # defines a GSS node.
        defaultdict = collections.defaultdict
        self.popped: defaultdict[GSSNodeReference, list[Node]] = defaultdict(list)
        # S -- collection of nodes used to check parsing success
        self.created: dict[IntermediateNodeKey, IntermediateNode] = {}
        self.terminal_nodes: dict[TerminalNodeKey, TerminalNode] = {}
        #
        self.gss: gss.GSS[GSSNodeReference, Node] = gss.GSS()

        # Defaults
        self.root: GSSNodeReference = GSSNodeReference(self.NULL_SLOT, 0)
        self.c_u: GSSNodeReference = self.root
        self.c_n: Node = InitialNode(0, 0)
        self.c_r: Node | None = None

        # Add initial descriptor
        slot = self.get_initial_grammar_slot()
        self.add(slot, self.root, 0, InitialNode(0, 0))

        # Main parsing loop
        while self.todo:
            descriptor: Descriptor = self.todo.popleft()
            #self.on_state_switch(descriptor)
            self.current_state = descriptor
            self.c_n = descriptor.node
            self.c_u = descriptor.stack
            self.scanner.position = descriptor.position
            self.goto(descriptor.slot)

        # Check whether we successfully parsed the input
        key = IntermediateNodeKey(self.get_final_slots()[0], True, 0, len(text))
        self._result = self.created.get(key, None)

    @property
    def result(self):
        if self._result is None:
            raise ValueError('Failed to parse')
        return self._result

    def add(self,
            g: GrammarSlot,
            stack: GSSNodeReference,
            position: int,
            s: Node):
        descriptor = Descriptor(g, stack, position, s)
        #self.on_add(descriptor)
        if descriptor not in self.seen_descriptors:
            self.seen_descriptors.add(descriptor)
            self.todo.append(descriptor)

    def create(self, slot: GrammarSlot):
        #self.on_create(slot)
        ref = GSSNodeReference(slot, self.scanner.position)
        if ref not in self.gss:
            self.gss.add_node(ref)
        if self.c_u not in self.gss.get_children(ref):
            self.gss.add_edge(from_=ref, to=self.c_u, label=self.c_n)
            for z in self.popped[ref]:
                node = self.get_node_p(slot, self.c_n, z)
                self.add(slot, self.c_u, z.right_extent, node)
        return ref

    def pop(self):
        #self.on_pop()
        if self.c_u is not self.root:
            self.popped[self.c_u].append(self.c_n)
            to: GSSNodeReference
            label: Node
            for to, label in self.gss.get_edges(self.c_u):
                node = self.get_node_p(self.c_u.slot, label, self.c_n)
                self.add(self.c_u.slot, to, self.scanner.position, node)

    def get_node_t(self, char: str) -> TerminalNode:
        node = TerminalNode(
            left_extent=self.scanner.position,
            right_extent=self.scanner.position + len(char),
            symbol=char
        )
        # Try to use a cached version of the node
        node = self.terminal_nodes.setdefault(node.key, node)
        #self.on_node_t(char, node)
        return node

    def get_node_p(self,
                   slot: GrammarSlot,
                   left: Node,
                   right: Node) -> Node:
        if slot.alpha_is_special and not slot.beta_is_special:
            #self.on_node_p(slot, left, right, right)
            return right
        left_extent = (left.left_extent
                       if not isinstance(left, InitialNode)
                       else right.left_extent)
        intermediate_node = IntermediateNode(
            left_extent=left_extent,
            right_extent=right.right_extent,
            is_nonterminal_node=slot.beta_is_special,
            slot=slot
        )
        node = self.created.setdefault(intermediate_node.key,
                                       intermediate_node)
        split = (left.right_extent
                 if not isinstance(left, InitialNode)
                 else right.left_extent)
        key = PackedNodeKey(slot, split)
        if key not in node.children:
            packed_node = PackedNode(
                left_extent=left_extent,
                right_extent=right.right_extent,
                slot=slot,
                left=left if not isinstance(left, InitialNode) else None,
                right=right,
                split=split
            )
            node.children[key] = packed_node
        #self.on_node_p(slot, left, right, node)
        return node

    @abc.abstractmethod
    def goto(self, slot: GrammarSlot):
        pass

    @abc.abstractmethod
    def get_initial_grammar_slot(self) -> GrammarSlot:
        pass

    @abc.abstractmethod
    def get_start_nonterminal(self) -> str:
        pass

    @abc.abstractmethod
    def get_final_slots(self) -> tuple[GrammarSlot]:
        pass

    def unknown(self, slot: GrammarSlot):
        raise ValueError(f'No function found for grammar slot {slot}')

    ###################################################################
    # Debugging Functionality

    def on_state_switch(self, new_state: Descriptor):
        self.log('=' * 72)
        self.log(f'Switching to new parser state: {new_state}')

    def on_goto(self, slot: GrammarSlot, function_name: str):
        self.log(f'Jump to function {function_name} (slot = {slot})')

    def on_node_t(self, char: str, node: TerminalNode):
        self.log(f'Created terminal node (char = {char})')

    def on_node_p(self,
                  slot: GrammarSlot,
                  left: Node,
                  right: Node,
                  created: Node):
        self.log(f'Created packed node for slot {slot}')

    def on_add(self, descriptor: Descriptor):
        self.log(f'Attempting to insert new descriptor: {descriptor}')
        if descriptor in self.seen_descriptors:
            self.log('Skipping descriptor insertion (already seen)')
        if self.dot is not None:
            self.dot.node(str(descriptor), f'{descriptor.slot} | {descriptor.position}')
            if descriptor.slot != self.get_initial_grammar_slot():
                self.dot.edge(str(self.current_state), str(descriptor))

    def on_pop(self):
        self.log('Popping from stack...')

    def on_create(self, slot: GrammarSlot):
        self.log(f'Creating GSS node for grammar slot: {slot}')

    def on_call(self, name: str):
        self.log(f'Entering function {name}')

    def on_advance_scanner(self, pattern: str, success: bool):
        self.log(
            f'Advancing scanner position with pattern {pattern} (success: {success})'
        )
        if not success:
            self.log(
                f'Current scanner lookahead: {self.scanner.peek((len(pattern)))}'
            )

    def log(self, message: str):
        if self.logger is not None:
            self.logger.debug('> ' + message)

    def draw_graph(self):
        if self.dot is None:
            raise ValueError('Install graphviz to visualize graph')
        self.dot.render('graph.gv', view=True)

