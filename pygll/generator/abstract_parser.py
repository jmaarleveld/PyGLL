##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import abc
import dataclasses
import enum
import typing

from . import context_free_grammar as _cfg

##############################################################################
##############################################################################
# Main Abstract Parser Definition
##############################################################################


@dataclasses.dataclass
class ParserDefinition:
    """Abstract parser definition.

    This class is used to represent the abstract definition of
    a parser.

    The `metadata` field is used to store metadata information about
    the parser. This information is not used during parser runtime.

    The `grammar_slots` field is a mapping of strings to grammar
    slot definitions. Grammar slots are used by the GLL algorithm
    to track how far along the parsing process the algorithm is.
    The dictionary maps the name of the grammar slot to the actual
    definition. The name can be used by other abstract nodes to
    refer to the grammar slot -- and retrieve it if necessary.
    if `self.grammar_slots[key] == slot`, then `slot.name == key`.

    The `literal_checks` is a dictionary mapping the names of functions
    for testing the input for literals to the abstract definitions
    of those functions.
    The `range_checks` field is a similar dictionary, but the
    nodes are for abstract definitions defining range checks.
    Range checks are functions for checking whether the next
    character in the input is contained within a given range.
    A check function can be retrieved using the `get_check_by_name`
    method, which looks in both the `literal_checks` and the
    `range_checks` dictionary.

    `parse_functions` is a dictionary containing the information
    for all the actual parsing functions.
    """

    ###################################################################
    # Field Definitions

    # Parser Metadata
    metadata: ParserMetadata

    # Grammar Slots
    _initial_grammar_slot: dict[str, str | None] = dataclasses.field(
        init=False, default_factory=lambda: {'start': None, 'end': None}
    )
    grammar_slots: dict[str, GrammarSlotDefinition] = dataclasses.field(
        init=False, default_factory=dict
    )

    # Input Check Functions
    input_checks: dict[str, InputCheckDefinition] = dataclasses.field(
        init=False, default_factory=dict
    )

    # Parsing Functions
    parse_functions: dict[str, FunctionDefinition] = dataclasses.field(
        init=False, default_factory=dict
    )

    # Disambiguation Checks
    ambiguity_checks: dict[str, AmbiguityCheckDefinition] = dataclasses.field(
        init=False, default_factory=dict
    )

    # Goto Definition
    goto: dict[str, str] = dataclasses.field(
        init=False, default_factory=dict
    )

    ###################################################################
    # get_and_declare functions

    @property
    def initial_grammar_slot_start(self) -> str | None:
        return self._initial_grammar_slot['start']

    @initial_grammar_slot_start.setter
    def initial_grammar_slot_start(self, slot: str):
        self._initial_grammar_slot['start'] = slot

    @property
    def initial_grammar_slot_end(self) -> str | None:
        return self._initial_grammar_slot['end']

    @initial_grammar_slot_end.setter
    def initial_grammar_slot_end(self, slot: str):
        self._initial_grammar_slot['end'] = slot

    def get_and_declare_grammar_slot(self,
                                     nonterminal: str,
                                     alternate: int,
                                     position: int,
                                     grammar: _cfg.ContextFreeGrammar,
                                     *, is_initial=False):
        name = GrammarSlotDefinition.get_slot_name(nonterminal,
                                                   alternate,
                                                   position,
                                                   is_initial=is_initial)
        if name not in self.grammar_slots:
            definition = GrammarSlotDefinition.from_key_and_grammar(
                nonterminal,
                alternate,
                position,
                grammar,
                is_initial=is_initial
            )
            self.add_grammar_slot(definition)
        return name

    def get_and_declare_grammar_slot_nonterminal(self,
                                                 nonterminal: str,
                                                 grammar: _cfg.ContextFreeGrammar,
                                                 *, is_initial=False):
        return self.get_and_declare_grammar_slot(
            nonterminal, -1, -1, grammar, is_initial=is_initial
        )

    def get_and_declare_literal_check(self, literal: str) -> str:
        definition = LiteralCheckDefinition(literal)
        if definition.name not in self.input_checks:
            self.add_input_check(definition)
        return definition.name

    def get_and_declare_range_check(self,
                                    ranges: tuple[tuple[int, int], ...]) -> str:
        definition = RangeCheckDefinition(ranges)
        if definition.name not in self.input_checks:
            self.add_input_check(definition)
        return definition.name

    def get_and_declare_follow(self, *,
                               slot: str,
                               literals: list[str] | None = None,
                               ranges: list[tuple[int, int]] | None = None,
                               in_pop: bool) -> str:
        return self._get_and_declare_ambiguity(
            FollowCheck(slot, literals, ranges, pop_check=in_pop)
        )

    def get_and_declare_not_follow(self, *,
                                   slot: str,
                                   literals: list[str] | None = None,
                                   ranges: list[tuple[int, int]] | None = None,
                                   in_pop: bool) -> str:
        return self._get_and_declare_ambiguity(
            FollowCheck(slot, literals, ranges, True, in_pop)
        )

    def get_and_declare_precede(self, *,
                                slot: str,
                                literals: list[str] | None = None,
                                ranges: list[tuple[int, int]] | None = None) -> str:
        return self._get_and_declare_ambiguity(
            PrecedeCheck(slot, literals, ranges)
        )

    def get_and_declare_not_precede(self, *,
                                    slot: str,
                                    literals: list[str] | None = None,
                                    ranges: list[tuple[int, int]] | None = None) -> str:
        return self._get_and_declare_ambiguity(
            PrecedeCheck(slot, literals, ranges, True)
        )

    def get_and_declare_restriction(self, *,
                                    slot: str,
                                    literals: list[str] | None = None,
                                    ranges: list[tuple[int, int]] | None = None) -> str:
        return self._get_and_declare_ambiguity(
            RestrictionCheck(slot, literals, ranges)
        )

    def _get_and_declare_ambiguity(self,
                                   check: AmbiguityCheckDefinition) -> str:
        if check.name not in self.ambiguity_checks:
            self.add_ambiguity_check(check)
        return check.name

    ###################################################################
    # Add functions

    def add_grammar_slot(self, slot: GrammarSlotDefinition):
        self.grammar_slots[slot.name] = slot

    def add_input_check(self, check: InputCheckDefinition):
        self.input_checks[check.name] = check

    def add_function(self, function: FunctionDefinition):
        self.parse_functions[function.name] = function

    def add_goto_entry(self, key: str, target: str):
        self.goto[key] = target

    def add_ambiguity_check(self, check: AmbiguityCheckDefinition):
        self.ambiguity_checks[check.name] = check


@dataclasses.dataclass(frozen=True, slots=True)
class ParserMetadata:
    name: str


##############################################################################
##############################################################################
# Type definitions -- Grammar Slot
##############################################################################


@dataclasses.dataclass(frozen=True, slots=True)
class GrammarSlotDefinition:
    nonterminal: str
    alternate: int
    position: int
    alpha: bool
    beta: bool
    is_initial: bool = False    # needed for naming

    @classmethod
    def from_key_and_grammar(cls,
                             nonterminal_name: str,
                             alternate_index: int,
                             position: int,
                             grammar: _cfg.ContextFreeGrammar,
                             *, is_initial=False) -> typing.Self:
        nonterminal = _cfg.Nonterminal(nonterminal_name)
        alternate = grammar.rules[nonterminal][alternate_index]
        if position != 1:
            alpha = False
        else:
            head = alternate[0]
            alpha = grammar.is_terminal(head) or head not in grammar.nullables
        beta = position == len(alternate)
        return cls(
            nonterminal=nonterminal_name,
            alternate=alternate_index if not is_initial else -1,
            position=position,
            alpha=alpha,
            beta=beta,
            is_initial=is_initial
        )

    @property
    def name(self) -> str:
        return self.get_slot_name(self.nonterminal,
                                  self.alternate,
                                  self.position,
                                  is_initial=self.is_initial)

    @staticmethod
    def get_slot_name(nonterminal: str,
                      alternate: int,
                      position: int,
                      *, is_initial=False):
        if is_initial and alternate < 0:
            return '_initial_grammar_slot'
        if is_initial:
            return f'_initial_grammar_slot_idx{position}'
        if alternate < 0:
            return f'_grammar_slot_{nonterminal}'
        return (f'_grammar_slot_'
                f'{nonterminal}_'
                f'alt{alternate}_'
                f'idx{position}')


##############################################################################
##############################################################################
# Type definitions -- Helper Classes
##############################################################################


class CheckType(enum.Enum):
    Literal = enum.auto()
    Range = enum.auto()


class CheckDefinition:

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @staticmethod
    def format_ranges(ranges: tuple[tuple[int, int], ...]) -> str:
        return '__'.join(
            (f'{chr(start)}_{chr(stop)}'
             if start != stop
             else chr(start))
            for start, stop in ranges
        )


class InputCheckDefinition(CheckDefinition, abc.ABC):

    @abc.abstractmethod
    def get_check_type(self) -> CheckType:
        pass


@dataclasses.dataclass(frozen=True, slots=True)
class LiteralCheckDefinition(InputCheckDefinition):
    text: str

    @property
    def name(self) -> str:
        if not self.text:
            return 'terminal_test_empty'
        return f'terminal_test_literal__{self.text}'

    def get_check_type(self) -> CheckType:
        return CheckType.Literal


@dataclasses.dataclass(frozen=True, slots=True)
class RangeCheckDefinition(InputCheckDefinition):
    ranges: tuple[tuple[int, int], ...]

    @property
    def name(self) -> str:
        return f'terminal_test_range__' + self.format_ranges(self.ranges)

    @property
    def formatted_ranges(self) -> str:
        return self.format_ranges(self.ranges)

    def get_check_type(self) -> CheckType:
        return CheckType.Range

##############################################################################
##############################################################################
# Type definitions -- Parsing Functions
##############################################################################


@dataclasses.dataclass(frozen=True, slots=True)
class FunctionDefinition:
    name: str
    body: list[StatementDefinition]

    @staticmethod
    def mangle_parse_function_name(nonterminal: str):
        return f'nonterminal_check_{nonterminal}'


@dataclasses.dataclass(frozen=True, slots=True)
class StatementDefinition:
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class Comment(StatementDefinition):
    text: str


@dataclasses.dataclass(frozen=True, slots=True)
class ConditionalCheck(StatementDefinition):
    checks: list[str]
    body: list[StatementDefinition]


class NodeAssignmentTarget(enum.Enum):
    CN = enum.auto()
    CR = enum.auto()


@dataclasses.dataclass(frozen=True, slots=True)
class InvokeNodeT(StatementDefinition):
    target: NodeAssignmentTarget
    parent_check: str


@dataclasses.dataclass(frozen=True, slots=True)
class InvokeNodeP(StatementDefinition):
    target: NodeAssignmentTarget
    grammar_slot: str


@dataclasses.dataclass(frozen=True, slots=True)
class InvokeCreate(StatementDefinition):
    grammar_slot: str


@dataclasses.dataclass(frozen=True, slots=True)
class InvokePop(StatementDefinition):
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class InvokeAdd(StatementDefinition):
    grammar_slot: str


@dataclasses.dataclass(frozen=True, slots=True)
class CallFunction(StatementDefinition):
    function: str


@dataclasses.dataclass(frozen=True, slots=True)
class Disambiguate(StatementDefinition):
    constraint_check: str


##############################################################################
##############################################################################
# Type definitions -- Disambiguation Checks
##############################################################################


@dataclasses.dataclass(frozen=True, slots=True)
class AmbiguityCheckDefinition(CheckDefinition, abc.ABC):
    slot: str

    def _get_name(self, base_name, literals, ranges, negated):
        prefix = 'not_' if negated else ''
        base = f'terminal_check_{prefix}{base_name}'
        formatted_literals = '__'.join(literals)
        formatted_ranges = self.format_ranges(ranges)
        if formatted_ranges and formatted_literals:
            return f'{base}__{formatted_literals}__{formatted_ranges}'
        elif formatted_ranges:
            return f'{base}__{formatted_ranges}'
        else:
            return f'{base}__{formatted_literals}'

    @abc.abstractmethod
    def as_pop_check(self) -> bool:
        pass


@dataclasses.dataclass(frozen=True, slots=True)
class PrecedeCheck(AmbiguityCheckDefinition):
    literals: list[str]
    ranges: list[tuple[int, int]]
    negated: bool = False

    @property
    def name(self) -> str:
        return self._get_name('precede',
                              self.literals,
                              self.ranges,
                              self.negated)

    def as_pop_check(self) -> bool:
        return False


@dataclasses.dataclass(frozen=True, slots=True)
class FollowCheck(AmbiguityCheckDefinition):
    literals: list[str]
    ranges: list[tuple[int, int]]
    negated: bool = False
    pop_check: bool = False

    @property
    def name(self) -> str:
        return self._get_name('follow',
                              self.literals,
                              self.ranges,
                              self.negated)

    def as_pop_check(self) -> bool:
        return self.pop_check


@dataclasses.dataclass(frozen=True, slots=True)
class RestrictionCheck(AmbiguityCheckDefinition):
    literals: list[str]
    ranges: list[tuple[int, int]]

    @property
    def name(self) -> str:
        return self._get_name('restriction',
                              self.literals,
                              self.ranges,
                              False)

    def as_pop_check(self) -> bool:
        return True
