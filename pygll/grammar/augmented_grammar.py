##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import collections
import dataclasses
import enum
import functools
import typing

from . import context_free_grammar as _cfg
from . import grammar_definitions as _def

##############################################################################
##############################################################################
# Classes for mapping the two basic grammar types to one another
##############################################################################


class RepeatType(enum.Enum):
    Star = enum.auto()
    Plus = enum.auto()
    Range = enum.auto()


@dataclasses.dataclass(frozen=True, slots=True)
class GrammarMapping:
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class DirectMap(GrammarMapping):
    cfg_node: _cfg.Nonterminal | _cfg.Terminal
    def_node: _def.SyntaxDefinition | _def.Symbol


@dataclasses.dataclass(frozen=True, slots=True)
class SequenceMap(GrammarMapping):
    def_node: _def.SyntaxDefinition | _def.Symbol
    cfg_node: list[_cfg.Nonterminal | _cfg.Terminal]


@dataclasses.dataclass(frozen=True, slots=True)
class NamedMap(GrammarMapping):
    def_node: _def.SyntaxDefinition | _def.Symbol
    cfg_node: _cfg.Nonterminal
    name: str


@dataclasses.dataclass(frozen=True, slots=True)
class InlineChoice(GrammarMapping):
    cfg_node: _cfg.Nonterminal
    def_node: _def.Alternative


@dataclasses.dataclass(frozen=True, slots=True)
class RepeatGroup(GrammarMapping):
    repeat_type: RepeatType
    with_separator: bool
    cfg_node: _cfg.Nonterminal
    def_node: _def.Symbol


@dataclasses.dataclass(frozen=True, slots=True)
class QuestionMark(GrammarMapping):
    cfg_node: _cfg.Nonterminal
    def_node: _def.Optional


@dataclasses.dataclass(frozen=True, slots=True)
class Layout(GrammarMapping):
    cfg_node: _cfg.Nonterminal


##############################################################################
##############################################################################
# Name manging helper
##############################################################################


class NameMangler:

    def __init__(self, prefix: str):
        self.__prefix = prefix
        self.__names = collections.defaultdict(int)

    def mangle(self, *parts: str) -> str:
        base_name = '_'.join(parts)
        self.__names[base_name] += 1
        return f'{self.__prefix}_{self.__names[base_name] - 1}_{base_name}'


##############################################################################
##############################################################################
# Augmented Grammar Class
##############################################################################


class AugmentedGrammar:

    def __init__(self,
                 cfg: _cfg.ContextFreeGrammar,
                 definition: _def.GrammarDefinition,
                 grammar_mapping: ...):
        self.__def = definition

    @classmethod
    def from_grammar_definition(
            cls, definition: _def.GrammarDefinition) -> typing.Self:
        cfg = _cfg.ContextFreeGrammar(
            start=_cfg.Nonterminal(name=definition.start)
        )

    @property
    def grammar_definition(self) -> _def.GrammarDefinition:
        return self.__def


##############################################################################
##############################################################################
# Augmented Grammar Creation
##############################################################################


class MappingResult(typing.NamedTuple):
    mapping: GrammarMapping
    rule: _cfg.Alternative


@functools.singledispatch
def _map_definition_to_cfg(
        symbol: _def.Symbol,
        cfg: _cfg.ContextFreeGrammar) -> MappingResult:
    """Utility function for generating a CFG from a grammar definition.

    This function does two things. First of all, it generates a
    datastructure which details how the generated context free
    grammar can be mapped to the CST defined by the grammar
    definition. This is later used to generate the CST generator
    when generating the parser.

    This function also populates the (initially empty) context
    free grammar.

    Note that this function handles converting a single
    _alternate_ to context free grammar form.

    This function returns a tuple. The first element is the
    datastructure detailing the mapping from CFG to
    grammar definition. The second element is the
    expansion of the alternate, usable for the
    `cfg.add_rule` method.
    """
    raise ValueError(f'No handler found for symbol type: {symbol.__name__}')


@_map_definition_to_cfg.register
def _(symbol: _def.Nonterminal,
      cfg: _cfg.ContextFreeGrammar) -> MappingResult:
    return MappingResult(
        mapping=DirectMap(def_node=symbol,
                          cfg_node=_cfg.Nonterminal(symbol.nonterminal)),
        rule=(_cfg.Nonterminal(symbol.nonterminal),)
    )


@_map_definition_to_cfg.register
def _(symbol: _def.Parameter, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Parameter')


@_map_definition_to_cfg.register
def _(symbol: _def.Parametrized, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Parameterized')


@_map_definition_to_cfg.register
def _(symbol: _def.LabeledSymbol, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('LabeledSymbol')


@_map_definition_to_cfg.register
def _(symbol: _def.Literal,
      cfg: _cfg.ContextFreeGrammar) -> MappingResult:
    node = _cfg.Terminal.literal(symbol.text)
    return MappingResult(
        mapping=DirectMap(def_node=symbol, cfg_node=node),
        rule=(node,)
    )


@_map_definition_to_cfg.register
def _(symbol: _def.CaseInsensitiveLiteral,
      cfg: _cfg.ContextFreeGrammar):
    characters = [(ord(char.lower()), ord(char.upper()))
                  for char in symbol.text]
    terminals = [
        _cfg.Terminal.character_class(
            (
                (lower, lower),
                (upper, upper)
            )
        )
        for lower, upper in characters
    ]
    return MappingResult(
        mapping=SequenceMap(def_node=symbol, cfg_node=terminals),
        rule=tuple(terminals)
    )


@_map_definition_to_cfg.register
def _(symbol: _def.StarRepeat, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('StarRepeat')


@_map_definition_to_cfg.register
def _(symbol: _def.PlusRepeat, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('PlusRepeat')


@_map_definition_to_cfg.register
def _(symbol: _def.RangeRepeat, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('RangeRepeat')


@_map_definition_to_cfg.register
def _(symbol: _def.StarRepeatWithSeparator, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('StarRepeatWithSeparator')


@_map_definition_to_cfg.register
def _(symbol: _def.PlusRepeatWithSeparator, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('PlusRepeatWithSeparator')


@_map_definition_to_cfg.register
def _(symbol: _def.RangeRepeatWithSeparator, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('RangeRepeatWithSeparator')


@_map_definition_to_cfg.register
def _(symbol: _def.Optional, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Optional')


@_map_definition_to_cfg.register
def _(symbol: _def.Alternative, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Alternative')


@_map_definition_to_cfg.register
def _(symbol: _def.Sequence, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Sequence')


@_map_definition_to_cfg.register
def _(symbol: _def.Empty,
      cfg: _cfg.ContextFreeGrammar) -> MappingResult:
    epsilon = _cfg.Terminal.empty()
    return MappingResult(
        mapping=DirectMap(def_node=symbol, cfg_node=epsilon),
        rule=(epsilon,)
    )


@_map_definition_to_cfg.register
def _(symbol: _def.StartOfLine, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('StartOfLine')


@_map_definition_to_cfg.register
def _(symbol: _def.EndOfLine, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('EndOfLine')


@_map_definition_to_cfg.register
def _(symbol: _def.Except, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Except')


@_map_definition_to_cfg.register
def _(symbol: _def.NotFollow, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('NotFollow')


@_map_definition_to_cfg.register
def _(symbol: _def.Follow, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Follow')


@_map_definition_to_cfg.register
def _(symbol: _def.NotPrecede, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('NotPrecede')


@_map_definition_to_cfg.register
def _(symbol: _def.Precede, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Precede')


@_map_definition_to_cfg.register
def _(symbol: _def.Restriction, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('Restriction')


@_map_definition_to_cfg.register
def _(symbol: _def.CharacterClass, cfg: _cfg.ContextFreeGrammar):
    _not_implemented('CharacterClass')


def _not_implemented(operation: str):
    raise NotImplementedError(f'Unsupported grammar construct: {operation}')

