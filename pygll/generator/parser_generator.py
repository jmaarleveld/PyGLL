##############################################################################
##############################################################################
# Imports
##############################################################################

import functools
import typing

from ...util import cache
from ..grammar import context_free_grammar as _cfg

from .code_gen import AbstractCodeGenerator

##############################################################################
##############################################################################
# Functionality for generating functions for parsing alternates
##############################################################################


def generate_parser(grammar: _cfg.ContextFreeGrammar,
                    generator: AbstractCodeGenerator):
    generator.define_import('orion.gll.core.base', 'AbstractParser')
    generator.define_import('orion.gll.core.base', 'GrammarSlot')
    generator.define_import('orion.gll.core.base', 'Descriptor')
    generator.define_import('orion.gll.core.base', 'InitialNode')
    with generator.define_class('Parser', ['AbstractParser']):
        _generate_grammar_slots(grammar, generator)
        _generate_initial_descriptor(grammar, generator)
        generate_functions_for_all_rules(grammar, generator)
        _generate_terminal_checks(grammar, generator)
        _generate_goto(grammar, generator)


##############################################################################
##############################################################################
# Grammar Slots
##############################################################################


def _generate_grammar_slots(grammar: _cfg.ContextFreeGrammar,
                            generator: AbstractCodeGenerator):
    # Generate a special slot for the first rule
    initial_slot = (f'GrammarSlot('
                    f'"_grammar_slot__init__{grammar.start.name}",'
                    f'0, 0, False, False)')
    generator.assign('_initial_grammar_slot', initial_slot)
    for nonterminal, expansion in grammar.rules.items():
        for alternate_id, alternate in enumerate(expansion):
            for dot_index in range(len(alternate) + 1):
                slot_name = _get_grammar_slot_name(nonterminal,
                                                   alternate_id,
                                                   dot_index)
                # For a grammar slot, we need the nonterminal name,
                # the number of the alternate, and the position
                # of the dot in the rule A ::= alpha . beta
                #
                # We also need some additional information;
                # see the definition of GrammarSlot
                # len(alpha) == 1 and (alpha[0] is a terminal or non-nullable)
                alpha = (
                        dot_index == 1 and
                        (
                                grammar.is_terminal(alternate[0]) or
                                alternate[0] not in grammar.nullables
                        )
                )
                slot = (f'GrammarSlot('
                        f'{nonterminal.name!r}, '
                        f'{alternate_id}, '
                        f'{dot_index}, '
                        f'{alpha}, '
                        f'{dot_index == len(alternate)}'
                        f')')
                generator.assign(slot_name, slot)


def _get_grammar_slot_name(nonterminal: _cfg.Nonterminal,
                           alternate: int,
                           position: int) -> str:
    return f'_grammar_slot_{nonterminal.name}_alt{alternate}_idx{position}'


def _generate_terminal_checks(grammar: _cfg.ContextFreeGrammar,
                              generator: AbstractCodeGenerator):
    seen = set()
    for expansion in grammar.rules.values():
        for alternate in expansion:
            for symbol in alternate:
                if isinstance(symbol, _cfg.Nonterminal):
                    continue
                if symbol in seen:
                    continue
                seen.add(symbol)
                _generate_check_for_terminal(symbol, generator)


def _generate_initial_descriptor(grammar: _cfg.ContextFreeGrammar,
                                 generator: AbstractCodeGenerator):
    name = 'get_initial_grammar_slot'
    with generator.define_function(name, {'self': None}, ''):
        generator.return_value(
            f'self._initial_grammar_slot'
        )
    name = 'get_start_nonterminal'
    with generator.define_function(name, {'self': None}, ''):
        generator.return_value(repr(grammar.start.name))
    slots = []
    for alternate_number, alternate in enumerate(grammar.rules[grammar.start]):
        slot = _get_grammar_slot_name(grammar.start,
                                      alternate_number,
                                      len(alternate))
        slots.append(f'self.{slot}')
    name = 'get_final_slots'
    with generator.define_function(name, {'self': None}, ''):
        generator.return_value('(' + ', '.join(slots) + ')')


def _generate_goto(grammar: _cfg.ContextFreeGrammar,
                   generator: AbstractCodeGenerator):
    with generator.define_function('goto', {'self': None, 'slot': 'GrammarSlot'}, ''):
        with generator.define_conditional():
            # Define a special slot for the initial grammar slot
            with generator.if_statement(f'slot == self._initial_grammar_slot'):
                #generator.call_function('self.on_goto',
                #                        ['slot', repr(grammar.start.name)])
                generator.call_function(f'self.{grammar.start.name}', [])
            for nonterminal, expansion in grammar.rules.items():
                for alternate_number, alternate in enumerate(expansion):
                    blocks = grammar.compute_gll_blocks(alternate)
                    for block_number, (gll_index, _) in enumerate(blocks):
                        name = _get_grammar_slot_name(nonterminal,
                                                      alternate_number,
                                                      gll_index)
                        func_name = f'{nonterminal.name}{alternate_number}'
                        if block_number > 0:
                            func_name += f'_{block_number}'
                        with generator.if_statement(f'slot == self.{name}'):
                            #generator.call_function(f'self.on_goto',
                            #                        ['slot', repr(func_name)])
                            generator.call_function(f'self.{func_name}', [])
            with generator.else_statement():
                generator.call_function('self.unknown', ['slot'])


##############################################################################
##############################################################################
# Functionality for generating functions for parsing alternates
##############################################################################


def generate_functions_for_all_rules(grammar: _cfg.ContextFreeGrammar,
                                     generator: AbstractCodeGenerator):
    for nonterminal, expansion in grammar.rules.items():
        generate_functions_for_rule(nonterminal,
                                    expansion,
                                    generator,
                                    grammar)


def generate_functions_for_rule(
        nonterminal: _cfg.Nonterminal,
        expansion: _cfg.Expansion,
        generator: AbstractCodeGenerator,
        grammar: _cfg.ContextFreeGrammar):
    _generate_alternate_switch_function(nonterminal,
                                        expansion,
                                        generator,
                                        grammar)
    for alternate_number, alternate in enumerate(expansion):
        _generate_functions_for_alternate(nonterminal,
                                          alternate,
                                          alternate_number,
                                          generator,
                                          grammar)


def _generate_alternate_switch_function(
        nonterminal: _cfg.Nonterminal,
        expansion: _cfg.Expansion,
        generator: AbstractCodeGenerator,
        grammar: _cfg.ContextFreeGrammar):
    with generator.define_function(nonterminal.name, {'self': None}, ''):
        #generator.call_function('self.on_call', [repr(nonterminal.name)])
        for alternate_number, alternate in enumerate(expansion):
            test_set = grammar.test_for_sequence(nonterminal,
                                                 alternate_number,
                                                 0)
            check = ' or '.join(f'self.{_get_terminal_check_name(x)}()'
                                for x in test_set)
            with generator.define_conditional():
                with generator.if_statement(check):
                    slot = _get_grammar_slot_name(nonterminal,
                                                  alternate_number,
                                                  0)
                    generator.call_function(
                        'self.add',
                        [
                            f'self.{slot}',
                            'self.c_u',
                            'self.scanner.position',
                            'InitialNode(0, 0)'
                        ]
                    )


def _generate_functions_for_alternate(
        nonterminal: _cfg.Nonterminal,
        alternate: _cfg.Alternative,
        alternate_number: int,
        generator: AbstractCodeGenerator,
        grammar: _cfg.ContextFreeGrammar):
    g = _cfg.ContextFreeGrammar
    gll_blocks = list(g.compute_gll_blocks(alternate))
    for block_number, (gll_index, gll_block) in enumerate(gll_blocks):
        function_name = f'{nonterminal.name}{alternate_number}'
        if block_number > 0:
            function_name = f'{function_name}_{block_number}'
        with generator.define_function(function_name, {'self': None}, ''):
            #generator.call_function('self.on_call', [repr(function_name)])
            _generate_body_for_function(gll_block,
                                        nonterminal,
                                        alternate_number,
                                        gll_index,
                                        block_number,
                                        block_number == 0,
                                        block_number == len(gll_blocks) - 1,
                                        1,
                                        generator,
                                        grammar)


def _generate_body_for_function(
        gll_block: _cfg.GLLBlock,
        nonterminal: _cfg.Nonterminal,
        alt_number: int,
        gll_index: int,
        block_number: int,
        first_symbol: bool,
        add_pop: bool,
        position: int,
        generator: AbstractCodeGenerator,
        grammar: _cfg.ContextFreeGrammar):
    if gll_block:
        first = gll_block[0]
        if isinstance(first, _cfg.Terminal):
            if not first_symbol:
                generator.assign('check_result, consumed',
                                 f'self.{_get_terminal_check_name(first, with_consumed=True)}()')
            else:
                generator.assign('consumed', _get_scanner_step(first))
            if first_symbol and len(gll_block) != 1:
                generator.assign(
                    'self.c_n',
                    f'self.get_node_t(consumed)'
                )
                generator.call_function('self.scanner.get_next', ['consumed'])
            condition = ('True' if first_symbol
                         else 'check_result')
            if (not first_symbol) or (first_symbol and len(gll_block) == 1):
                with generator.define_conditional():
                    with generator.if_statement(condition):
                        generator.assign(
                            'self.c_r',
                            f'self.get_node_t(consumed)'
                        )
                        generator.call_function('self.scanner.get_next',
                                                ['consumed'])
                        slot = _get_grammar_slot_name(nonterminal,
                                                      alt_number,
                                                      gll_index + 1)
                        generator.assign(
                            'self.c_n',
                            f'self.get_node_p(self.{slot}, self.c_n, self.c_r)'
                        )
        else:
            test_set = grammar.test(first)
            check = ' or '.join(f'self.{_get_terminal_check_name(x)}()' for x in test_set)
            condition = ('True' if first_symbol
                         else f'{check}')
            next_slot = _get_grammar_slot_name(nonterminal, alt_number, gll_index + 1)
            with generator.define_conditional():
                with generator.if_statement(condition):
                    generator.assign(
                        'self.c_u',
                        f'self.create(self.{next_slot})'
                    )
                    generator.call_function(f'self.{first.name}', [])
        _generate_body_for_function(gll_block[1:],
                                    nonterminal,
                                    alt_number,
                                    gll_index + 1,
                                    block_number,
                                    False,
                                    add_pop,
                                    position + 1,
                                    generator,
                                    grammar)
    elif add_pop:
        generator.call_function('self.pop', [])


@functools.cache
def _get_terminal_check_name(terminal: _cfg.Terminal,
                             *, with_consumed=False) -> str:
    match terminal:
        case _cfg.Terminal(ranges=None, sequence=None):
            suffix = 'empty'
        case _cfg.Terminal(ranges=ranges, sequence=None):
            suffix = 'ranges' + '__'.join(
                f'{start}_{stop}' if start != stop else str(start)
                for start, stop in ranges
            )
        case _cfg.Terminal(ranges=None, sequence=seq):
            suffix = f'literal_{seq}'
        case _:
            raise ValueError(terminal)
    if with_consumed:
        extra = 'consumed_'
    else:
        extra = ''
    return f'terminal_test_{extra}{suffix}'


@functools.cache
def _get_scanner_step(terminal: _cfg.Terminal) -> str:
    match terminal:
        case _cfg.Terminal(ranges=None, sequence=None):
            return repr('')
        case _cfg.Terminal(ranges=_, sequence=None):
            return 'self.scanner.peek(1)'
        case _cfg.Terminal(ranges=None, sequence=seq):
            return repr(seq)
        case _:
            raise ValueError(terminal)


@cache.cached(key=lambda terminal, generator: terminal)
def _generate_check_for_terminal(terminal: _cfg.Terminal,
                                 generator: AbstractCodeGenerator):
    function_name_normal = _get_terminal_check_name(terminal)
    function_name_consumed = _get_terminal_check_name(terminal,
                                                      with_consumed=True)
    match terminal:
        case _cfg.Terminal(ranges=None, sequence=None):
            with generator.define_function(function_name_consumed, {'self': None}, ''):
                generator.return_value('True, ""')
            with generator.define_function(function_name_normal, {'self': None}, ''):
                generator.return_value('True')
        case _cfg.Terminal(ranges=None, sequence=seq):
            with generator.define_function(function_name_consumed, {'self': None}, ''):
                generator.assign('check', f'self.scanner.has_next({seq!r})')
                with generator.define_conditional():
                    with generator.if_statement('check'):
                        generator.return_value(f'True, {seq!r}')
                    with generator.else_statement():
                        generator.return_value(f'False, None')
            with generator.define_function(function_name_normal, {'self': None}, ''):
                generator.return_value(f'self.scanner.has_next({seq!r})')
        case _cfg.Terminal(ranges=ranges, sequence=None):
            condition = ' or '.join(
                (
                    f'{start} <= symbol <= {stop}'
                    if start != stop
                    else f'{start} == symbol')
                for start, stop in ranges
            )
            with generator.define_function(function_name_consumed, {'self': None}, ''):
                generator.assign('symbol', 'ord(self.scanner.peek(1))')
                generator.assign('check', condition)
                with generator.define_conditional():
                    with generator.if_statement('check'):
                        generator.return_value(f'True, self.scanner.peek(1)')
                    with generator.else_statement():
                        generator.return_value(f'False, None')
            with generator.define_function(function_name_normal, {'self': None}, ''):
                generator.assign('symbol', 'ord(self.scanner.peek(1))')
                generator.return_value(condition)
        case _:
            raise ValueError(terminal)

