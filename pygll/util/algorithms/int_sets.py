##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import functools
import typing


##############################################################################
##############################################################################
# IntSet class
##############################################################################


class IntSet:

    def __init__(self,
                 content: typing.Iterable[tuple[int, int]],
                 universe: tuple[int, int]):
        self.__universe = universe
        # Normalize the input ranges
        self.__content = sorted(self.__union(list(content)))

    @classmethod
    def empty_set(cls, universe: tuple[int, int]) -> typing.Self:
        return cls((), universe)

    @property
    def ranges(self) -> tuple[tuple[int, int]]:
        return tuple(self.__content)

    @property
    def universe(self) -> tuple[int, int]:
        return self.__universe

    @property
    def empty(self) -> bool:
        return not bool(self.__content)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}({self.__content}, {self.__universe})'
        )

    def __and__(self, other):
        if not isinstance(other, IntSet):
            return NotImplemented
        if self.empty:
            return self
        # Compute the intersection of two IntSets.
        # The algorithm makes use of two facts:
        #   - An IntSet is a union of disjoint ranges (sets)
        #   - intersection is distributive over union
        # What this means is that we can compute the intersection
        # of every range in self with every range in other,
        # and then take the union.
        intersections = []
        for self_start, self_stop in self.ranges:
            for other_start, other_stop in other.ranges:
                if self_start > other_stop or other_start > self_stop:
                    # disjoint
                    continue
                start = max(self_start, other_start)
                stop = min(self_stop, other_stop)
                intersections.append((start, stop))
        return IntSet(self.__union(intersections), self.__universe)

    def __or__(self, other):
        if not isinstance(other, IntSet):
            return NotImplemented
        if self.empty:
            return other
        return IntSet(
            self.__union(self.__content + list(other.ranges)),
            self.__universe
        )

    @staticmethod
    def __union(ranges: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
        # Simplify a collection of ranges, such that all
        # duplicate ranges are removed, and overlapping and
        # adjacent ranges are merged.
        n = len(ranges)
        not_changed = 0
        while len(ranges) > 1:
            new_ranges = []
            start, stop = ranges[0]
            changed = False
            for other_start, other_stop in ranges[1:]:
                are_disjoint = stop < other_start or start > other_stop
                are_adjacent = (stop + 1 == other_start or
                                other_stop + 1 == start)
                if are_disjoint and not are_adjacent:
                    # Disjoint
                    new_ranges.append((other_start, other_stop))
                else:
                    # Merge ranges
                    start = min(start, other_start)
                    stop = max(stop, other_stop)
                    changed = True
            new_ranges.append((start, stop))
            ranges = new_ranges
            if changed:
                not_changed = 0
            else:
                not_changed += 1
            if not_changed >= n:
                break
        return tuple(ranges)

    def __invert__(self):
        # Compute the complement of an IntSet.
        # The complement is computed using
        # DeMorgan:
        # complement(union(x_1, x_2, ..., x_n)) =
        # intersection(complement(x_1), ..., complement(x_n))
        individual_sets = [
            self.__complement(start, stop)
            for start, stop in self.__content
        ]
        return functools.reduce(
            lambda x, y: x & y,
            individual_sets,
            IntSet((self.__universe,), self.__universe)
        )

    def __complement(self, start: int, stop: int) -> IntSet:
        # Compute the complement of a single range, w.r.t.
        # the universe of the set
        if (start, stop) == self.__universe:
            return IntSet((), self.__universe)
        elif self.empty:
            return IntSet((self.__universe,), self.__universe)
        elif start == self.__universe[0]:
            return IntSet(
                ((stop+1, self.__universe[1]),),
                self.__universe
            )
        elif stop == self.__universe[1]:
            return IntSet(
                ((self.__universe[0], start-1),),
                self.__universe
            )
        return IntSet(
            (
                (self.__universe[0], start-1),
                (stop+1, self.__universe[1])
            ),
            self.__universe
        )

    def __sub__(self, other):
        if not isinstance(other, IntSet):
            return NotImplemented
        return self & ~other

    def __eq__(self, other):
        if not isinstance(other, IntSet):
            return False
        return (self.__universe == other.universe and
                self.ranges == other.ranges)

    def __lt__(self, other):
        if not isinstance(other, IntSet):
            return NotImplemented
        if self.__universe != other.universe:
            raise ValueError(
                'Cannot compare IntSets with different universes.'
            )
        raise NotImplementedError


if __name__ == '__main__':
    p = IntSet(((0, 1), (4, 4), (8, 14)), (0, 20))
    q = IntSet(((2, 6), (12, 17), (20, 20)), (0, 20))
    u = IntSet(((0, 20),), (0, 20))
    e = IntSet((), (0, 20))
    assert p == p
    assert p != q
    assert p & u == p, p & u
    assert p | u == u, p | u
    assert (~u).empty
    assert not p.empty
    assert not q.empty
    assert not u.empty
    assert not (~p).empty
    assert p | q == IntSet(((0, 6), (8, 17), (20, 20)), (0, 20)), p | q
    assert p | q == q | p
    assert p & q == IntSet(((4, 4), (12, 14)), (0, 20)), p & q
    assert (~~p) == p
    assert (~~u) == u
    assert e | p == p
    assert e | q == q
    assert e | u == u
    assert e | e == e
    assert e & p == e
    assert e & q == e
    assert e & u == e
    assert e & e == e
    assert (~e) == IntSet(((0, 20),), (0, 20))
    assert (~~e) == e
    assert e.empty
    assert e == IntSet.empty_set((0, 20))
