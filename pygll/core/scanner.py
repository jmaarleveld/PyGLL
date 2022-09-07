import collections
import enum


class ScannerEvent(enum.Enum):
    HasNext = enum.auto()
    GetNext = enum.auto()


class Scanner:

    def __init__(self, source: str):
        self.__source = source
        self.__pos = 0
        self.__callbacks = collections.defaultdict(list)

    def register_callback(self, event: ScannerEvent, callback):
        assert callable(callback)
        self.__callbacks[event].append(callback)

    def __invoke_callbacks(self, event: ScannerEvent, args):
        for cb in self.__callbacks[event]:
            cb(*args)

    @property
    def position(self) -> int:
        return self.__pos

    @position.setter
    def position(self, value: int):
        self.__pos = value

    def has_next(self, pattern: str) -> bool:
        stop = self.__pos + len(pattern)
        result = self.__source.find(pattern, self.__pos, stop) != -1
        self.__invoke_callbacks(ScannerEvent.HasNext, (pattern, result))
        return result

    def peek(self, length: int) -> str:
        return self.__source[self.__pos:self.__pos + length]

    def reached_eoi(self) -> bool:
        return self.__pos >= len(self.__source)

    def get_next(self, pattern: str) -> str | None:
        if self.has_next(pattern):
            self.__pos += len(pattern)
            self.__invoke_callbacks(ScannerEvent.GetNext, (pattern, True))
            return pattern
        else:
            self.__invoke_callbacks(ScannerEvent.GetNext, (pattern, False))

