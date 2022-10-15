from .grammar_definitions import *


syntax_definitions = Syntax(
    name='SyntaxDefinitions',
    production=LabeledRule(
        (),
        StarRepeat(Nonterminal('SyntaxDefinition')),
        'definitions'
    )
)

syntax_definition = Syntax(
    name='SyntaxDefinition',
    production=Choice(
        (
            (
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('layout'),
                            LabeledSymbol('defined', Nonterminal('Sym')),
                            Literal('='),
                            LabeledSymbol('production', Nonterminal('Prod')),
                            Literal(';')
                        )
                    ),
                    'layout'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('lexical'),
                            LabeledSymbol('defined', Nonterminal('Sym')),
                            Literal('='),
                            LabeledSymbol('production', Nonterminal('Prod')),
                            Literal(';')
                        )
                    ),
                    'lexical'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('keyword'),
                            LabeledSymbol('defined', Nonterminal('Sym')),
                            Literal('='),
                            LabeledSymbol('production', Nonterminal('Prod')),
                            Literal(';')
                        )
                    ),
                    'keyword'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('start', Nonterminal('Start')),
                            Literal('syntax'),
                            LabeledSymbol('defined', Nonterminal('Sym')),
                            Literal('='),
                            LabeledSymbol('production', Nonterminal('Prod')),
                            Literal(';')
                        )
                    ),
                    'syntax'
                ),
            ),
        )
    )
)

start = Syntax(
    name='Start',
    production=Choice(
        (   # outer tuple
            (   # inner tuple
                LabeledRule((), Empty(), 'absent'),
                LabeledRule((), Literal('start'), 'present')
            ),
        )
    )
)

octal_literal = Lexical(
    name='OctalIntegerLiteral',
    production=UnlabeledRule(
        (),
        NotFollow(
            Sequence(
                (
                    Literal('0'),
                    CharacterRange((
                        (ord('o'), ord('o')),
                        (ord('O'), ord('O'))
                    )),
                    PlusRepeat(
                        CharacterRange(((ord('0'), ord('7')),)),
                    ),
                )
            ),
            CharacterRange((
                (ord('0'), ord('9')),
                (ord('a'), ord('z')),
                (ord('A'), ord('Z')),
                (ord('_'), ord('_'))
            ))
        )
    )
)

hex_literal = Lexical(
    name='HexIntegerLiteral',
    production=UnlabeledRule(
        (),
        NotFollow(
            Sequence(
                (
                   Literal('0'),
                    CharacterRange((
                        (ord('x'), ord('x')),
                        (ord('X'), ord('X'))
                    )),
                    PlusRepeat(
                        CharacterRange((
                            (ord('0'), ord('9')),
                            (ord('a'), ord('f')),
                            (ord('A'), ord('F')),
                        )),
                    ),
                )
            ),
            CharacterRange((
                (ord('0'), ord('9')),
                (ord('a'), ord('z')),
                (ord('A'), ord('Z')),
                (ord('_'), ord('_'))
            ))
        )
    )
)

decimal_literal = Lexical(
    name='DecimalIntegerLiteral',
    production=Choice(
        (
            (
                UnlabeledRule(
                    (),
                    NotFollow(
                        Sequence(
                            (
                                CharacterRange((
                                    (ord('1'), ord('9')),
                                )),
                                StarRepeat(
                                    CharacterRange(((ord('0'), ord('9')),)),
                                ),
                            )
                        ),
                        CharacterRange((
                            (ord('0'), ord('9')),
                            (ord('a'), ord('z')),
                            (ord('A'), ord('Z')),
                            (ord('_'), ord('_'))
                        ))
                    )
                ),
                UnlabeledRule(
                    (),
                    NotFollow(
                        Literal('0'),
                        CharacterRange((
                            (ord('0'), ord('9')),
                            (ord('a'), ord('z')),
                            (ord('A'), ord('Z')),
                            (ord('_'), ord('_'))
                        ))
                    )
                )
            ),
        ),
    )
)

integer_literal = Syntax(
    name='IntegerLiteral',
    production=Choice
    (
        (
            (
                LabeledRule(
                    (),
                    LabeledSymbol('decimal', Nonterminal('DecimalIntegerLiteral')),
                    'decimalIntegerLiteral'),
                LabeledRule(
                    (),
                    LabeledSymbol('hex', Nonterminal('HexIntegerLiteral')),
                    'hexIntegerLiteral'),
                LabeledRule(
                    (),
                    LabeledSymbol('octal', Nonterminal('OctalIntegerLiteral')),
                    'octalIntegerLiteral'),
            ),
        )
    )
)

assoc = Syntax(
    name='Assoc',
    production=Choice(
        (
            (
                LabeledRule((), Literal('assoc'), 'associative'),
                LabeledRule((), Literal('left'), 'left'),
                LabeledRule((), Literal('non-assoc'), 'nonAssociative'),
                LabeledRule((), Literal('right'), 'right'),
            ),
        )
    )
)

unicode_escape = Syntax(
    name='UnicodeEscape',
    production=Choice(
        (
            (
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('\\u'),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            )),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            )),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            )),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            ))
                        )
                    ),
                    'utf16'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('\\U'),
                            Alternative(
                                (
                                    Literal('10'),
                                    Sequence(
                                        (
                                            Literal('0'),
                                            CharacterRange((
                                                (ord('0'), ord('9')),
                                                (ord('a'), ord('f')),
                                                (ord('A'), ord('F')),
                                            )),
                                        )
                                    )
                                )
                            ),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            )),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            )),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            )),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            ))
                        )
                    ),
                    'utf32'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('\\a'),
                            CharacterRange((
                                (ord('0'), ord('7')),
                            )),
                            CharacterRange((
                                (ord('0'), ord('9')),
                                (ord('a'), ord('f')),
                                (ord('A'), ord('F')),
                            ))
                        )
                    ),
                    'ascii'
                ),
            ),
        )
    )
)

name = Lexical(
    name='Name',
    production=UnlabeledRule(
        (),
        NotPrecede(
            symbol=NotFollow(
                symbol=Sequence(
                    (
                        CharacterRange(
                            (
                                (ord('a'), ord('z')),
                                (ord('A'), ord('Z')),
                                (ord('_'), ord('_')),
                            )
                        ),
                        StarRepeat(
                            CharacterRange(
                                (
                                    (ord('0'), ord('9')),
                                    (ord('a'), ord('z')),
                                    (ord('A'), ord('Z')),
                                    (ord('_'), ord('_')),
                                )
                            )
                        )
                    )
                ),
                constraint=CharacterRange(
                    (
                        (ord('0'), ord('9')),
                        (ord('a'), ord('z')),
                        (ord('A'), ord('Z')),
                        (ord('_'), ord('_')),
                    )
                )
            ),
            constraint=CharacterRange(
                (
                    (ord('0'), ord('9')),
                    (ord('a'), ord('z')),
                    (ord('A'), ord('Z')),
                    (ord('_'), ord('_')),
                )
            )
        )
    )
)

nonterminal_label = Lexical(
    name='NonterminalLabel',
    production=UnlabeledRule(
        (),
        NotFollow(
            symbol=Sequence(
                (
                    CharacterRange((
                        (ord('a'), ord('z')),
                    )),
                    CharacterRange((
                        (ord('0'), ord('9')),
                        (ord('a'), ord('z')),
                        (ord('A'), ord('Z')),
                        (ord('_'), ord('_')),
                    ))
                )
            ),
            constraint=CharacterRange((
                (ord('0'), ord('9')),
                (ord('a'), ord('z')),
                (ord('A'), ord('Z')),
                (ord('_'), ord('_')),
            ))
        )
    )
)

string_character = Lexical(
    name='StringCharacter',
    production=Choice(
        (
            (
                UnlabeledRule(
                    (),
                    Nonterminal('UnicodeEscape')
                ),
                UnlabeledRule(
                    (),
                    CharacterClassComplement(
                        CharacterRange((
                            (ord('"'), ord('"')),
                            (ord("'"), ord("'")),
                            (ord('<'), ord('>')),
                            (ord('>'), ord('>')),
                            (ord('\\'), ord('\\')),
                        ))
                    )
                ),
                UnlabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('\\'),
                            CharacterRange((
                                (ord('"'), ord('"')),
                                (ord("'"), ord("'")),
                                (ord('<'), ord('>')),
                                (ord('>'), ord('>')),
                                (ord('\\'), ord('\\')),
                                (ord('b'), ord('b')),
                                (ord('f'), ord('f')),
                                (ord('n'), ord('n')),
                                (ord('r'), ord('r')),
                                (ord('t'), ord('t')),
                            ))
                        )
                    )
                )
            ),
        )
    )
)

case_insensitive_string_constant = Lexical(
    name='CaseInsensitiveStringConstant',
    production=UnlabeledRule(
        (),
        Sequence(
            (
                Literal("'"),
                LabeledSymbol(
                    'chars',
                    StarRepeat(
                        Nonterminal('StringCharacter')
                    )
                ),
                Literal("'")
            )
        )
    )
)

string_constant = Lexical(
    name='StringConstant',
    production=UnlabeledRule(
        (),
        Sequence(
            (
                Literal('"'),
                LabeledSymbol(
                    'chars',
                    StarRepeat(
                        Nonterminal('StringCharacter')
                    )
                ),
                Literal('"')
            )
        )
    )
)

nonterminal = Lexical(
    name='Nonterminal',
    production=UnlabeledRule(
        (),
        Restriction(
            symbol=NotFollow(
                symbol=NotPrecede(
                    symbol=Sequence(
                        (
                            CharacterRange((
                                (ord('A'), ord('Z')),
                            )),
                            StarRepeat(
                                CharacterRange((
                                    (ord('A'), ord('Z')),
                                    (ord('a'), ord('z')),
                                    (ord('0'), ord('9')),
                                    (ord('_'), ord('_')),
                                )),
                            )
                        )
                    ),
                    constraint=CharacterRange((
                        (ord('A'), ord('Z')),
                    )),
                ),
                constraint=CharacterRange((
                    (ord('A'), ord('Z')),
                    (ord('a'), ord('z')),
                    (ord('0'), ord('9')),
                    (ord('_'), ord('_')),
                )),
            ),
            constraint=Nonterminal('SyntaxKeywords')
        )
    )
)

syntax_keywords = Keywords(
    name='SyntaxKeywords',
    production=Choice(
        (
            (
                UnlabeledRule((), Literal('syntax')),
                UnlabeledRule((), Literal('start')),
                UnlabeledRule((), Literal('layout')),
                UnlabeledRule((), Literal('lexical')),
                UnlabeledRule((), Literal('assoc')),
                UnlabeledRule((), Literal('non-assoc')),
                UnlabeledRule((), Literal('left')),
                UnlabeledRule((), Literal('right')),
            ),
        )
    )
)

tag = Syntax(
    name='Tag',
    production=Choice(
        (
            (
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('@'),
                            LabeledSymbol('name', Nonterminal('Name')),
                            LabeledSymbol('contents', Nonterminal('TagString'))
                        )
                    ),
                    'default'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('@'),
                            LabeledSymbol('name', Nonterminal('Name')),
                        )
                    ),
                    'empty'
                )
            ),
        )
    )
)

tag_string = Lexical(
    name='TagString',
    production=UnlabeledRule(
        (),
        Sequence(
            (
                NotPrecede(
                    symbol=Literal('{'),
                    constraint=Literal('\\')
                ),
                LabeledSymbol(
                    'contents',
                    StarRepeat(
                        Alternative(
                            (
                                CharacterClassComplement(
                                    CharacterRange((
                                        (ord('{'), ord('{')),
                                        (ord('}'), ord('}')),
                                    ))
                                ),
                                Sequence(
                                    (
                                        Literal('\\'),
                                        CharacterRange((
                                            (ord('{'), ord('{')),
                                            (ord('}'), ord('}')),
                                        ))
                                    )
                                ),
                                Nonterminal('TagString')
                            )
                        )
                    )
                ),
                NotPrecede(
                    symbol=Literal('}'),
                    constraint=Literal('\\')
                ),
            )
        )
    )
)

prod_modifier = Syntax(
    name='ProdModifier',
    production=Choice(
        (
            (
                LabeledRule(
                    (),
                    LabeledSymbol('associativity', Nonterminal('Assoc')),
                    'associativity'
                ),
                LabeledRule((), Literal('bracket'), 'bracket'),
                LabeledRule(
                    (),
                    LabeledSymbol('tag', Nonterminal('Tag')),
                    'tag'
                ),
            ),
        )
    )
)

prod = Syntax(
    name='Prod',
    production=Choice(
        (
            (
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal(':'),
                            LabeledSymbol('referenced', Nonterminal('Name'))
                        )
                    ),
                    'reference'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol(
                                'modifiers',
                                StarRepeat(
                                    Nonterminal('ProdModifier')
                                )
                            ),
                            LabeledSymbol('name', Nonterminal('Name')),
                            Literal(':'),
                            LabeledSymbol(
                                'syms',
                                StarRepeat(
                                    Nonterminal('Sym')
                                )
                            )
                        )
                    ),
                    'labeled'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol(
                                'modifiers',
                                StarRepeat(
                                    Nonterminal('ProdModifier')
                                )
                            ),
                            LabeledSymbol(
                                'syms',
                                StarRepeat(
                                    Nonterminal('Sym')
                                )
                            )
                        )
                    ),
                    'unlabeled'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol(
                                'associativity',
                                Nonterminal('Assoc')
                            ),
                            Literal('('),
                            LabeledSymbol('group', Nonterminal('Prod')),
                            Literal(')')
                        )
                    ),
                    'associativityGroup'
                )
            ),
            (
                LabeledRule(
                    (
                        AssociativityModifier(AssociativityOptions.Left),
                    ),
                    Sequence(
                        (
                            LabeledSymbol('lhs', Nonterminal('Prod')),
                            Literal('|'),
                            LabeledSymbol('rhs', Nonterminal('Prod'))
                        )
                    ),
                    'all'
                ),
            ),
            (
                LabeledRule(
                    (
                        AssociativityModifier(AssociativityOptions.Left),
                    ),
                    Sequence(
                        (
                            LabeledSymbol('lhs', Nonterminal('Prod')),
                            NotFollow(
                                symbol=Literal('>'),
                                constraint=Literal('>')
                            ),
                            LabeledSymbol('rhs', Nonterminal('Prod'))
                        )
                    ),
                    'first'
                ),
            )
        )
    )
)


char_class = Syntax(
    name='Class',
    production=Choice(
        (
            (
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('['),
                            LabeledSymbol(
                                'ranges',
                                StarRepeat(Nonterminal('Range'))
                            ),
                            Literal(']')
                        )
                    ),
                    'simpleCharclass'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('!'),
                            LabeledSymbol('charClass', Nonterminal('Class'))
                        )
                    ),
                    'complement'
                )
            ),
            (
                LabeledRule(
                    (
                        AssociativityModifier(AssociativityOptions.Left),
                    ),
                    Sequence(
                        (
                            LabeledSymbol('lhs', Nonterminal('Class')),
                            Literal('-'),
                            LabeledSymbol('rhs', Nonterminal('Class'))
                        )
                    ),
                    'difference'
                ),
            ),
            (
                LabeledRule(
                    (
                        AssociativityModifier(AssociativityOptions.Left),
                    ),
                    Sequence(
                        (
                            LabeledSymbol('lhs', Nonterminal('Class')),
                            Literal('&&'),
                            LabeledSymbol('rhs', Nonterminal('Class'))
                        )
                    ),
                    'intersection'
                ),
            ),
            (
                LabeledRule(
                    (
                        AssociativityModifier(AssociativityOptions.Left),
                    ),
                    Sequence(
                        (
                            LabeledSymbol('lhs', Nonterminal('Class')),
                            Literal('||'),
                            LabeledSymbol('rhs', Nonterminal('Class'))
                        )
                    ),
                    'union'
                ),
                LabeledRule(
                    (
                        BracketModifier(),
                    ),
                    Sequence(
                        (
                            Literal('('),
                            LabeledSymbol('charClass', Nonterminal('Class')),
                            Literal(')')
                        )
                    ),
                    'bracket'
                )
            )
        )
    )
)

char_range = Syntax(
    name='Range',
    production=Choice(
        (
            (
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('start', Nonterminal('Char')),
                            Literal('-'),
                            LabeledSymbol('end', Nonterminal('Char'))
                        )
                    ),
                    'fromTo'
                ),
                LabeledRule(
                    (),
                    LabeledSymbol('character', Nonterminal('Char')),
                    'character'
                )
            ),
        )
    )
)

char = Lexical(
    name='Char',
    production=Choice(
        (
            (
                UnlabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('\\'),
                            CharacterRange((
                                (ord(' '), ord(' ')),
                                (ord('"'), ord('"')),
                                (ord("'"), ord("'")),
                                (ord('-'), ord('-')),
                                (ord('<'), ord('<')),
                                (ord('>'), ord('>')),
                                (ord('['), ord('[')),
                                (ord(']'), ord(']')),
                                (ord('\\'), ord('\\')),
                                (ord('b'), ord('b')),
                                (ord('f'), ord('f')),
                                (ord('n'), ord('n')),
                                (ord('r'), ord('r')),
                                (ord('t'), ord('t')),
                            ))
                        )
                    )
                ),
                UnlabeledRule(
                    (),
                    CharacterClassComplement(
                        CharacterRange((
                            (ord(' '), ord(' ')),
                            (ord('"'), ord('"')),
                            (ord("'"), ord("'")),
                            (ord('-'), ord('-')),
                            (ord('<'), ord('<')),
                            (ord('>'), ord('>')),
                            (ord('['), ord('[')),
                            (ord(']'), ord(']')),
                            (ord('\\'), ord('\\')),
                            (ord('b'), ord('b')),
                            (ord('f'), ord('f')),
                            (ord('n'), ord('n')),
                            (ord('r'), ord('r')),
                            (ord('t'), ord('t')),
                        ))
                    )
                ),
                UnlabeledRule(
                    (),
                    Nonterminal('UnicodeEscape')
                )
            ),
        )
    )
)

sym = Syntax(
    name='Sym',
    production=Choice(
        (
            (
                LabeledRule(
                    (),
                    NotFollow(
                        symbol=LabeledSymbol('nonterminal', Nonterminal('Nonterminal')),
                        constraint=Literal('[')
                    ),
                    'nonterminal'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('&'),
                            LabeledSymbol('nonterminal', Nonterminal('Nonterminal'))
                        )
                    ),
                    'parameter'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            NotFollow(
                                symbol=LabeledSymbol('nonterminal', Nonterminal('Nonterminal')),
                                constraint=Literal('[')
                            ),
                            Literal('['),
                            LabeledSymbol(
                                'parameters',
                                PlusRepeatWithSeparator(
                                    symbol=Nonterminal('Sym'),
                                    separator=Literal(',')
                                )
                            ),
                            Literal(']')
                        )
                    ),
                    'parametrized'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('start'),
                            Literal('['),
                            LabeledSymbol('nonterminal', Nonterminal('Nonterminal')),
                            Literal(']')
                        )
                    ),
                    'start'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            LabeledSymbol('label', Nonterminal('nonterminalLabel'))
                        )
                    ),
                    'labeled'
                ),
                LabeledRule(
                    (),
                    LabeledSymbol('charClass', Nonterminal('Class')),
                    'characterClass'
                ),
                LabeledRule(
                    (),
                    LabeledSymbol('string', Nonterminal('StringConstant')),
                    'literal'
                ),
                LabeledRule(
                    (),
                    LabeledSymbol('cistring', Nonterminal('CaseInsensitiveStringConstant')),
                    'caseInsensitiveLiteral'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            Literal('+')
                        )
                    ),
                    'iter'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            Literal('*')
                        )
                    ),
                    'iterStar'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('{'),
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            LabeledSymbol('sep', Nonterminal('Sym')),
                            Literal('}'),
                            Literal('+')
                        )
                    ),
                    'iterSep'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('{'),
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            LabeledSymbol('sep', Nonterminal('Sym')),
                            Literal('}'),
                            Literal('*')
                        )
                    ),
                    'iterStarSep'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            Literal('?')
                        )
                    ),
                    'optional'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('('),
                            LabeledSymbol('first', Nonterminal('Sym')),
                            Literal('|'),
                            LabeledSymbol(
                                'alternatives',
                                PlusRepeatWithSeparator(
                                    symbol=Nonterminal('Sym'),
                                    separator=Literal('|')
                                )
                            ),
                            Literal(')')
                        )
                    ),
                    'alternative'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('('),
                            LabeledSymbol('first', Nonterminal('Sym')),
                            LabeledSymbol(
                                'sequence',
                                PlusRepeat(
                                    Nonterminal('Sym')
                                )
                            ),
                            Literal(')')
                        )
                    ),
                    'sequence'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            Literal('{'),
                            Optional(
                                LabeledSymbol(
                                    'minimum',
                                    Nonterminal('IntegerLiteral')
                                )
                            ),
                            Literal(':'),
                            Optional(
                                LabeledSymbol(
                                    'maximum',
                                    Nonterminal('IntegerLiteral')
                                )
                            ),
                            Literal('}')
                        )
                    ),
                    'rangedIter'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('{'),
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            LabeledSymbol('separator', Nonterminal('Sym')),
                            Literal('}'),
                            Literal('{'),
                            Optional(
                                LabeledSymbol(
                                    'minimum',
                                    Nonterminal('IntegerLiteral')
                                )
                            ),
                            Literal(':'),
                            Optional(
                                LabeledSymbol(
                                    'maximum',
                                    Nonterminal('IntegerLiteral')
                                )
                            ),
                            Literal('}')
                        )
                    ),
                    'rangedIterSep'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('('),
                            Literal(')')
                        )
                    ),
                    'empty'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            Literal('$')
                        )
                    ),
                    'endOfLine'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('^'),
                            LabeledSymbol('symbol', Nonterminal('Sym'))
                        )
                    ),
                    'startOfLine'
                ),
                LabeledRule(
                    (),
                    Sequence(
                        (
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            Literal('!'),
                            LabeledSymbol('label', Nonterminal('NonterminalLabel'))
                        )
                    ),
                    'except'
                )
            ),
            (
                AssociativityGroup(
                    associativity=AssociativityOptions.Assoc,
                    group=Choice(
                        (
                            (
                                AssociativityGroup(
                                    associativity=AssociativityOptions.Left,
                                    group=Choice(
                                        (
                                            (
                                                LabeledRule(
                                                    (),
                                                    Sequence(
                                                        (
                                                            LabeledSymbol('symbol', Nonterminal('Sym')),
                                                            Literal('>>'),
                                                            LabeledSymbol('match', Nonterminal('Sym'))
                                                        )
                                                    ),
                                                    'follow'
                                                ),
                                                LabeledRule(
                                                    (),
                                                    Sequence(
                                                        (
                                                            LabeledSymbol('symbol', Nonterminal('Sym')),
                                                            Literal('!>>'),
                                                            LabeledSymbol('match', Nonterminal('Sym'))
                                                        )
                                                    ),
                                                    'notFollow'
                                                ),
                                            ),
                                        )
                                    )
                                ),
                                AssociativityGroup(
                                    associativity=AssociativityOptions.Right,
                                    group=Choice(
                                        (
                                            (
                                                LabeledRule(
                                                    (),
                                                    Sequence(
                                                        (
                                                            LabeledSymbol('match', Nonterminal('Sym')),
                                                            Literal('<<'),
                                                            LabeledSymbol('symbol', Nonterminal('Sym'))
                                                        )
                                                    ),
                                                    'precede'
                                                ),
                                                LabeledRule(
                                                    (),
                                                    Sequence(
                                                        (
                                                            LabeledSymbol('match', Nonterminal('Sym')),
                                                            Literal('!<<'),
                                                            LabeledSymbol('symbol', Nonterminal('Sym'))
                                                        )
                                                    ),
                                                    'notPrecede'
                                                ),
                                            ),
                                        )
                                    )
                                ),
                            ),
                        )
                    )
                ),
            ),
            (
                LabeledRule(
                    (
                        AssociativityModifier(AssociativityOptions.Left),
                    ),
                    Sequence(
                        (
                            LabeledSymbol('symbol', Nonterminal('Sym')),
                            Literal('\\\\'),
                            LabeledSymbol('match', Nonterminal('Sym'))
                        )
                    ),
                    'unequal'
                ),
            )
        )
    )
)

comment = Lexical(
    name='Comment',
    production=Choice(
        (
            (
                UnlabeledRule(
                    (),
                    Sequence(
                        (
                            Literal('/*'),
                            StarRepeat(
                                Alternative(
                                    (
                                        CharacterClassComplement(
                                            CharacterRange((
                                                (ord('*'), ord('*')),
                                            ))
                                        ),
                                        NotFollow(
                                            symbol=Literal('*'),
                                            constraint=Literal('/')
                                        )
                                    )
                                )
                            ),
                            Literal('*/')
                        )
                    )
                ),
                UnlabeledRule(
                    (),
                    Sequence(
                        (

                            Literal('//'),
                            EndOfLine(
                                StarRepeat(
                                    CharacterClassComplement(
                                        CharacterRange((
                                            (ord('\n'), ord('\n')),
                                        ))
                                    )
                                )
                            )
                        )
                    )
                )
            ),
        )
    )
)

layout = Layout(
    name='LAYOUT',
    production=Choice(
        (
            (
                UnlabeledRule(
                    (),
                    Nonterminal('Comment')
                ),
                UnlabeledRule(
                    (),
                    CharacterRange((
                        (ord('\u0009'), ord('\u000D')),
                        (ord('\u0020'), ord('\u0020')),
                        (ord('\u0085'), ord('\u0085')),
                        (ord('\u00A0'), ord('\u00A0')),
                        (ord('\u1680'), ord('\u1680')),
                        (ord('\u180E'), ord('\u180E')),
                        (ord('\u2000'), ord('\u200A')),
                        (ord('\u2028'), ord('\u2029')),
                        (ord('\u202F'), ord('\u202F')),
                        (ord('\u205F'), ord('\u205F')),
                        (ord('\u3000'), ord('\u3000')),
                    ))
                )
            ),
        )
    )
)

grammar = GrammarDefinition(
    language='Rascal',
    layout=layout,
    start='SyntaxDefinitions',
    rules=[
        syntax_definitions,
        syntax_definition,
        start,
        octal_literal,
        hex_literal,
        decimal_literal,
        integer_literal,
        assoc,
        unicode_escape,
        name,
        nonterminal_label,
        string_character,
        case_insensitive_string_constant,
        string_constant,
        nonterminal,
        syntax_keywords,
        tag,
        tag_string,
        prod_modifier,
        prod,
        char_class,
        char_range,
        char,
        sym,
        comment
    ]
)
