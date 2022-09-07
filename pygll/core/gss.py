##############################################################################
##############################################################################
# Imports
##############################################################################

import typing

T = typing.TypeVar('T', bound=typing.Hashable)
V = typing.TypeVar('V')

##############################################################################
##############################################################################
# GSS class
##############################################################################


class GSS(typing.Generic[T, V]):

    def __init__(self):
        self.__edge_labels: dict[tuple[T, T], V] = {}
        self.__edges: dict[T, set[T]] = {}

    def __contains__(self, item: T) -> bool:
        return item in self.__edges

    def add_node(self, node: T):
        self.__edges[node] = set()

    def add_edge(self, from_: T, to: T, label: V):
        self.__edge_labels[(from_, to)] = label
        self.__edges[from_].add(to)

    def get_children(self, node: T):
        yield from self.__edges[node]

    def get_label(self, edge: tuple[T, T]) -> V:
        return self.__edge_labels[edge]

    def get_edges(self, node: T) -> typing.Iterator[tuple[T, V]]:
        for target in self.__edges[node]:
            yield target, self.get_label((node, target))
