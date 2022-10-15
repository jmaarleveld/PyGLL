##############################################################################
##############################################################################
# Imports
##############################################################################

from .py_grammar_builder import *

##############################################################################
##############################################################################
# Pre-defined character classes
##############################################################################


_escapable_chars = chars([' ', ' '], ['"', '"'], ["'", "'"], ['-', '-'], ['<', '<'],
                         ['>', '>'], ['[', '['], [']', ']'], ['\\', '\\'], ['b', 'b'],
                         ['f', 'f'], ['n', 'n'], ['r', 'r'], ['t', 't'])
_hex_digits = chars(['0', '9'], ['a', 'f'], ['A', 'F'])
_ident_chars = chars(['A', 'Z'], ['a', 'z'], ['0', '9'], ['_', '_'])
_ident_start_chars = chars(['A', 'Z'], ['a', 'z'], ['_', '_'])


##############################################################################
##############################################################################
# Rascal Grammar -- Layout and keywords
##############################################################################


comment = lexical('Comment')
comment |= lit('/*') + (~chars(['*', '*']) | not_followed_by('*', '/'))[:] + lit('*/')
comment |= lit('//') + ~chars(['\n', '\n'])

layout = layout('LAYOUT', comment.ref)
layout |= chars(['\t', '\r'], [' ', ' '], ['\x85', '\x85'], ['\xa0', '\xa0'],
                ['\u1680', '\u1680'], ['\u180e', '\u180e'], ['\u2000', '\u200a'],
                ['\u2028', '\u2029'], ['\u202f', '\u202f'], ['\u205f', '\u205f'],
                ['\u3000', '\u3000'])

syntax_keywords = keywords('SyntaxKeywords',
                           'syntax', 'start', 'layout', 'lexical',
                           'assoc', 'non-assoc', 'left', 'right')

unicode_escape = syntax('UnicodeEscape',
                        utf16='\\u' + _hex_digits[4],
                        utf32='\\U' + ('10' | ('0' + _hex_digits)) + _hex_digits[4],
                        ascii='\\a' + chars(['0', '7']) + _hex_digits
                        )

##############################################################################
##############################################################################
# Rascal Grammar -- Strings, characters, and literals
##############################################################################

char = lexical('Char',
               lit('\\') + _escapable_chars,
               _escapable_chars,
               unicode_escape.ref)
char_range = syntax('Range',
                    fromto=char.ref @ 'start' + '-' + char.ref @ 'stop',
                    character=char.ref @ 'character')
char_class = syntax('Class')
char_class |= named('simpleCharClass', '[' + char_range.ref[:] @ 'ranges' + ']')

octal_literal = lexical(
    'OctalIntegerLiteral',
    not_followed_by('0' + (lit('o') | lit('O')) + chars(['0', '7'])[1:], _ident_chars)
)
hex_literal = lexical(
    'HexIntegerLiteral',
    not_followed_by('0' + (lit('x') | lit('X')) + _hex_digits[1:], _ident_chars)
)
decimal_literal = lexical(
    'DecimalIntegerLiteral',
    not_followed_by(chars(['1', '9']) + chars(['0', '9'][:]), _ident_chars),
    not_followed_by('0', _ident_chars)
)
integer_literal = syntax(
    'IntegerLiteral',
    decimalIntegerLiteral=decimal_literal.ref @ 'decimal',
    hexIntegerLiteral=hex_literal.ref @ 'hex',
    octalIntegerLiteral=octal_literal.ref @ 'octal'
)

string_character = lexical(
    'StringCharacter',
    unicode_escape.ref,
    ~chars(['"', '"'], ["'", "'"], ['>', '>'], ['<', '<'], ['\\', '\\']),
    '\\' + _escapable_chars
)

case_insensitive_string_constant = lexical(
    'CaseInsensitiveStringConstant',
    "'" + string_character.ref[:] @ 'chars' + "'"
)

string_constant = lexical(
    'StringConstant',
    '"' + string_character[:] @ 'chars' + "'"
)

##############################################################################
##############################################################################
# Rascal Grammar -- Names
##############################################################################

name = lexical(
    'Name',
    not_precede(
        _ident_chars,
        not_followed_by(_ident_start_chars + _ident_chars[:], _ident_chars)
    )
)

nonterminal_label = lexical(
    'NonterminalLabel',
    not_followed_by(chars(['a', 'z']) + _ident_chars[:], _ident_chars)
)


nonterminal = lexical(
    'Nonterminal',
    not_followed_by(
        not_precede(
            chars(['A', 'Z']),
            chars(['A', 'Z']) + _ident_chars
        ),
        syntax_keywords.ref
    )
)

##############################################################################
##############################################################################
# Rascal Grammar -- Production Modifiers
##############################################################################

assoc = syntax('Assoc',
               associative='assoc',
               left='left',
               nonAssociative='non-assoc',
               right='right')

tag_string = lexical('TagString')
tag_string |= (
    not_precede('\\', '{') +
    (
            ~chars(['{', '{'], ['}', '}']) |
            '\\' + chars(['{', '{'], ['}', '}']) |
            tag_string.ref
    )[:] @ 'contents' +
    not_precede('\\', '}')
)

tag = syntax(
    'Tag',
    default='@' + nonterminal.ref @ 'name' + tag_string.ref
)

prod_modifier = syntax(
    'ProdModifier',
    associativity=assoc.ref @ 'associativity',
    bracket='bracket',
    tag=tag.ref @ 'tag'
)

##############################################################################
##############################################################################
# Rascal Grammar -- Symbol
##############################################################################

##############################################################################
##############################################################################
# Rascal Grammar -- Production
##############################################################################






