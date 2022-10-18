import contextlib
import importlib
import inspect
import io
import os
import pprint
import time
import typing
import unittest


from pygll.generator import generate_parser
from pygll.generator.parser_generator import generate_parser as _gen_abstract_parser
from pygll.core.base import ParsingError, AbstractParser
from pygll.core.interpreter import build_dynamic_parser


class ParserTestCase(unittest.TestCase):
    """Base class for all test cases testing the parser.

    This class provides basic functionality for generating parser
    and generating elaborate error reports on test failure.

    In particular, this class generates a file for every failed test,
    containing the generated parser.
    """

    def setUp(self) -> None:
        self.__abstract_parser = None

    def build_parser(self, grammar, tags):
        self.__abstract_parser = _gen_abstract_parser('TestParser', grammar, tags)
        return build_dynamic_parser(
            self.__abstract_parser
        )

    def tearDown(self):
        self.__abstract_parser = None

    def assert_parsing_failure(self,
                               parser: typing.Type[AbstractParser],
                               parser_input: str,
                               description: str = ''):
        p = parser()
        try:
            p.parse(parser_input)
        except ParsingError:
            pass
        else:
            self.make_report(parser,
                             parser_input,
                             'Expected parsing failure',
                             description)
            self.fail(f'Expected parsing failure ({description})')

    def assert_parsing_success(self,
                               parser: typing.Type[AbstractParser],
                               parser_input: str,
                               description: str = ''):
        p = parser()
        try:
            p.parse(parser_input)
        except ParsingError:
            self.make_report(parser,
                             parser_input,
                             'Expected parsing success',
                             description)
            self.fail(f'Expected parsing success ({description})')

    def make_report(self,
                    parser: typing.Type[AbstractParser],
                    parser_input: str,
                    base_message: str,
                    description: str):
        current_frame = inspect.currentframe()
        caller_frame = inspect.getouterframes(current_frame, 2)
        caller = caller_frame[2].function.replace('<', '').replace('>', '')
        #source = inspect.getsource(parser)
        filename = f'{self.__class__.__name__}.{caller}'.replace('.', '_') + '.txt'
        with open(filename, 'w') as file:
            file.write(f'TEST FAILURE: {self.__class__.__name__}.{caller}\n')
            file.write(base_message + '\n')
            file.write(description + '\n')
            file.write(f'Parsing input: {parser_input!r}\n')
            file.write('='*80 + '\n')
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                p = parser(debug=True)
                result = p.parse(parser_input)
            file.write(f'Key: [{result.get_final_slot()}, True, 0, {len(parser_input)}]\n')
            file.write('\n')
            file.write('Created:\n')
            for key in result.created:
                file.write(repr(key) + '\n')
            file.write('='*80 + '\n')
            file.write('Parser Debug Output:\n\n')
            file.write(buffer.getvalue() + '\n')
            file.write('='*80 + '\n')
            pprint.pprint(self.__abstract_parser, stream=file)
            #file.write(source)
