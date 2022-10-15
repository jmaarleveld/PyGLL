from .generator import Language, generate_parser
from .generator.parser_generator import generate_parser as _generate_abstract_parser
from .core.interpreter import DynamicParser
from .core.interpreter import build_dynamic_parser as _build_dynamic_parser
from .generator import context_free_grammar as _cfg


def generate_dynamic_parser(grammar: _cfg.ContextFreeGrammar,
                            *, tags: dict = None) -> DynamicParser:
    parser_definition = _generate_abstract_parser('Parser', grammar, tags)
    return _build_dynamic_parser(parser_definition)

