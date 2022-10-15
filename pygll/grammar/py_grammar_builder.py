"""
Convenient ways of defining grammars in pure Python.

The goal of this module is to provide functionality
which allows the definition of grammars inside Python
code in an easy to write manner.
"""

##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import string

from . import grammar_definitions as _defs

##############################################################################
##############################################################################
# Public API 
##############################################################################


def lexical(name, *initial_rules, **named_initial_rules):
    return _rule_factory('lexical', name, initial_rules, named_initial_rules)


def syntax(name, *initial_rules, **named_initial_rules):
    return _rule_factory('syntax', name, initial_rules, named_initial_rules)


def keywords(name, *initial_rules, **named_initial_rules):
    return _rule_factory('keywords', name, initial_rules, named_initial_rules)


def layout(name, *initial_rules, **named_initial_rules):
    return _rule_factory('layout', name, initial_rules, named_initial_rules)


def named(name: str, rule):
    rule = _maybe_convert_literal(rule)
    if isinstance(rule, _defs.Symbol):
        return _defs.LabeledRule((), rule, name)
    if isinstance(rule, _AltBuilder):
        return _defs.LabeledRule((), rule.finalize(), name)
    raise ValueError(f'Cannot name {rule.__class__.__name__}')


def assoc(*rules):
    return _apply_assoc(rules, _defs.AssociativityOptions.Assoc)


def non_assoc(*rules):
    return _apply_assoc(rules, _defs.AssociativityOptions.NonAssoc)


def left(*rules):
    return _apply_assoc(rules, _defs.AssociativityOptions.Left)


def right(*rules):
    return _apply_assoc(rules, _defs.AssociativityOptions.Right)


def _apply_assoc(rules, associativity):
    if len(rules) == 1:
        return _tag_assoc(rules[0], associativity)
    converted_rules: list[_defs.Production] = []
    for rule in rules:
        rule = _maybe_convert_literal(rule)
        if isinstance(rule, _defs.Symbol):
            converted_rules.append(_defs.UnlabeledRule((), rule))
        elif isinstance(rule, _AltBuilder):
            converted_rules.append(_defs.UnlabeledRule((), rule.finalize()))
        elif isinstance(rule, _ProductionBuilder):
            raise ValueError('Cannot have multiple productions inside assoc.')
        else:
            raise ValueError(f'Cannot convert type '
                             f'{rule.__class__.__name__} to alternate.')
    return _defs.AssociativityGroup(_defs.AssociativityOptions.Assoc,
                                    _defs.Choice((tuple(converted_rules),)))


def _tag_assoc(rule, tag):
    rule = _maybe_convert_literal(rule)
    if isinstance(rule, _defs.Symbol):
        return _ProductionBuilder(rule, assoc=tag)
    elif isinstance(rule, _AltBuilder):
        return _ProductionBuilder(rule.finalize(), assoc=tag)
    elif isinstance(rule, _ProductionBuilder):
        return _ProductionBuilder(
            _defs.AssociativityGroup(tag, rule.finalize())
        )
    raise ValueError(f'Cannot apply associativity to object '
                     f'of type {rule.__class__.__name__}')


def lit(x: str):
    return literal(x)


def literal(x: str):
    return _AltBuilder(_defs.Literal(x))


def chars(*pairs: list[str]):
    assert all(len(x) == 2 for x in pairs)
    return _CharClassBuilder(
        _defs.CharacterRange(
            tuple(
                (ord(start), ord(stop))
                for start, stop in pairs
            )
        )
    )


def not_precede(a, b):
    """A should not precede B"""
    a = _maybe_convert_literal(a)
    b = _maybe_convert_literal(b)
    if isinstance(a, _AltBuilder):
        a = a.finalize()
    if isinstance(b, _AltBuilder):
        b = b.finalize()
    return _AltBuilder(_defs.NotPrecede(b, a))


def not_followed_by(a, b):
    """A should not be followed by B"""
    a = _maybe_convert_literal(a)
    b = _maybe_convert_literal(b)
    if isinstance(a, _AltBuilder):
        a = a.finalize()
    if isinstance(b, _AltBuilder):
        b = b.finalize()
    return _AltBuilder(_defs.NotFollow(a, b))


##############################################################################
##############################################################################
# Production Builder
##############################################################################


class _ProductionBuilder:

    def __init__(self, wrapped, **kwargs):
        self.__wrapped = wrapped
        self.__info = kwargs

    def finalize(self) -> _defs.Production:
        return self.__wrapped


##############################################################################
##############################################################################
# Rule Builder
##############################################################################


def _rule_factory(rule_type: str,
                  name: str,
                  initial_rules,
                  named_initial_rules):
    rules = []
    for rule in initial_rules:
        if isinstance(rule, str):
            rule = literal(rule)
        rules.append(_defs.UnlabeledRule((), rule.finalize()))
    for rule_name, rule in named_initial_rules.items():
        if isinstance(rule, str):
            rule = literal(rule)
        rules.append(_defs.LabeledRule((), rule.finalize(), rule_name))
    return _RuleBuilder(rule_type, name, rules)


class _RuleBuilder:
    """The _RuleBuilder class is used to build grammar rules.
    Here, by grammar rules we mean expansions like
    syntax A = B | C | D;

    The grammar rule has a type (syntax, lexical, layout, keyword),
    a name, and a collection of initial rules.
    Note that the initial rules must be a list of Productions.

    The operations on a rule builder are limited.
    One can add additional rules using the |= operator,
    and one can make a grammar with the current rule
    as a starting nonterminal.
    """

    def __init__(self, rule_type: str, name: str, initial_rules=None):
        self.__type = rule_type
        self.__name = name
        if initial_rules is None:
            initial_rules = []
        self.__rules = initial_rules

    def finalize(self) -> _defs.SyntaxDefinition:
        """Retrieve the final grammar rule defined by this builder.
        """
        prod=_defs.Choice((tuple(self.__rules),))
        match self.__type:
            case 'syntax':
                return _defs.Syntax(self.__name, prod)
            case 'lexical':
                return _defs.Lexical(self.__name, prod)
            case 'keywords':
                return _defs.Keywords(self.__name, prod)
            case 'layout':
                return _defs.Layout(self.__name, prod)
            case _:
                raise ValueError(self.__type)

    def make_grammar(self, language: str, *nonterminals: _RuleBuilder, layout=None):
        """Make a grammar, with the current nonterminal as the starting nonterminal.
        All nonterminals in the grammar must be explicitly passed to this function
        in order to be registered correctly.

        Optionally, the layout may be given. Otherwise, any whitespace is
        considered layout.
        """
        mapping: dict[str, _defs.SyntaxDefinition] = {}
        for n in nonterminals:
            rule = n.finalize()
            mapping[rule.name] = rule
        return _defs.GrammarDefinition(
            language,
            self.__name,
            layout if layout else self._default_layout,
            mapping
        )

    @property
    def _default_layout(self):
        layout = lexical('layout', *string.whitespace)
        return layout.finalize()
    
    def __ior__(self, other):
        """Add another alternate to this rule.

        other can be one of the following:
            - An _AltBuilder instance
            - A _defs.UnlabeledRule
            - A _defs.LabeledRule
            - An instance of _CharClassBuilder
            - Any type _maybe_convert_literal knows about (i.e. str)
        """
        other = _maybe_convert_literal(other)
        if isinstance(other, _AltBuilder):
            rule = _defs.UnlabeledRule((), other.finalize())
            self.__rules.append(rule)
            return self
        if isinstance(other, _CharClassBuilder):
            rule = _defs.UnlabeledRule((), other.finalize())
            self.__rules.append(rule)
            return rule 
        if isinstance(other, (_defs.UnlabeledRule, _defs.LabeledRule)):
            self.__rules.append(other)
            return self 
        return NotImplemented

    @property
    def ref(self):
        """Use this function when referring to this rule in an alternate.
        """
        return _AltBuilder(_defs.Nonterminal(self.__name)) 


##############################################################################
##############################################################################
# Expansion Builder
##############################################################################


class _AltBuilder: 
    """This class is a builder for single alternates in rules.
    """

    def __init__(self, definition):
        self.__def = definition

    def finalize(self) -> _defs.Symbol:
        return self.__def
    
    def __getitem__(self, index):
        """Slice notation is used to denote repetitions of a symbol.
        We have the following conventions:

        [:1:]     --> Optional (?)
        [::]      --> Kleene Star (*)
        [1::]     --> Plus (+)
        [n:m:]    --> Range ({n, m})
        [::sep]   --> Kleene Star with separator
        [1::sep]  --> Plus with separator
        [n:m:sep] --> Range with separator

        The separator must either be an _xxxBuilder type,
        or a type compatible with _maybe_convert_literal.
        """
        if isinstance(index, int):
            return _AltBuilder(_defs.Sequence((self.__def,) * index))
        assert isinstance(index, slice)
        start, stop = index.start, index.stop
        sep = _maybe_convert_literal(index.step)
        sep = _maybe_finalize(sep)
        if start is None and stop is None:
            if sep is None:
                return _AltBuilder(_defs.StarRepeat(self.__def))
            return _AltBuilder(
                _defs.StarRepeatWithSeparator(self.__def, sep)
            )
        elif start == 1 and stop is None:
            if sep is None:
                return _AltBuilder(_defs.PlusRepeat(self.__def))
            return _AltBuilder(
                _defs.PlusRepeatWithSeparator(self.__def, sep)
            )
        elif start is None and stop == 1:
            assert sep is None
            return _AltBuilder(_defs.Optional(self.__def))
        else:
            if sep is None:
                return _AltBuilder(
                    _defs.RangeRepeat(self.__def, start, stop)
                )
            return _AltBuilder(
                _defs.RangeRepeatWithSeparator(self.__def, sep, start, stop)
            )

    def __generic_operator(self, other, cls):
        other = _maybe_convert_literal(other)
        if isinstance(other, _defs.Symbol):
            return self.__maybe_combine(cls, other)
        if isinstance(other, _AltBuilder):
            return self.__maybe_combine(cls, other.finalize())
        if isinstance(other, _CharClassBuilder):
            return self.__maybe_combine(cls, other.finalize())
        return NotImplemented

    def __maybe_combine(self, cls, other):
        if isinstance(self.__def, cls):
            return _AltBuilder(cls(self.__def.items + (other,)))
        return _AltBuilder(cls((self.__def, other)))

    def __generic_reverse_operator(self, other, op):
        other = _maybe_convert_literal(other)
        if isinstance(other, _CharClassBuilder):
            return op(_AltBuilder(other.finalize()), self)
        if isinstance(other, _defs.Symbol):
            return op(_AltBuilder(other), self)
        return op(other, self)

    def __add__(self, other):
        return self.__generic_operator(other, _defs.Sequence)
    
    def __radd__(self, other):
        return self.__generic_reverse_operator(other, lambda x, y: x + y)

    def __or__(self, other):
        return self.__generic_operator(other, _defs.Alternative)

    def __ror__(self, other):
        return self.__generic_reverse_operator(other, lambda x, y: x | y)

    def __matmul__(self, other):
        """Name a symbol or group.

        The syntax `self @ other` is equivalent to `Self other`
        in a grammar definition, i.e. the symbol defined
        by self is referred to by the name other.
        """
        if not isinstance(other, str):
            return NotImplemented
        return _AltBuilder(_defs.LabeledSymbol(name=other, symbol=self.__def))

    def __lshift__(self, other):
        if not isinstance(other, _AltBuilder):
            return NotImplemented
        return _AltBuilder(_defs.Precede(other.finalize(), self.finalize()))

    def __rlshift__(self, other):
        # other << self
        other = _maybe_convert_literal(other)
        if isinstance(other, _AltBuilder):
            other = other.finalize()
        if not isinstance(other, _defs.Symbol):
            return NotImplemented
        return _AltBuilder(_defs.Precede(self.finalize(), other))

    def __rshift__(self, other):
        # self >> other
        other = _maybe_convert_literal(other)
        if isinstance(other, _AltBuilder):
            other = other.finalize()
        return _AltBuilder(_defs.Follow(self.finalize(), other))


##############################################################################
##############################################################################
# Char Class Builder
##############################################################################


class _CharClassBuilder:

    def __init__(self, inner):
        self.__cls = inner

    def finalize(self):
        return self.__cls 

    def __or__(self, other):
        if not isinstance(other, _CharClassBuilder):
            return NotImplemented
        return _CharClassBuilder(
            _defs.CharacterClassUnion(self.finalize(), other.finalize())
        )

    def __and__(self, other):
        if not isinstance(other, _CharClassBuilder):
            return NotImplemented
        return _CharClassBuilder(
            _defs.CharacterClassIntersection(self.finalize(), other.finalize())
        )

    def __sub__(self, other):
        if not isinstance(other, _CharClassBuilder):
            return NotImplemented
        return _CharClassBuilder(
            _defs.CharacterClassDifference(self.finalize(), other.finalize())
        )

    def __add__(self, other):
        return _AltBuilder(self) + other

    def __radd__(self, other):
        return other + _AltBuilder(self)

    def __invert__(self):
        return _CharClassBuilder(
            _defs.CharacterClassComplement(self.finalize())
        )

    def __getitem__(self, index):
        return self.cast().__getitem__(index)

    def __matmul__(self, other):
        return self.cast() @ other

    def cast(self):
        return _AltBuilder(self.finalize())
    

##############################################################################
##############################################################################
# Utility Functions
##############################################################################


def _maybe_convert_literal(x):
    if isinstance(x, str):
        if not x:
            return _defs.Empty()
        return _defs.Literal(x)
    if isinstance(x, tuple) and x == ():
        return _defs.Empty()
    return x


def _maybe_finalize(x):
    if isinstance(x, _AltBuilder):
        return x.finalize()
    return x


##############################################################################
##############################################################################
# Testing Code
##############################################################################


def test():
    integer = lexical('integer', '0', chars(['1', '9']) + chars(['0', '9'])[:])
    string = lexical('string', lit('"') + (~chars(['"', '"'])) + lit('"'))
    boolean = lexical('boolean', 'true', 'false')
    array = syntax('array')
    mapping = syntax('object')
    value = syntax('value', integer.ref, string.ref, boolean.ref, array.ref, mapping.ref)
    array |= lit("[") + value.ref[::','] + lit("]")
    mapping |= lit('{') + value.ref[::','] + lit(']')
    json = syntax('json', array.ref, mapping.ref)
    return json.make_grammar('JSON', integer, string, boolean, array, mapping, value)
