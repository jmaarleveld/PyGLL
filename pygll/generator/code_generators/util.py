import contextlib
import io


class CodeWriter:

    def __init__(self, file: str | io.TextIOBase):
        if isinstance(file, str):
            file = open(file, 'w')
        self.__file = file
        self.__indent = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        pass

    @property
    def closed(self):
        return self.__file.closed

    @contextlib.contextmanager
    def increased_indent(self):
        self.__indent += 1
        yield self
        self.__indent -= 1

    def write_line(self, line: str):
        self.__file.write('    '*self.__indent + line + '\n')

    def write_empty_line(self):
        self.__file.write('\n')
