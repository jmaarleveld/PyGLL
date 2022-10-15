##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import abc
import collections
import logging

from . import scanner
from . import gss

from .nodes import *


class ParsingError(Exception):
    pass


##############################################################################
##############################################################################
# Parser Base Class
##############################################################################


class AbstractParser(abc.ABC):

    NULL_SLOT = GrammarSlot('$null', 0, 0, False, False)

    def __init__(self,
                 text: str,
                 *, logger: logging.Logger | None = None,
                 debug: bool = False):
        # Set up debugging functionality
        self.logger = logger
        self.debug = debug

        # Actual parsing
        self.scanner = scanner.Scanner(text)

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
        slot = self.get_initial_slot()
        self.add(slot, self.root, 0, InitialNode(0, 0))

        # Main parsing loop
        while self.todo:
            descriptor: Descriptor = self.todo.popleft()
            if self.debug:
                self.on_state_switch(descriptor)
            self.current_state = descriptor
            self.c_n = descriptor.node
            self.c_u = descriptor.stack
            self.scanner.position = descriptor.position
            self.goto(descriptor.slot)

        # Check whether we successfully parsed the input
        # Note that this lookup may look weird, but
        # intermediate node keys do not compare alternate
        # number and position when nonterminal == True.
        slot = self.get_final_slot()
        key = IntermediateNodeKey(slot, True, 0, len(text))
        self._result = self.created.get(key, None)

    _initial_grammar_slot_idx0 = None
    _initial_grammar_slot_idx1 = None

    @property
    def result(self):
        if self._result is None:
            raise ParsingError('Failed to parse')
        return self._result

    def add(self,
            g: GrammarSlot,
            stack: GSSNodeReference,
            position: int,
            s: Node):
        descriptor = Descriptor(g, stack, position, s)
        if self.debug:
            self.on_add(descriptor)
        if descriptor not in self.seen_descriptors:
            self.seen_descriptors.add(descriptor)
            self.todo.append(descriptor)

    def create(self, slot: GrammarSlot):
        if self.debug:
            self.on_create(slot)
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
        # Pop the node (self.c_u, self.scanner.position)
        if self.debug:
            self.on_pop()
        if self.c_u is not self.root:
            self.popped[self.c_u].append(self.c_n)
            to: GSSNodeReference
            label: Node
            for to, label in self.gss.get_edges(self.c_u):
                # Check for ambiguity
                for check in self.get_ambiguity_checks_for_slot(self.c_u.slot):
                    if self.debug:
                        self.log(
                            f'Running ambiguity check on: <{to.slot}, {to.position}> '
                            f'(span: {to.position}-{self.scanner.position - 1})'
                        )
                    # Check is called with the span of the parsed nonterminal
                    if not check(to.position, self.scanner.position):
                        break
                    if self.debug:
                        self.log('check success')
                else:   # Only execute if all checks succeeded
                    # Add descriptor
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
        if self.debug:
            self.on_node_t(char, node)
        return node

    def get_node_p(self,
                   slot: GrammarSlot,
                   left: Node,
                   right: Node) -> Node:
        if slot.alpha_is_special and not slot.beta_is_special:
            if self.debug:
                self.on_node_p(slot, left, right, right)
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
        if self.debug:
            self.on_inode(intermediate_node.key)
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
        if self.debug:
            self.on_node_p(slot, left, right, node)
        return node

    ###################################################################
    # Abstract methods

    @abc.abstractmethod
    def goto(self, slot: GrammarSlot):
        pass

    def unknown(self, slot: GrammarSlot):
        raise ValueError(f'No function found for grammar slot {slot}')

    @abc.abstractmethod
    def get_initial_slot(self) -> GrammarSlot:
        pass

    @abc.abstractmethod
    def get_final_slot(self) -> GrammarSlot:
        pass

    @abc.abstractmethod
    def get_ambiguity_checks_for_slot(self, slot: GrammarSlot):
        pass

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

    def on_pop(self):
        self.log(f'Popping from stack ({self.c_u})')

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

    def on_inode(self, key: IntermediateNodeKey):
        if key not in self.created:
            self.log(f'Create new INode: {key}')

    def log(self, message: str):
        if self.logger is not None:
            self.logger.debug('> ' + message)
        elif self.debug:
            print('>', message)
