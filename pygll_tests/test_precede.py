import contextlib
import importlib
import os
import unittest

try:
    from pygll_tests.util.parser_test import ParserTestCase
except ImportError:
    from .util.parser_test import ParserTestCase


from pygll.generator.context_free_grammar import ContextFreeGrammar, Nonterminal, Terminal


class TestNotPrecede(ParserTestCase):

    ###################################################################
    ###################################################################
    # Grammar 1
    ###################################################################

    @staticmethod
    def get_grammar_1():
        grammar = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('a'), Nonterminal('S')),
                    (Terminal.literal('b'),),
                    (Terminal.empty(),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 1, 0): [
                ('not_precede', [Terminal.literal('a')])
            ]
        }
        return grammar, tags

    def test__not_precede_literal__no_interference_with_normal(self):
        grammar, tags = self.get_grammar_1()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_success(parser, 'aaa')
        self.assert_parsing_success(parser, 'b')
        self.assert_parsing_success(parser, '')
        self.assert_parsing_success(parser, 'a')

    def test__not_precede_literal__failure_case_1(self):
        grammar, tags = self.get_grammar_1()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'ab')

    def test__not_precede_literal__failure_case_2(self):
        grammar, tags = self.get_grammar_1()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'aaaab')

    ###################################################################
    ###################################################################
    # Grammar 2
    ###################################################################

    @staticmethod
    def get_grammar_2():
        grammar = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('a'), Nonterminal('S')),
                    (Nonterminal('B'),),
                    (Terminal.empty(),),
                ),
                Nonterminal('B'): (
                    (Terminal.literal('b'),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 1, 0): [
                ('not_precede', [Terminal.literal('a')])
            ]
        }
        return grammar, tags

    def test__not_precede_nonterminal__no_interference_with_normal(self):
        grammar, tags = self.get_grammar_2()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_success(parser, 'aaa')
        self.assert_parsing_success(parser, 'b')
        self.assert_parsing_success(parser, '')
        self.assert_parsing_success(parser, 'a')

    def test__not_precede_nonterminal__failure_case_1(self):
        grammar, tags = self.get_grammar_2()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'ab')

    def test__not_precede_nonterminal__failure_case_2(self):
        grammar, tags = self.get_grammar_2()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'aaaab')

    ###################################################################
    ###################################################################
    # Grammar 3
    ###################################################################

    @staticmethod
    def get_grammar_3():
        grammar = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('a'), Nonterminal('S')),
                    (Terminal.literal('c'), Nonterminal('S')),
                    (Terminal.literal('b'),),
                    (Terminal.empty(),),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 2, 0): [
                ('not_precede', [Terminal.literal('a'), Terminal.literal('c')])
            ]
        }
        return grammar, tags

    def test__not_precede_multiple__no_interference_with_normal(self):
        grammar, tags = self.get_grammar_3()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_success(parser, 'aaa')
        self.assert_parsing_success(parser, 'b')
        self.assert_parsing_success(parser, '')
        self.assert_parsing_success(parser, 'a')
        self.assert_parsing_success(parser, 'c')
        self.assert_parsing_success(parser, 'ccc')

    def test__not_precede_multiple__failure_case_1(self):
        grammar, tags = self.get_grammar_3()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'cb')

    def test__not_precede_multiple__failure_case_2(self):
        grammar, tags = self.get_grammar_3()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'ab')

    def test__not_precede_multiple__failure_case_3(self):
        grammar, tags = self.get_grammar_3()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'cccb')

    def test__not_precede_multiple__failure_case_4(self):
        grammar, tags = self.get_grammar_3()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'aaaaab')

    ###################################################################
    ###################################################################
    # Grammar 4
    ###################################################################

    @staticmethod
    def get_grammar_4():
        grammar = ContextFreeGrammar(
            start=Nonterminal('S'),
            rules={
                Nonterminal('S'): (
                    (Terminal.literal('a'), Terminal.literal('b')),
                )
            }
        )
        tags = {
            (Nonterminal('S'), 0, 1): [
                ('not_precede', [Terminal.literal('a')])
            ]
        }
        return grammar, tags

    def test__not_precede_literal_with_literal(self):
        grammar, tags = self.get_grammar_4()
        parser = self.build_parser(grammar, tags)
        self.assert_parsing_failure(parser, 'ab')

