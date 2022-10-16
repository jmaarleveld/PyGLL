try:
    from pygll_tests.util.parser_test import ParserTestCase
except ImportError:
    from .util.parser_test import ParserTestCase


from pygll.generator.context_free_grammar import (ContextFreeGrammar,
                                                  Nonterminal,
                                                  Terminal)


class FollowCheck(ParserTestCase):

    ###################################################################
    ###################################################################
    # Grammar 1
    ###################################################################

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
            (Nonterminal('S'), 0, 0): [
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

    ###################################################################
    ###################################################################
    # Grammar 2
    ###################################################################

    @staticmethod
    def get_grammar_2():
        g = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('a'), Nonterminal('S')),
                    (Nonterminal('B'),),
                    (Nonterminal('C'),)
                ),
                Nonterminal('B'): (
                    (Terminal.literal('b'),),
                ),
                Nonterminal('C'): (
                    (Terminal.literal('c'),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 0, 0): [
                ('not_follow', [Terminal.literal('b')])
            ]
        }
        return g, tags

    def test_indirect_terminal_not_follow_success(self):
        parser = self.build_parser(*self.get_grammar_2())
        self.assert_parsing_success(parser, 'c')
        self.assert_parsing_success(parser, 'ac')
        self.assert_parsing_success(parser, 'aac')
        self.assert_parsing_success(parser, 'b')

    def test_indirect_terminal_not_follow_failure(self):
        parser = self.build_parser(*self.get_grammar_2())
        self.assert_parsing_failure(parser, 'ab')
        self.assert_parsing_failure(parser, 'aab')
        self.assert_parsing_failure(parser, 'aaab')

    ###################################################################
    ###################################################################
    # Grammar 5
    ###################################################################

    @staticmethod
    def get_grammar_3():
        g = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Nonterminal('A'), Nonterminal('S')),
                    (Terminal.literal('b'),),
                    (Terminal.literal('c'),)
                ),
                Nonterminal('A'): (
                    (Terminal.literal('a'),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 0, 0): [
                ('not_follow', [Terminal.literal('b')])
            ]
        }
        return g, tags

    def test_nonterminal_not_follow_success(self):
        parser = self.build_parser(*self.get_grammar_4())
        self.assert_parsing_success(parser, 'c')
        self.assert_parsing_success(parser, 'ac')
        self.assert_parsing_success(parser, 'aac')
        self.assert_parsing_success(parser, 'b')

    def test_nonterminal_not_follow_failure(self):
        parser = self.build_parser(*self.get_grammar_4())
        self.assert_parsing_failure(parser, 'ab')
        self.assert_parsing_failure(parser, 'aab')
        self.assert_parsing_failure(parser, 'aaab')

    ###################################################################
    ###################################################################
    # Grammar 4
    ###################################################################

    @staticmethod
    def get_grammar_4():
        g = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Nonterminal('A'), Nonterminal('S')),
                    (Nonterminal('B'),),
                    (Nonterminal('C'),)
                ),
                Nonterminal('A'): (
                    (Terminal.literal('a'),),
                ),
                Nonterminal('B'): (
                    (Terminal.literal('b'),),
                ),
                Nonterminal('C'): (
                    (Terminal.literal('c'),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 0, 0): [
                ('not_follow', [Terminal.literal('b')])
            ]
        }
        return g, tags

    def test_nonterminal_indirect_not_follow_success(self):
        parser = self.build_parser(*self.get_grammar_4())
        self.assert_parsing_success(parser, 'c')
        self.assert_parsing_success(parser, 'ac')
        self.assert_parsing_success(parser, 'aac')
        self.assert_parsing_success(parser, 'b')

    def test_nonterminal_indirect_not_follow_failure(self):
        parser = self.build_parser(*self.get_grammar_4())
        self.assert_parsing_failure(parser, 'ab')
        self.assert_parsing_failure(parser, 'aab')
        self.assert_parsing_failure(parser, 'aaab')

    ###################################################################
    ###################################################################
    # Grammar 5
    ###################################################################

    @staticmethod
    def get_grammar_5():
        g = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('a'), Nonterminal('P'), Nonterminal('T'), Nonterminal('S')),
                    (Terminal.literal('e'), Nonterminal('T'), Terminal.literal('c')),
                ),
                Nonterminal('T'): (
                    (Terminal.literal('b'), Nonterminal('T')),
                    (Terminal.literal('d'),)
                ),
                Nonterminal('P'): (
                    (Terminal.empty(),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 0, 1): [
                ('not_follow', [Terminal.literal('b')])
            ]
        }
        return g, tags

    def test_not_follow_advanced_success(self):
        parser = self.build_parser(*self.get_grammar_5())
        self.assert_parsing_success(parser, 'adedc')
        self.assert_parsing_success(parser, 'adedc')
        self.assert_parsing_success(parser, 'adebdc')
        self.assert_parsing_success(parser, 'adebbbbdc')

    def test_not_follow_advanced_succes_without_tags(self):
        parser = self.build_parser(self.get_grammar_5()[0], {})
        self.assert_parsing_success(parser, 'abdedc')
        self.assert_parsing_success(parser, 'abdebdc')

    def test_not_follow_advanced_failure(self):
        parser = self.build_parser(*self.get_grammar_5())
        self.assert_parsing_failure(parser, 'abdedc')
        self.assert_parsing_failure(parser, 'abdebdc')
