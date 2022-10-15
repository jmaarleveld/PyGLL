from pygll.generator.context_free_grammar import ContextFreeGrammar, Terminal, Nonterminal
from pygll import generate_parser


# g = ContextFreeGrammar(
#     start=Nonterminal('S'),
#     rules={
#         Nonterminal('S'): (
#             (Terminal.literal('a'), Nonterminal('S')),
#             (Nonterminal('A'), Nonterminal('S'), Terminal.literal('d')),
#             (Terminal.empty(),),
#             (Nonterminal('B'),)
#         ),
#         Nonterminal('A'): (
#             (Terminal.literal('a'),),
#             (Terminal.literal('c'),),
#         ),
#         Nonterminal('B'): (
#             (Terminal.literal('b'), Nonterminal('B')),
#             (Terminal.literal('b'),),
#             (Terminal.literal('e'), Terminal.literal('e'), Terminal.literal('e'))
#         )
#     },
# )

# tags = {
#     (Nonterminal('S'), 1, 1): [
#         ('not_precede', [Terminal.literal('c')])
#     ],
#     # FIXME: THIS GENERATES TWO CHECKS, BOTH OF WHICH ARE IN THE WRONG PLACE
#     (Nonterminal('B'), 2, 2): [
#         ('not_precede', [Terminal.literal('ee')])
#     ]
# }

g = ContextFreeGrammar(
    start=Nonterminal('S'),
    rules={
        Nonterminal('S'): (
            (Terminal.literal('a'), Nonterminal('S')),
            (Terminal.literal('b'),),
            (Terminal.literal('a'),)
        )
    }
)
tags = {
    (Nonterminal('S'), 0, 1): [
        ('not_follow', [Terminal.literal('b')])
    ]
}

generate_parser(g, 'TestParser', 'test_parser.py', tags=tags)
