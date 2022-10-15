##############################################################################
##############################################################################
# Imports
##############################################################################

import functools
import typing

from ..util.algorithms import int_sets as _int_sets

from . import context_free_grammar as _cfg
from . import abstract_parser as _ast


GrammarPosition = tuple[_cfg.Nonterminal, int, int]
TagName = typing.Literal['precede',
                         'not_precede',
                         'follow',
                         'not_follow',
                         'restrict']
Tag = tuple[TagName, typing.Any]

##############################################################################
##############################################################################
# Functionality for generating functions for parsing alternates
##############################################################################


def generate_parser(
        parser_name: str,
        grammar: _cfg.ContextFreeGrammar,
        tags: dict[GrammarPosition, list[Tag]]) -> _ast.ParserDefinition:
    parser_definition = _ast.ParserDefinition(
        _ast.ParserMetadata(parser_name)
    )
    _generate_start_nonterminal_functions(parser_definition, grammar)
    _generate_functions_for_rules(parser_definition, grammar, tags)
    return parser_definition


def _generate_start_nonterminal_functions(definition: _ast.ParserDefinition,
                                          grammar: _cfg.ContextFreeGrammar):
    # define the initial grammar slot.
    initial_slot_start = definition.get_and_declare_grammar_slot(
        grammar.start.name, 0, 0, grammar, is_initial=True
    )
    definition.initial_grammar_slot_start = initial_slot_start
    initial_slot_end = definition.get_and_declare_grammar_slot(
        grammar.start.name, 0, 1, grammar, is_initial=True
    )
    definition.initial_grammar_slot_end = initial_slot_end
    definition.add_goto_entry(initial_slot_start,
                              f'nonterminal_check_{grammar.start.name}')


def _generate_functions_for_rules(definition: _ast.ParserDefinition,
                                  grammar: _cfg.ContextFreeGrammar,
                                  tags: dict[GrammarPosition, list[Tag]]):
    for nonterminal, expansion in grammar.rules.items():
        _generate_start_function(nonterminal, definition, grammar, tags)
        for alternate_number, alternate in enumerate(expansion):
            gll_blocks = list(grammar.compute_gll_blocks(alternate))
            blocks_and_indices = enumerate(gll_blocks)
            for block_number, (block_index, gll_block) in blocks_and_indices:
                # Get function body
                body = _generate_gll_block_function(
                    definition, gll_block, nonterminal, alternate_number,
                    block_index, block_number, block_number == 0,
                    block_number == len(gll_blocks) - 1, grammar, tags)
                # Get function name
                if block_number == 0:
                    function_name = f'nonterminal_check_{nonterminal.name}{alternate_number}'
                else:
                    function_name = f'nonterminal_check_{nonterminal.name}{alternate_number}_{block_number}'
                # Add function to parser
                definition.add_function(
                    _ast.FunctionDefinition(name=function_name, body=body)
                )
                # Add goto entry
                grammar_slot = definition.get_and_declare_grammar_slot(
                    nonterminal.name, alternate_number, block_index, grammar
                )
                definition.add_goto_entry(grammar_slot, function_name)


##############################################################################
##############################################################################
# Nonterminal -- start function
##############################################################################


def _generate_start_function(nonterminal: _cfg.Nonterminal,
                             definition: _ast.ParserDefinition,
                             grammar: _cfg.ContextFreeGrammar,
                             tags: dict[GrammarPosition, list[Tag]]):
    body = []
    for alternate_number, alternate in enumerate(grammar.rules[nonterminal]):
        test_set = grammar.test_for_sequence(nonterminal,
                                             alternate_number,
                                             0)
        slot_name = definition.get_and_declare_grammar_slot(nonterminal.name,
                                                            alternate_number,
                                                            0,
                                                            grammar)
        body.append(
            _ast.ConditionalCheck(checks=_test_set_to_checks(definition,
                                                             test_set),
                                  body=[_ast.InvokeAdd(slot_name)])
        )
    definition.add_function(
        _ast.FunctionDefinition(name=f'nonterminal_check_{nonterminal.name}',
                                body=body)
    )


##############################################################################
##############################################################################
# Parsing functions
##############################################################################


def _generate_gll_block_function(definition: _ast.ParserDefinition,
                                 gll_block: _cfg.GLLBlock,
                                 nonterminal: _cfg.Nonterminal,
                                 alternate_number: int,
                                 absolute_position: int,
                                 block_number: int,
                                 first_symbol: bool,
                                 add_pop: bool,
                                 grammar: _cfg.ContextFreeGrammar,
                                 tags: dict[GrammarPosition, list[Tag]]
                                 ) -> list[_ast.StatementDefinition]:
    body = []
    if gll_block:
        # body.extend(
        #     _generate_precede_checks(definition,
        #                              nonterminal,
        #                              alternate_number,
        #                              absolute_position,
        #                              grammar,
        #                              tags)
        # )
        if isinstance(gll_block[0], _cfg.Terminal):
            new_statements, inner_body = _generate_gll_block_function_for_terminal(
                definition, gll_block, nonterminal, alternate_number,
                absolute_position, block_number, first_symbol, add_pop, grammar, tags
            )
        else:
            new_statements, inner_body = _generate_gll_block_function_for_nonterminal(
                definition, gll_block, nonterminal, alternate_number,
                absolute_position, block_number, first_symbol, add_pop, grammar, tags
            )
        tail = _generate_gll_block_function(definition,
                                            gll_block[1:],
                                            nonterminal,
                                            alternate_number,
                                            absolute_position + 1,
                                            block_number,
                                            False,
                                            add_pop,
                                            grammar,
                                            tags)

        # Add new statements before tail in case new_statements is inner_body
        inner_body.extend(tail)
        body.extend(new_statements)
    elif add_pop:
        body.append(_ast.InvokePop())
    return body


_T = tuple[list[_ast.StatementDefinition], list[_ast.StatementDefinition]]


def _generate_gll_block_function_for_terminal(
        definition: _ast.ParserDefinition,
        gll_block: _cfg.GLLBlock,
        nonterminal: _cfg.Nonterminal,
        alternate_number: int,
        absolute_position: int,
        block_number: int,
        first_symbol: bool,
        add_pop: bool,
        grammar: _cfg.ContextFreeGrammar,
        tags: dict[GrammarPosition, list[Tag]]) -> _T:
    # This function generates the body of the function
    # responsible for generating a GLL block.
    # This function also inserts the ambiguity checks
    # in the GLL block.
    # Whenever we call get_node_t and advance the scanner,
    # we effectively move to a new grammar position
    # where we may have to insert an ambiguity check.
    # We can generate get_node_t in two possible places
    # in this function. In both places, we insert a
    # check if needed. The checks are generated in
    # mutually exclusive scenarios, so no double
    # check can be generated.
    body = []
    head_check = _terminal_to_check(definition, gll_block[0])
    if first_symbol and len(gll_block) != 1:
        body.extend(
            _generate_ambiguity_checks(definition,
                                       nonterminal,
                                       alternate_number,
                                       absolute_position,
                                       grammar,
                                       tags)
        )
        body.append(_ast.InvokeNodeT(_ast.NodeAssignmentTarget.CN,
                                     head_check))
    if not first_symbol:
        inner_body = []
        conditional = _ast.ConditionalCheck(
            checks=[_terminal_to_check(definition, gll_block[0])],
            body=inner_body
        )
        body.append(conditional)
    else:
        inner_body = body
    if (first_symbol and len(gll_block) == 1) or not first_symbol:
        inner_body.extend(
            _generate_ambiguity_checks(definition,
                                       nonterminal,
                                       alternate_number,
                                       absolute_position,
                                       grammar,
                                       tags)
        )
        inner_body.append(_ast.InvokeNodeT(_ast.NodeAssignmentTarget.CR,
                                           head_check))
        next_slot_name = definition.get_and_declare_grammar_slot(
            nonterminal.name, alternate_number, absolute_position + 1, grammar
        )
        inner_body.append(_ast.InvokeNodeP(_ast.NodeAssignmentTarget.CN,
                                           next_slot_name))
    return body, inner_body


def _generate_gll_block_function_for_nonterminal(
        definition: _ast.ParserDefinition,
        gll_block: _cfg.GLLBlock,
        nonterminal: _cfg.Nonterminal,
        alternate_number: int,
        absolute_position: int,
        block_number: int,
        first_symbol: bool,
        add_pop: bool,
        grammar: _cfg.ContextFreeGrammar,
        tags: dict[GrammarPosition, list[Tag]]) -> _T:
    # First, check whether we need a conditional
    body = []
    if not first_symbol:
        inner_body = []
        test_functions = _test_set_to_checks(definition,
                                             grammar.test(gll_block[0]))
        conditional = _ast.ConditionalCheck(checks=test_functions,
                                            body=inner_body)
        body.append(conditional)
    else:
        inner_body = body
    # Get name of the grammar slot
    inner_body.extend(
        _generate_ambiguity_checks(definition,
                                   nonterminal,
                                   alternate_number,
                                   absolute_position,
                                   grammar,
                                   tags)
    )
    grammar_slot_name = definition.get_and_declare_grammar_slot(
        nonterminal.name, alternate_number, absolute_position + 1, grammar
    )
    # Add body content
    # TODO: insert precede check? What about the conditional?
    inner_body.append(_ast.InvokeCreate(grammar_slot_name))
    inner_body.append(
        _ast.CallFunction(f'nonterminal_check_{gll_block[0].name}')
    )
    # Return result
    return body, inner_body


##############################################################################
##############################################################################
# Ambiguity Checks
##############################################################################


def _generate_ambiguity_checks(definition: _ast.ParserDefinition,
                               nonterminal: _cfg.Nonterminal,
                               alternate_number: int,
                               absolute_position: int,
                               grammar: _cfg.ContextFreeGrammar,
                               tags: dict[GrammarPosition, list[Tag]]):
    key = (nonterminal, alternate_number, absolute_position)
    tags_at_pos = tags.get(key, [])
    slot_name = _ast.GrammarSlotDefinition.get_slot_name(
        nonterminal.name, alternate_number, absolute_position + 1
    )
    ambiguity_checks = []
    for tag in tags_at_pos:
        match tag:
            case ('precede', terminals):
                literals, ranges = _split_terminals(terminals)
                check = definition.get_and_declare_precede(slot=slot_name,
                                                           literals=literals,
                                                           ranges=list(ranges))
                ambiguity_checks.append(_ast.Disambiguate(check))
            case ('not_precede', terminals):
                literals, ranges = _split_terminals(terminals)
                check = definition.get_and_declare_not_precede(slot=slot_name,
                                                               literals=literals,
                                                               ranges=list(ranges))
                ambiguity_checks.append(_ast.Disambiguate(check))
            case ('follow', terminals):
                literals, ranges = _split_terminals(terminals)
                symbol_at_pos = grammar.rules[nonterminal][alternate_number][absolute_position]
                check_in_pop = not grammar.is_terminal(symbol_at_pos)
                check = definition.get_and_declare_follow(slot=slot_name,
                                                          literals=literals,
                                                          ranges=list(ranges),
                                                          in_pop=check_in_pop)
                if not check_in_pop:
                    ambiguity_checks.append(_ast.Disambiguate(check))
            case ('not_follow', terminals):
                literals, ranges = _split_terminals(terminals)
                symbol_at_pos = grammar.rules[nonterminal][alternate_number][absolute_position]
                check_in_pop = not grammar.is_terminal(symbol_at_pos)
                check = definition.get_and_declare_not_follow(slot=slot_name,
                                                              literals=literals,
                                                              ranges=list(ranges),
                                                              in_pop=check_in_pop)
                if not check_in_pop:
                    ambiguity_checks.append(_ast.Disambiguate(check))
            case ('restriction', terminals):
                literals, ranges = _split_terminals(terminals)
                definition.get_and_declare_restriction(slot=slot_name,
                                                       literals=literals,
                                                       ranges=list(ranges))
            case _:
                raise ValueError(f'Cannot handle tag: {tag}')
    return ambiguity_checks


def _split_terminals(
        terminals: list[_cfg.Terminal]) -> tuple[list[str], tuple[tuple[int, int], ...]]:
    literals = []
    ranges = []
    for terminal in terminals:
        match terminal:
            case _cfg.Terminal(ranges=None, sequence=None):
                literals.append('')
            case _cfg.Terminal(ranges=None, sequence=seq):
                literals.append(seq)
            case _cfg.Terminal(ranges=ranges, sequence=None):
                ranges.append(ranges)
            case _:
                raise ValueError(terminal)
    utf8_max = 0x10FFFF
    combined_range = functools.reduce(
        lambda x, y: x | y,
        [_int_sets.IntSet(r, (0, utf8_max)) for r in ranges],
        _int_sets.IntSet.empty_set((0, utf8_max))
    ).ranges
    return literals, combined_range


##############################################################################
##############################################################################
# Auxiliary Functions
##############################################################################


def _test_set_to_checks(
        definition: _ast.ParserDefinition,
        test_set: frozenset[_cfg.Terminal]) -> list[str]:
    return [_terminal_to_check(definition, symbol) for symbol in test_set]


def _terminal_to_check(
        definition: _ast.ParserDefinition,
        terminal: _cfg.Terminal) -> str:
    match terminal:
        case _cfg.Terminal(ranges=None, sequence=None):
            return definition.get_and_declare_literal_check('')
        case _cfg.Terminal(ranges=None, sequence=seq):
            return definition.get_and_declare_literal_check(seq)
        case _cfg.Terminal(ranges=ranges, sequence=None):
            return definition.get_and_declare_range_check(ranges)
