import enum
import io

from .context_free_grammar import ContextFreeGrammar

from . import code_generators as _code
from . import parser_generator as _parser_generator


class Language(enum.Enum):
    Python = enum.auto()


def generate_parser(grammar: ContextFreeGrammar,
                    parser_name: str,
                    file: str | io.TextIOBase,
                    language: Language = Language.Python,
                    *,
                    tags: dict = None):
    if tags is None:
        tags = {}
    abstract_parser = _parser_generator.generate_parser(parser_name,
                                                        grammar,
                                                        tags)
    match language:
        case Language.Python:
            code_generator = _code.PythonCodeGenerator(file)
        case _:
            raise ValueError(f'Invalid language: {language}')
    code_generator.generate_code(abstract_parser)
