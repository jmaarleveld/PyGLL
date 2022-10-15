##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import abc
import dataclasses
import enum
import functools
import operator

from ...util.algorithms import int_sets as _int_sets

##############################################################################
##############################################################################
# Constants
##############################################################################


class AssociativityOptions(enum.Enum):
    NonAssoc = enum.auto()
    Assoc = enum.auto()
    Left = enum.auto()
    Right = enum.auto()


##############################################################################
##############################################################################
# Grammar Class
##############################################################################


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class GrammarDefinition:
    language: str
    start: str
    layout: Layout
    rules: list[SyntaxDefinition]


##############################################################################
##############################################################################
# Syntax Definitions
##############################################################################


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class SyntaxDefinition(abc.ABC):
    name: str
    production: Production


class Layout(SyntaxDefinition):
    pass


class Keywords(SyntaxDefinition):
    pass


class Lexical(SyntaxDefinition):
    pass


class Syntax(SyntaxDefinition):
    pass


##############################################################################
##############################################################################
# Productions
##############################################################################


class Production(abc.ABC):
    """Productions are the part of grammar rules which do not deal
    with single expansions of nonterminals.
    Specifically, productions deal with priorities and alternatives
    for rules.
    """
    __slots__ = ()


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Reference(Production):
    referenced: str


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class _Rule(Production, abc.ABC):
    modifiers: tuple[ProductionModifier, ...]
    expansion: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class LabeledRule(_Rule):
    name: str


# Rascal supports unlabeled rules, but to support
# them you need something like Rascal's concrete
# syntax fragments.
# Supporting this in Python would at the very least
# not be very clean, and it would not work nicely
# with static typing.
#
# Unlabeled rules still have their place, though.
# They are still the cleanest way of defining
# lexical, layout, and keyword nonterminals.
# However, they will be banned for syntax
# nonterminals.
@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class UnlabeledRule(_Rule):
    pass


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class AssociativityGroup(Production):
    associativity: AssociativityOptions
    group: Production


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Choice(Production):
    choices: tuple[tuple[Production, ...], ...]


class ProductionModifier(abc.ABC):
    pass


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class AssociativityModifier(ProductionModifier):
    associativity: AssociativityOptions


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class BracketModifier(ProductionModifier):
    pass


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class TagModifier(ProductionModifier):
    name: str
    content: str | None = None


##############################################################################
##############################################################################
# Rules (productions)
##############################################################################


class Symbol(abc.ABC):
    __slots__ = ()


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Nonterminal(Symbol):
    nonterminal: str


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Parameter(Symbol):
    nonterminal: str


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Parametrized(Symbol):
    nonterminal: str
    parameters: tuple[Symbol, ...]


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class LabeledSymbol(Symbol):
    name: str
    symbol: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Literal(Symbol):
    text: str


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class CaseInsensitiveLiteral(Symbol):
    text: str


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class PlusRepeat(Symbol):
    symbol: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class StarRepeat(Symbol):
    symbol: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class RangeRepeat(Symbol):
    symbol: Symbol
    minimum: int | None = None
    maximum: int | None = None


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class PlusRepeatWithSeparator(Symbol):
    symbol: Symbol
    separator: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class StarRepeatWithSeparator(Symbol):
    symbol: Symbol
    separator: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class RangeRepeatWithSeparator(Symbol):
    symbol: Symbol
    separator: Symbol
    minimum: int | None = None
    maximum: int | None = None


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Optional(Symbol):
    symbol: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Alternative(Symbol):
    alternatives: tuple[Symbol, ...]


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Sequence(Symbol):
    items: tuple[Symbol, ...]


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Empty(Symbol):
    pass


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class EndOfLine(Symbol):
    symbol: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class StartOfLine(Symbol):
    symbol: Symbol


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Except(Symbol):
    symbol: Symbol
    label: str


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class _FollowOrPrecede(Symbol, abc.ABC):
    symbol: Symbol
    constraint: Symbol


class Follow(_FollowOrPrecede):
    pass


class NotFollow(_FollowOrPrecede):
    pass


class Precede(_FollowOrPrecede):
    pass


class NotPrecede(_FollowOrPrecede):
    pass


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Restriction(Symbol):
    symbol: Symbol
    constraint: Symbol


class CharacterClass(Symbol, abc.ABC):

    UNICODE_MIN = 0
    UNICODE_MAX = 0x10_FF_FF
    UNICODE_RANGE = (UNICODE_MIN, UNICODE_MAX)

    @abc.abstractmethod
    def resolve(self) -> tuple[tuple[int, int], ...]:
        pass


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class CharacterRange(CharacterClass):
    ranges: tuple[tuple[int, int], ...]

    def resolve(self) -> tuple[tuple[int, int], ...]:
        return _int_sets.IntSet(
            self.ranges,
            self.UNICODE_RANGE
        ).ranges


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class CharacterClassComplement(CharacterClass):
    cls: CharacterClass

    def resolve(self) -> tuple[tuple[int, int], ...]:
        return (~_int_sets.IntSet(
            self.cls.resolve(),
            self.UNICODE_RANGE
        )).ranges


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class CharacterClassDifference(CharacterClass):
    left: CharacterClass
    right: CharacterClass

    def resolve(self) -> tuple[tuple[int, int], ...]:
        left = _int_sets.IntSet(self.left.resolve(), self.UNICODE_RANGE)
        right = _int_sets.IntSet(self.right.resolve(), self.UNICODE_RANGE)
        return (left - right).ranges


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class CharacterClassUnion(CharacterClass):
    left: CharacterClass
    right: CharacterClass

    def resolve(self) -> tuple[tuple[int, int], ...]:
        left = _int_sets.IntSet(self.left.resolve(), self.UNICODE_RANGE)
        right = _int_sets.IntSet(self.right.resolve(), self.UNICODE_RANGE)
        return (left | right).ranges


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class CharacterClassIntersection(CharacterClass):
    left: CharacterClass
    right: CharacterClass

    def resolve(self) -> tuple[tuple[int, int], ...]:
        left = _int_sets.IntSet(self.left.resolve(), self.UNICODE_RANGE)
        right = _int_sets.IntSet(self.right.resolve(), self.UNICODE_RANGE)
        return (left & right).ranges
