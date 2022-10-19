try:
    from pygll_tests.util.parser_test import ParserTestCase
except ImportError:
    from .util.parser_test import ParserTestCase


from pygll.generator.context_free_grammar import (ContextFreeGrammar,
                                                  Nonterminal,
                                                  Terminal)


class RestrictionCheck(ParserTestCase):

    @staticmethod
    def get_grammar_1():
        g = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('x'), Nonterminal('T'), Terminal.literal('y')),
                ),
                Nonterminal('T'): (
                    (Terminal.literal('a'),),
                    (Terminal.literal('b'),),
                    (Terminal.literal('c'),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 0, 1): [
                ('restriction', [Terminal.literal('a'), Terminal.literal('b')])
            ]
        }
        return g, tags

    def test_restriction_success(self):
        parser = self.build_parser(*self.get_grammar_1())
        self.assert_parsing_success(parser, 'xcy')

    def test_restriction_failure(self):
        parser = self.build_parser(*self.get_grammar_1())
        self.assert_parsing_failure(parser, 'xay')
        self.assert_parsing_failure(parser, 'xby')

    @staticmethod
    def get_grammar_2():
        g = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('x'), Nonterminal('T'), Terminal.literal('y')),
                ),
                Nonterminal('T'): (
                    (Terminal.literal('aaa'),),
                    (Terminal.literal('bbb'),),
                    (Terminal.literal('ccc'),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 0, 1): [
                ('restriction', [Terminal.literal('aaa'), Terminal.literal('bbb')])
            ]
        }
        return g, tags

    def test_restriction_sequence_success(self):
        parser = self.build_parser(*self.get_grammar_2())
        self.assert_parsing_success(parser, 'xcccy')

    def test_restriction_sequence_failure(self):
        parser = self.build_parser(*self.get_grammar_2())
        self.assert_parsing_failure(parser, 'xaaay')
        self.assert_parsing_failure(parser, 'xbbby')