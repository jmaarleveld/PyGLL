"""
This module provides tools for working with mathematical
relationships.
"""

##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import functools
import typing


##############################################################################
##############################################################################
# Relation Class
##############################################################################


U = typing.TypeVar('U')
V = typing.TypeVar('V')


class Relation(typing.Generic[U, V]):
    """Class used to represent a mathematical relation.

    A relation R is of pairs.
    A pair (x, y) is said to be R-related if
    (x, y) is contained in R, also denoted x R y.

    Relation objects can be created by specifying an
    iterable of pairs.
    The Relation object then enables the easy computation
    of some properties of the relation, such as closures.
    """

    def __init__(self, pairs: typing.Iterable[tuple[U, V]]):
        self.__rel = frozenset(pairs)

    @property
    def pairs(self) -> frozenset[tuple[U, V]]:
        """Obtain the relation represented as a set of pairs.

        Note that Relation(self.pairs) == self
        """
        return self.__rel

    def __contains__(self, item: tuple[U, V]) -> bool:
        return item in self.__rel

    @functools.cached_property
    def left(self) -> frozenset[U]:
        """A relation is a subset of U x V.

        This function computes all instances u of U
        contained in this relation.
        """
        return frozenset(x for x, _ in self.__rel)

    @functools.cached_property
    def right(self) -> frozenset[V]:
        """A relation is a subset of U x V.

        This function computes all instances v of V
        contained in this relation.
        """
        return frozenset(y for _, y in self.__rel)

    @functools.cache
    def reflexive_closure(self) -> Relation[U | V, U | V]:
        """Compute the reflexive closure of the relation.

        The reflexive closure is a new relation containing
        (x, x) for every x in the union of U and V.
        """
        return Relation(
            self.__rel | {
                (x, x) for x in self.left
            } | {
                (y, y) for y in self.right
            }
        )

    @functools.cache
    def symmetric_closure(self) -> Relation[U | V, U | V]:
        """Compute the symmetric closure of the relation.
        """
        return Relation(
            self.__rel | {(y, x) for x, y in self.__rel}
        )

    @functools.cache
    def transitive_closure(self) -> Relation[U, V]:
        """Compute the transitive closure of the relation.
        """
        rel = set(self.pairs)
        for k in self.left | self.right:
            next_relation = rel.copy()
            for i in self.left | self.right:
                for j in self.left | self.right:
                    if (i, j) in rel:
                        continue
                    if (i, k) in rel and (k, j) in rel:
                        next_relation.add((i, j))
            rel = next_relation
        return Relation(frozenset(rel))

    def as_dict(self) -> dict[U, list[V]]:
        """Convert the relation to a dict representation.

        For every (x, y) in the relation, x becomes a key
        in the dictionary. The corresponding value is a list
        of y_1, ..., y_n, where x is R-related to all the y_i.
        """
        result = {}
        for x, y in self.__rel:
            result.setdefault(x, []).append(y)
        return result
