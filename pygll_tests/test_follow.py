try:
    from pygll_tests.util.parser_test import ParserTestCase
except ImportError:
    from .util.parser_test import ParserTestCase


from pygll.generator.context_free_grammar import (ContextFreeGrammar,
                                                  Nonterminal,
                                                  Terminal)


class FollowCheck(ParserTestCase):

    @staticmethod
    def get_grammar_1():
        g = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('a'), Nonterminal('S')),
                    (Terminal.literal('b'),),
                    (Terminal.literal('c'),)
                )
            }
        )
        tags = {
            (Nonterminal('S'), 0, 1): [
                ('not_follow', [Terminal.literal('b')])
            ]
        }
        return g, tags

    def test_simple_not_follow_success(self):
        parser = self.build_parser(*self.get_grammar_1())
        self.assert_parsing_success(parser, 'c')
        self.assert_parsing_success(parser, 'ac')
        self.assert_parsing_success(parser, 'aac')
        self.assert_parsing_success(parser, 'b')

    def test_simple_not_follow_failure(self):
        parser = self.build_parser(*self.get_grammar_1())
        self.assert_parsing_failure(parser, 'ab')
        self.assert_parsing_failure(parser, 'aab')
        self.assert_parsing_failure(parser, 'aaab')

