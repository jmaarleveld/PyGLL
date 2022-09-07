##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import collections
import dataclasses
import functools
import typing

from ..util.algorithms import relations

##############################################################################
##############################################################################
# Auxiliary Classes
##############################################################################


@dataclasses.dataclass(frozen=True, slots=True)
class Nonterminal:
    name: str


@dataclasses.dataclass(frozen=True, slots=True)
class Terminal:
    ranges: tuple[tuple[int, int], ...] | None
    sequence: str | None

    @classmethod
    def literal(cls, seq: str) -> Terminal:
        return cls(ranges=None, sequence=seq)

    @classmethod
    def empty(cls) -> Terminal:
        return cls(ranges=None, sequence=None)

    @classmethod
    def from_char(cls, char: str) -> Terminal:
        return cls(ranges=None, sequence=char)

    @classmethod
    def character_class(cls,
                        ranges: tuple[tuple[int, int], ...]) -> Terminal:
        return cls(ranges=ranges, sequence=None)

    def is_empty(self):
        return self.ranges is None and self.sequence is None


Alternative = tuple[Nonterminal | Terminal, ...]
Expansion = tuple[Alternative, ...]

GLLBlock = list[Terminal | Nonterminal]


##############################################################################
##############################################################################
# Context Free Grammar
##############################################################################


class ContextFreeGrammar:
    """Class for representing a Context Free Grammar (CFG).
    """

    def __init__(self,
                 start: Nonterminal,
                 rules: dict[Nonterminal, Expansion] = None):
        if rules is None:
            rules = {}
        self.__rules = rules
        self.__start = start
        self.__first = None
        self.__follow = None

    ###################################################################
    # Grammar Printing

    def pprint(self):
        for nonterminal, alternatives in self.__rules.items():
            if nonterminal == self.__start:
                prefix = 'start syntax'
            else:
                prefix = 'syntax'
            expansion = self.__format_expansion(alternatives)
            margin = len(f'{prefix} {nonterminal.name}') + 1
            formatted = '\n'.join(
                ' '*margin + '| ' + exp for exp in expansion[1:]
            )
            base = f'{prefix} {nonterminal.name} = {expansion[0]}'
            if formatted:
                base += '\n' + formatted
                base += '\n' + ' '*margin + ';'
            else:
                base += ';'
            print(base)

    @classmethod
    def __format_expansion(cls, alternatives: Expansion) -> list[str]:
        return [
            cls.__format_alternative(alternative)
            for alternative in alternatives
        ]

    @classmethod
    def __format_alternative(cls, alternative: Alternative) -> str:
        return ' '.join(cls.__format_symbol(symbol)
                        for symbol in alternative)

    @classmethod
    def __format_symbol(cls, symbol: Nonterminal | Terminal) -> str:
        match symbol:
            case Nonterminal(name):
                return name
            case Terminal(ranges=None, sequence=None):
                return '()'
            case Terminal(ranges=None, sequence=seq):
                return '"' + seq + '"'
            case Terminal(ranges=ranges, sequence=None):
                content = ''.join(
                    f'{chr(start)}-{chr(end)}' if start != end else chr(start)
                    for start, end in ranges
                )
                return f'[{content}]'

    ###################################################################
    # Remove redundant empty symbols

    def normalize_null(self) -> ContextFreeGrammar:
        return ContextFreeGrammar(
            start=self.__start,
            rules={
                symbol: self.__normalize_null_alternatives(alternatives)
                for symbol, alternatives in self.__rules.items()
            }
        )

    def __normalize_null_alternatives(self,
                                      alternatives: tuple[Alternative]):
        return tuple(self.__normalize_alternative(alternative)
                     for alternative in alternatives)

    def __normalize_alternative(self, alternative: Alternative):
        if all(self.__is_empty_terminal(x) for x in alternative):
            return Terminal.empty(),
        return tuple(x
                     for x in alternative
                     if not self.__is_empty_terminal(x))

    ###################################################################
    # Compression into more compact terminals

    def compress(self):
        return ContextFreeGrammar(
            start=self.__start,
            rules={
                symbol: self.__compress_alternatives(alternatives)
                for symbol, alternatives in self.__rules.items()
            }
        )

    @classmethod
    def __compress_alternatives(cls, alternatives: Expansion):
        return tuple(cls.__compress_alternative(alternative)
                     for alternative in alternatives)

    @classmethod
    def __compress_alternative(cls, alternative: Alternative):
        parts = []
        current_seq = []
        for symbol in alternative:
            if isinstance(symbol, Terminal) and cls.__is_literal(symbol):
                current_seq.append(cls.__get_literal(symbol))
            else:
                if current_seq:
                    part = Terminal.literal(''.join(current_seq))
                    if not part.sequence:
                        parts.append(Terminal.empty())
                    else:
                        parts.append(part)
                    current_seq = []
                parts.append(symbol)
        if current_seq:
            part = Terminal.literal(''.join(current_seq))
            if not part.sequence:
                parts.append(Terminal.empty())
            else:
                parts.append(part)
        return tuple(parts)

    @classmethod
    def __is_literal(cls, symbol):
        match symbol:
            case Terminal(ranges=None, sequence=_):
                return True
            case Terminal(ranges=((x, y),), sequence=None):
                return x == y
            case _:
                return False

    @classmethod
    def __get_literal(cls, symbol):
        match symbol:
            case Terminal(ranges=None, sequence=None):
                return ''
            case Terminal(ranges=None, sequence=seq):
                return seq
            case Terminal(ranges=((x, y),), sequence=None) if x == y:
                return chr(x)
            case _:
                raise ValueError(f'{symbol} is not a literal')

    ###################################################################
    # Properties and basic interface

    @property
    def start(self) -> Nonterminal:
        return self.__start

    @property
    def rules(self) -> dict[Nonterminal, Expansion]:
        return self.__rules.copy()

    def add_rule(self, symbol: Nonterminal, expansion: Expansion):
        if symbol in self.__rules:
            self.__rules[symbol] += expansion
        else:
            self.__rules[symbol] = expansion

    ###################################################################
    # Computing first and follow sets

    def test_for_sequence(self,
                          nonterminal: Nonterminal,
                          alternate: int,
                          index: int) -> frozenset[Terminal]:
        epsilon = Terminal.empty()
        if self.__rules[nonterminal][alternate][index:] == (epsilon,):
            return frozenset({epsilon})
        first = self.first_for_sequence(nonterminal, alternate, index)
        if any(self.__is_empty_terminal(x) for x in first):
            follow = self.follow_for_sequence(nonterminal, alternate, index)
            return first | follow
        return first

    def test(self,
             symbol: Nonterminal | Terminal) -> frozenset[Terminal]:
        first = self.first(symbol)
        if any(self.__is_empty_terminal(x) for x in first):
            return first | self.follow(symbol)
        return first

    @functools.cache
    def first_for_sequence(self,
                           nonterminal: Nonterminal,
                           alternate: int,
                           index: int) -> frozenset[Terminal]:
        sequence = self.__rules[nonterminal][alternate][index:]
        first = set()
        epsilon = Terminal.empty()
        for symbol in sequence:
            addition = self.first(symbol)
            first |= addition - {epsilon}
            if epsilon not in addition:
                break
        else:
            first.add(epsilon)
        return frozenset(first)

    def first(self, x: Nonterminal | Terminal) -> frozenset[Terminal]:
        if self.__first is None:
            # first(x) can be computed by considering the
            # transitive closure of the relation R defined
            # by: x R y if and only if
            #       1) x -> y, or
            #       2) x -> yz, or
            #       3) x -> wyz
            # Here, z is any arbitrary sequence of terminals
            # and nonterminals. w is a sequence of nullable
            # nonterminals.
            # In the following code, we first build this relation.
            # Next, we compute the transitive closure.
            # The transitive closure immediately gives us
            # first(x).
            pairs = self.__build_directly_followed_by_relation()
            rel = relations.Relation(pairs)
            self.__first = {
                key: [x for x in value if isinstance(x, Terminal)]
                for key, value in rel.transitive_closure().as_dict().items()
            }
        if isinstance(x, Terminal):
            return frozenset({x})
        return frozenset(self.__first[x])

    def __build_directly_followed_by_relation(self) -> set[tuple[Nonterminal, Terminal]]:
        pairs = set()
        for nonterminal, alternatives in self.__rules.items():
            for alternative in alternatives:
                for symbol in alternative:
                    if isinstance(symbol, Nonterminal):
                        pairs.add((nonterminal, symbol))
                        if symbol not in self.nullables:
                            break
                    elif self.__is_empty_terminal(symbol):
                        pairs.add((nonterminal, Terminal.empty()))
                    else:
                        pairs.add((nonterminal, symbol))
                        break
                else:
                    pairs.add((nonterminal, Terminal.empty()))
        return pairs

    @functools.cache
    def follow_for_sequence(self,
                            nonterminal: Nonterminal,
                            alternate: int,
                            index: int) -> frozenset[Terminal]:
        sequence = self.__rules[nonterminal][alternate][index+1:]
        follow = set()
        epsilon = Terminal.empty()
        for symbol in sequence:
            first = self.first(symbol)
            follow |= (first - {epsilon})
            if epsilon not in first:
                break
        else:
            follow |= self.follow(nonterminal)
        return frozenset(follow)

    def follow(self, x: Nonterminal) -> frozenset[Terminal]:
        if self.__follow is None:
            # Initialize follow mapping
            self.__build_follow_mapping()
        return frozenset(self.__follow[x])

    def __build_follow_mapping(self):
        # There are two steps. First, we compute the
        # "base" follow relations. This means that we
        # identify pairs of nonterminals (x, y)
        # such that follow(x) <= follow(y).
        # We also build the initial follow sets using the
        # first(x) sets.
        # The second step is to build the follow(x) mapping
        # using a simple fixed-point algorithm:
        # we keep updating the final result until
        # no more changes occur.

        # Step 1:
        follow_mapping = collections.defaultdict(set)
        follow_relations = set()
        epsilon = Terminal.empty()
        epsilon_set = {epsilon}
        for nonterminal, alternatives in self.__rules.items():
            for alternative in alternatives:
                for index, symbol in enumerate(alternative):
                    if isinstance(symbol, Terminal):
                        continue
                    assert isinstance(symbol, Nonterminal)
                    remainder = alternative[index+1:]
                    if not remainder:
                        # Rule of the form A -> pB
                        # follow(A) <= follow(B),
                        # since every item in follow(A)
                        # can also follow B.
                        follow_relations.add((nonterminal, symbol))
                        continue
                    for remainder_symbol in remainder:
                        first = self.first(remainder_symbol)
                        follow_mapping[symbol] |= first - epsilon_set
                        if epsilon not in first:
                            break
                    else:
                        # Rule of the form A -> pBq, where
                        # q is nullable (epsilon in first(q)).
                        # This means that every item in follow(A)
                        # may follow B; follow(A) <= follow(B)
                        follow_relations.add((nonterminal, symbol))

        # Step 2:
        while True:
            changed = False
            for x, y in follow_relations:
                # follow(x) <= follow(y)
                if not (follow_mapping[x] <= follow_mapping[y]):
                    changed = True
                    follow_mapping[y] |= follow_mapping[x]
            if not changed:
                break

        self.__follow = dict(follow_mapping)

    ###################################################################
    # Handling of reachable nonterminals

    @functools.cached_property
    def reachable_nonterminals(self) -> frozenset[Nonterminal]:
        reachables = set()
        new = collections.deque()
        new.append(self.__start)
        while new:
            start = new.popleft()
            reachables |= {
                symbol
                for alternative in self.__rules[start]
                for symbol in alternative
                if isinstance(symbol, Nonterminal)

            }
        return frozenset(reachables)

    ###################################################################
    # Handling of Nullable nonterminals

    @functools.cached_property
    def nullables(self) -> frozenset[Nonterminal]:
        nullables = set()
        universe = set(self.__rules)
        while True:
            additions = {
                nonterminal
                for nonterminal in universe
                for rule in self.__rules[nonterminal]
                if self.__rule_is_nullable(rule, nullables)
            }
            if additions <= nullables:
                break
            nullables |= additions
        return frozenset(nullables)

    @classmethod
    def __rule_is_nullable(cls,
                           rule: Alternative,
                           nullables: set[Nonterminal]) -> bool:
        for symbol in rule:
            if isinstance(symbol, Nonterminal):
                if symbol not in nullables:
                    return False
            else:
                assert isinstance(symbol, Terminal)
                if not cls.__is_empty_terminal(symbol):
                    return False
        return True

    ###################################################################
    # Helpers

    @staticmethod
    def __is_empty_terminal(x: Terminal) -> bool:
        return x.ranges is None and x.sequence is None

    ###################################################################
    # GLL Specific functions

    @staticmethod
    def is_terminal(symbol: Terminal | Nonterminal) -> bool:
        return isinstance(symbol, Terminal)

    @classmethod
    def compute_gll_blocks(
            cls,
            alternate: Alternative) -> typing.Iterable[tuple[int, GLLBlock]]:
        """Divide the given input alternate into GLL blocks.

        A GLL block is either
           1) the empty string
           2) a sequence of terminals followed by a nonterminal
           3) a sequence of terminals, which is (in the alternate)
               not followed by a literal
        """
        start = 0
        stop = 0
        last_is_nonterminal = False
        while start < len(alternate):
            while stop < len(alternate) and cls.is_terminal(alternate[stop]):
                stop += 1
            if stop == len(alternate):
                block = alternate[start:stop]
                yield start, block
                last_is_nonterminal = not cls.is_terminal(block[-1])
                break
            else:
                stop += 1
                block = alternate[start:stop]
                yield start, block
                last_is_nonterminal = not cls.is_terminal(block[-1])
            start = stop
        if last_is_nonterminal:
            yield len(alternate), ()
