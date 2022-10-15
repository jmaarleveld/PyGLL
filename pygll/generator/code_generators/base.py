##############################################################################
##############################################################################
# Imports
##############################################################################

import abc
import io

from ..abstract_parser import ParserDefinition
from .. import abstract_parser as _ast

from . import util as _util

##############################################################################
##############################################################################
# Abstract Base Class
##############################################################################


class AbstractCodeGenerator(abc.ABC):

    def __init__(self, file: str | io.TextIOBase):
        self.__writer = _util.CodeWriter(file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__writer.close()

    def close(self):
        self.__writer.close()

    def closed(self):
        return self.writer.closed

    @property
    def writer(self) -> _util.CodeWriter:
        return self.__writer

    @abc.abstractmethod
    def generate_code(self, parser: ParserDefinition):
        pass

