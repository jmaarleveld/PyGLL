import collections
import enum


class ScannerEvent(enum.Enum):
    HasNext = enum.auto()
    GetNext = enum.auto()


class Scanner:

    def __init__(self, source: str):
        self.__source = source
        self.__pos = 0

    @property
    def position(self) -> int:
        return self.__pos

    @position.setter
    def position(self, value: int):
        self.__pos = value

    def has_next(self, pattern: str) -> bool:
        stop = self.__pos + len(pattern)
        result = self.__source.find(pattern, self.__pos, stop) != -1
        return result

    def peek(self, length: int) -> str:
        return self.__source[self.__pos:self.__pos + length]

    def peek_forward(self, length: int) -> str:
        #return self.__source[self.__pos + 1:self.__pos + length + 1]
        return self.peek(length)

    def peek_backward(self, length: int) -> str:
        return self.__source[self.__pos - length:self.__pos]

    def get_slice(self, start: int, stop: int) -> str:
        return self.__source[start:stop]

    def reached_eoi(self) -> bool:
        return self.__pos >= len(self.__source)

    def advance(self, by: int):
        self.__pos += by

