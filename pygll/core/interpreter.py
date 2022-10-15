import typing

from . import base as _base
from . import nodes as _nodes
from .nodes import GrammarSlot
from ..generator import abstract_parser as _ast


class DynamicParser(typing.Protocol):
    def __call__(self, text: str, **kwargs) -> _base.AbstractParser:
        pass


def build_dynamic_parser(
        parser: _ast.ParserDefinition) -> DynamicParser:
    def dynamic_parser(text, **kwargs) -> _base.AbstractParser:
        return _InterpretedParser(parser, text, **kwargs)
    return dynamic_parser


class _InterpretedParser(_base.AbstractParser):

    def __init__(self,
                 definition: _ast.ParserDefinition,
                 text: str,
                 **kwargs):
        self.__def = definition
        self.__checks_by_slot = {}
        for name, check in definition.ambiguity_checks.items():
            if not check.as_pop_check():
                continue
            slot = self.__definition_to_slot(self.__def.grammar_slots[check.slot])
            self.__checks_by_slot.setdefault(slot, []).append(
                lambda *args, _c=name: self.__emulate_pop_check(*args, _c)
            )
        # Invoke the parser
        super().__init__(text, **kwargs)

    def goto(self, slot: GrammarSlot):
        name = self.__slot_to_name(slot)
        function_name = self.__def.goto[name]
        self.goto_name(function_name)

    def goto_name(self, name: str):
        function = self.__def.parse_functions[name]
        self.__emulate_function(function)

    def __emulate_function(self, function: _ast.FunctionDefinition):
        self.__emulate(function.body)

    def __emulate(self, instructions: list[_ast.StatementDefinition]):
        for instruction in instructions:
            match instruction:
                case _ast.Disambiguate(constraint_check=function_name):
                    result = self.__emulate_disambiguation_check(function_name)
                    if not result:
                        return  # Abort
                case _ast.ConditionalCheck(checks=checks, body=body):
                    check_results = (self.__emulate_input_check(check)
                                     for check in checks)
                    if any(check_results):
                        self.__emulate(body)
                case _ast.InvokeNodeT(parent_check=check_name, target=target):
                    check = self.__def.input_checks[check_name]
                    if isinstance(check, _ast.LiteralCheckDefinition):
                        if target == _ast.NodeAssignmentTarget.CN:
                            self.c_n = self.get_node_t(check.text)
                        else:
                            self.c_r = self.get_node_t(check.text)
                        self.scanner.advance(len(check.text))
                    else:
                        if target == _ast.NodeAssignmentTarget.CN:
                            self.c_n = self.get_node_t(self.scanner.peek())
                        else:
                            self.c_r = self.get_node_t(self.scanner.peek())
                        self.scanner.advance(1)
                case _ast.InvokeNodeP(target=target, grammar_slot=slot_name):
                    slot_definition = self.__def.grammar_slots[slot_name]
                    slot = self.__definition_to_slot(slot_definition)
                    if target == _ast.NodeAssignmentTarget.CN:
                        self.c_n = self.get_node_p(slot, self.c_n, self.c_r)
                    else:
                        assert False
                case _ast.InvokeCreate(grammar_slot=slot_name):
                    slot_definition = self.__def.grammar_slots[slot_name]
                    slot = self.__definition_to_slot(slot_definition)
                    self.c_u = self.create(slot)
                case _ast.InvokeAdd(grammar_slot=slot_name):
                    slot_definition = self.__def.grammar_slots[slot_name]
                    slot = self.__definition_to_slot(slot_definition)
                    self.add(slot, self.c_u, self.scanner.position, _nodes.InitialNode(0, 0))
                case _ast.CallFunction(function=function_name):
                    self.goto_name(function_name)
                case _ast.InvokePop():
                    self.pop()
                case _:
                    raise NotImplementedError(
                        f'Unknown parser instruction: {instruction.__class__.__name__}'
                    )

    def __emulate_input_check(self, check_name: str) -> bool:
        check = self.__def.input_checks[check_name]
        match check:
            case _ast.LiteralCheckDefinition(text=text):
                return self.scanner.has_next(text)
            case _ast.RangeCheckDefinition(ranges=ranges):
                char = self.scanner.peek(1)
                for start, stop in ranges:
                    if start <= char <= stop:
                        return True
                return False
            case _:
                raise NotImplementedError(
                    f'Invalid input check: {check.__class__.__name__}'
                )

    def __emulate_disambiguation_check(self, check_name: str) -> bool:
        check = self.__def.ambiguity_checks[check_name]
        match check:
            case _ast.PrecedeCheck(slot, literals, ranges, negated):
                return self.__emulate_range_or_literal_check(
                    ranges, literals, negated, self.scanner.peek_backward
                )
            case _ast.FollowCheck(slot, literals, ranges, negated, pop_check):
                if pop_check:
                    raise NotImplementedError
                return self.__emulate_range_or_literal_check(
                    ranges, literals, negated, self.scanner.peek_forward
                )
            case _ast.RestrictionCheck(slot, literals, ranges):
                raise NotImplementedError
            case _:
                raise ValueError(
                    f'Unknown disambiguation check: {check.__class__.__name__}'
                )

    def __emulate_pop_check(self, start, stop, check_name: str):
        check = self.__def.ambiguity_checks[check_name]
        match check:
            case _ast.FollowCheck(slot, literals, ranges, negated, True):
                return self.__emulate_range_or_literal_check(ranges,
                                                             literals,
                                                             negated,
                                                             self.scanner.peek_forward)
            case _ast.RestrictionCheck(slot, literals, ranges):
                raise NotImplementedError
            case _:
                raise ValueError(
                    f'Unknown disambiguation check: {check.__class__.__name__}'
                )

    @staticmethod
    def __emulate_range_or_literal_check(ranges,
                                         literals,
                                         negated,
                                         peek_function) -> bool:
        char = peek_function(1)
        for start, stop in ranges:
            if start <= char <= stop:
                return not negated
        literals_by_length = {}
        for literal in literals:
            literals_by_length.setdefault(len(literal), set()).add(literal)
        for length, literals_with_length in literals_by_length.items():
            if peek_function(length) in literals_with_length:
                return not negated
        return negated

    def get_ambiguity_checks_for_slot(self, slot: GrammarSlot):
        return self.__checks_by_slot.get(slot, [])

    def get_initial_slot(self) -> GrammarSlot:
        key = self.__def.initial_grammar_slot_start
        definition = self.__def.grammar_slots[key]
        return self.__definition_to_slot(definition)

    def get_final_slot(self) -> GrammarSlot:
        key = self.__def.initial_grammar_slot_end
        definition = self.__def.grammar_slots[key]
        return self.__definition_to_slot(definition)

    @staticmethod
    def __definition_to_slot(definition: _ast.GrammarSlotDefinition):
        return _nodes.GrammarSlot(
            nonterminal=definition.nonterminal,
            alternate=definition.alternate,
            position=definition.position,
            alpha_is_special=definition.alpha,
            beta_is_special=definition.beta
        )

    @staticmethod
    def __slot_to_name(slot: _nodes.GrammarSlot) -> str:
        return _ast.GrammarSlotDefinition.get_slot_name(
            slot.nonterminal,
            slot.alternate,
            slot.position,
            is_initial=slot.alternate < 0
        )
