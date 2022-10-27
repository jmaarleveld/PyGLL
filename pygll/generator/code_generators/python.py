##############################################################################
##############################################################################
# Imports
##############################################################################

from .base import AbstractCodeGenerator

from ..abstract_parser import ParserDefinition
from .. import abstract_parser as _ast

##############################################################################
##############################################################################
# Python Implementation
##############################################################################


# This is gonna be messy

class PythonCodeGenerator(AbstractCodeGenerator):

    def generate_code(self, parser: ParserDefinition):
        imports = [
            'from pygll.core.base import AbstractParser',
            'from pygll.core.nodes import GrammarSlot',
            'from pygll.core.nodes import InitialNode',
        ]
        for statement in imports:
            self.writer.write_line(statement)
        self.writer.write_empty_line()
        self.writer.write_empty_line()
        self.writer.write_line(
            f'class {parser.metadata.name}(AbstractParser):'
        )
        with self.writer.increased_indent():
            self._generate_grammar_slots(parser.all_grammar_slots)
            self.writer.write_empty_line()
            self._generate_abstract_methods(parser)
            self.writer.write_empty_line()
            for function in parser.parse_functions.values():
                self._generate_function(parser, function)
                self.writer.write_empty_line()
            for check in parser.input_checks.values():
                if check.get_check_type() == _ast.CheckType.Literal:
                    assert isinstance(check, _ast.LiteralCheckDefinition)
                    self._generate_terminal_check(check)
                else:
                    assert isinstance(check, _ast.RangeCheckDefinition)
                    self._generate_range_check(check)
                self.writer.write_empty_line()
            for check in parser.ambiguity_checks.values():
                self._generate_ambiguity_check(check)
                self.writer.write_empty_line()
            self._generate_pop_ambiguity_jump_table([
                check
                for check in parser.ambiguity_checks.values()
                if check.as_pop_check()
            ])
            self.writer.write_empty_line()
            self._generate_goto(parser.goto)
            self.writer.write_empty_line()
        self.writer.close()

    def _generate_grammar_slots(self,
                                slots: dict[str, _ast.GrammarSlotDefinition]):
        for name, slot in slots.items():
            slot_definition = (f'GrammarSlot('
                               f'{slot.nonterminal!r}, '
                               f'{slot.alternate}, '
                               f'{slot.position}, '
                               f'{slot.alpha}, '
                               f'{slot.beta})')
            self.writer.write_line(f'{name} = {slot_definition}')

    def _generate_goto(self, goto: dict[str, str]):
        self.writer.write_line('def goto(self, slot: GrammarSlot):')
        with self.writer.increased_indent():
            self.writer.write_line('match slot:')
            for slot, target in goto.items():
                with self.writer.increased_indent():
                    if slot is not None:
                        self.writer.write_line(f'case self.{slot}:')
                    else:
                        self.writer.write_line(f'case None:')
                    with self.writer.increased_indent():
                        self.writer.write_line('if self.debug:')
                        with self.writer.increased_indent():
                            self.writer.write_line(f'self.on_goto(slot, {target!r})')
                        self.writer.write_line(f'self.{target}()')
            with self.writer.increased_indent():
                self.writer.write_line('case _:')
                with self.writer.increased_indent():
                    self.writer.write_line('self.unknown(slot)')

    def _generate_abstract_methods(self, parser: ParserDefinition):
        self.writer.write_line('def get_final_slot(self):')
        with self.writer.increased_indent():
            slot_name = parser.final_grammar_slot.name
            self.writer.write_line(f'return self.{slot_name}')
        self.writer.write_empty_line()
        self.writer.write_line('def get_full_nonterminal_slot_for_slot(self, slot):')
        with self.writer.increased_indent():
            self.writer.write_line('match slot.nonterminal:')
            with self.writer.increased_indent():
                for name, slot in parser.full_nonterminal_slots.items():
                    self.writer.write_line(f'case "{slot.nonterminal}":')
                    with self.writer.increased_indent():
                        self.writer.write_line(f'return self.{name}')
                self.writer.write_line('case _:')
                with self.writer.increased_indent():
                    self.writer.write_line('raise ValueError(slot)')

    def _generate_terminal_check(self, check: _ast.LiteralCheckDefinition):
        self.writer.write_line(f'def {check.name}(self):')
        with self.writer.increased_indent():
            if check.text:
                self.writer.write_line(
                    f'return self.scanner.has_next({check.text!r})'
                )
            else:
                self.writer.write_line('return True')

    def _generate_range_check(self, check: _ast.RangeCheckDefinition):
        self.writer.write_line(f'def {check.name}(self):')
        with self.writer.increased_indent():
            self.writer.write_line('char = ord(self.scanner.peek(1))')
            condition = self._get_range_check('char', check.ranges)
            self.writer.write_line(f'return {condition}')

    def _generate_function(self,
                           parser: ParserDefinition,
                           function: _ast.FunctionDefinition):
        self.writer.write_line(f'def {function.name}(self):')
        with self.writer.increased_indent():
            for statement in function.body:
                self._write_statement(parser, statement)

    def _generate_pop_ambiguity_jump_table(self,
                                           checks: list[_ast.AmbiguityCheckDefinition]):
        self.writer.write_line('def get_ambiguity_checks_for_slot(self, slot: GrammarSlot):')
        with self.writer.increased_indent():
            checks_by_slot = {}
            for check in checks:
                checks_by_slot.setdefault(f'self.{check.slot}', []).append(
                    f'self.{check.name}'
            )
            self.writer.write_line(
                'checks_by_slot = {' +
                ', '.join(f'{key}: [{", ".join(value)}]' for key, value in checks_by_slot.items()) +
                '}'
            )
            self.writer.write_line('return checks_by_slot.get(slot, [])')

    def _generate_ambiguity_check(self,
                                  check: _ast.AmbiguityCheckDefinition):
        match check:
            case _ast.PrecedeCheck(_, literals, ranges, negated):
                self._generate_inline_ambiguity_check(literals,
                                                      ranges,
                                                      negated,
                                                      check.name,
                                                      'peek_backward')
            case _ast.FollowCheck(_, literals, ranges, negated, pop_check=False):
                self._generate_inline_ambiguity_check(literals,
                                                      ranges,
                                                      negated,
                                                      check.name,
                                                      'peek_forward')
            case _ast.FollowCheck(_, literals, ranges, negated, pop_check=True):
                self._generate_pop_follow_check(literals,
                                                ranges,
                                                negated,
                                                check.name)
            case _ast.RestrictionCheck(_, literals, ranges):
                self._generate_restriction_check(literals, ranges, check.name)
            case _:
                raise ValueError(
                    f'Cannot generate {check.__class__.__name__} check inline'
                )

    def _generate_inline_ambiguity_check(self,
                                         literals,
                                         ranges,
                                         negated,
                                         name,
                                         peek_function):
        self.writer.write_line(f'def {name}(self):')
        with self.writer.increased_indent():
            self._generate_precede_or_follow_check_body(literals,
                                                        ranges,
                                                        negated,
                                                        peek_function)

    def _generate_pop_follow_check(self, literals, ranges, negated, name):
        self.writer.write_line(f'def {name}(self, start: int, stop: int) -> bool:')
        with self.writer.increased_indent():
            self._generate_precede_or_follow_check_body(literals,
                                                        ranges,
                                                        negated,
                                                        'peek')

    def _generate_precede_or_follow_check_body(self, literals, ranges, negated, peek_function):
        if ranges:
            self.writer.write_line(f'char = self.scanner.{peek_function}(1)')
            condition = self._get_range_check('char', ranges)
            self.writer.write_line(f'if {condition}:')
            with self.writer.increased_indent():
                self.writer.write_line(f'return {not negated}')
        if literals:
            literals_by_length = {}
            for literal in literals:
                literals_by_length.setdefault(len(literal), set()).add(literal)
            for length, literals_with_length in literals_by_length.items():
                self.writer.write_line(f'text = self.scanner.{peek_function}({length})')
                self.writer.write_line(f'if text in {literals_with_length}:')
                with self.writer.increased_indent():
                    self.writer.write_line(f'return {not negated}')
        self.writer.write_line(f'return {negated}')

    def _generate_restriction_check(self, literals, ranges, name):
        self.writer.write_line(f'def {name}(self, start: int, stop: int) -> bool:')
        with self.writer.increased_indent():
            self.writer.write_line('length = stop - start')
            self.writer.write_line('string = self.scanner.get_slice(start, stop)')
            if ranges:
                range_condition = self._get_range_check('c', ranges)
                self.writer.write_line(f'if length == 1:')
                with self.writer.increased_indent():
                    self.writer.write_line('c = ord(string)')
                    self.writer.write_line(f'if {range_condition}:')
                    with self.writer.increased_indent():
                        self.writer.write_line('return False')
            if literals:
                literals_by_length = {}
                for literal in literals:
                    literals_by_length.setdefault(len(literal), set()).add(literal)
                self.writer.write_line(f'literals_by_length = {literals_by_length!r}')
                self.writer.write_line('return string in literals_by_length[length]')
            self.writer.write_line('return True')

    def _write_statement(self,
                         parser: ParserDefinition,
                         statement: _ast.StatementDefinition):
        match statement:
            case _ast.InvokeCreate(grammar_slot=slot):
                self.writer.write_line(f'self.c_u = self.create(self.{slot})')
            case _ast.InvokeAdd(grammar_slot=slot):
                self.writer.write_line(f'self.add('
                                       f'self.{slot}, '
                                       f'self.c_u, '
                                       f'self.scanner.position, '
                                       f'InitialNode(0, 0))')
            case _ast.CallFunction(function=function):
                self.writer.write_line(f'self.{function}()')
            case _ast.InvokePop():
                self.writer.write_line('self.pop()')
            case _ast.InvokeNodeT(parent_check=check_name, target=target):
                target = self._resolve_target(target)
                check = parser.input_checks[check_name]
                if isinstance(check, _ast.LiteralCheckDefinition):
                    self.writer.write_line(
                        f'{target} = self.get_node_t({check.text!r})'
                    )
                    self.writer.write_line(
                        f'self.scanner.advance({len(check.text)})'
                    )
                else:
                    self.writer.write_line(
                        f'{target} = self.get_node_t(self.scanner.peek(1))'
                    )
                    self.writer.write_line('self.scanner.advance(1)')
            case _ast.InvokeNodeP(grammar_slot=slot):
                self.writer.write_line(
                    f'self.c_n = self.get_node_p('
                    f'self.{slot}, self.c_n, self.c_r)'
                )
            case _ast.ConditionalCheck(checks=checks, body=body):
                condition = ' or '.join(f'self.{check}()' for check in checks)
                self.writer.write_line(f'if {condition}:')
                with self.writer.increased_indent():
                    for line in body:
                        self._write_statement(parser, line)
            case _ast.Disambiguate(constraint_check=function_name):
                self.writer.write_line(f'if not self.{function_name}():')
                with self.writer.increased_indent():
                    self.writer.write_line('return  # Abort')
            case _ast.Comment(text=text):
                self.writer.write_line(f'# {text}')
            case _:
                raise ValueError(statement)

    @staticmethod
    def _resolve_target(target: _ast.NodeAssignmentTarget):
        match target:
            case _ast.NodeAssignmentTarget.CN:
                return 'self.c_n'
            case _ast.NodeAssignmentTarget.CR:
                return 'self.c_r'

    @staticmethod
    def _get_range_check(var: str, ranges: tuple[tuple[int, int], ...]) -> str:
        return ' or '.join(
            (f'{start} <= {var} <= {stop}'
             if start != stop
             else f'start == {var}')
            for start, stop in ranges
        )