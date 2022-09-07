##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import collections
import dataclasses
import enum
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
    cfg_node: _cfg.Nonterminal
    def_node: _def.SyntaxDefinition | _def.Symbol


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
        pass

    @classmethod
    def from_grammar_definition(
            cls, definition: _def.GrammarDefinition) -> typing.Self:
        cfg = _cfg.ContextFreeGrammar(
            start=_cfg.Nonterminal(name=definition.start)
        )

    @classmethod
    def __convert_to_cfg(cls,
                         symbol: _def.Symbol,
                         current_rule: str,
                         mangler: NameMangler):
        match symbol:
            case _def.Nonterminal(name):
                pass
            case _def.StarRepeat(group):
                pass
            case _def.PlusRepeat(group):
                pass
            case _def.RangeRepeat(group):
                pass
            case _def.StarRepeatWithSeparator(group, separator):
                pass
            case _def.PlusRepeatWithSeparator(group, separator):
                pass
            case _def.RangeRepeatWithSeparator(group, separator):
                pass
            case _def.Optional(group):
                pass
            case _def.Alternative(groups):
                pass
            case _:
                pass


