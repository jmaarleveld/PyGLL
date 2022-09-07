##############################################################################
##############################################################################
# Imports
##############################################################################

from __future__ import annotations

import abc
import ast
import contextlib
import enum
import io
import dataclasses
import typing

##############################################################################
# Scope
##############################################################################


class ScopeType(enum.Enum):
    Module = enum.auto()
    Function = enum.auto()
    Class = enum.auto()
    Conditional = enum.auto()


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Scope:
    scope_type: ScopeType
    metadata: dict[str, typing.Any]
    body: list[CodeObject]

##############################################################################
# Code Objects - Statements
##############################################################################


class CodeObject:
    pass


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class ClassDefinition(CodeObject):
    name: str
    bases: list[str]
    doc_string: str
    body: list[CodeObject]


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class FunctionDefinition(CodeObject):
    name: str
    arguments: dict[str, str | None]
    doc_string: str
    body: list[CodeObject]


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Conditional(CodeObject):
    conditions: list[Expression]
    bodies: list[list[CodeObject]]
    else_body: list[CodeObject] | None = None


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class _ConditionalMarker(CodeObject):
    condition: Expression | None
    is_else: bool


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Import(CodeObject):
    location: str
    name: str


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Assignment(CodeObject):
    name: str
    value: Expression


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class FunctionCall(CodeObject):
    name: str
    arguments: list[Expression]


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Return(CodeObject):
    value: Expression


##############################################################################
# Code Objects - Expressions
##############################################################################


@dataclasses.dataclass(eq=False, frozen=True, slots=True)
class Expression:
    tree: dict[str, dict | str]

    @classmethod
    def from_source(cls, source: str) -> typing.Self:
        tree = ast.parse(source)
        assert len(tree.body) == 1
        return cls.from_ast(tree.body[0])

    @classmethod
    def from_ast(cls, tree: ast.AST) -> typing.Self:
        return cls(cls.__parse_recursive(tree))

    @classmethod
    def __parse_recursive(cls, node: ast.AST):
        match node:
            case ast.Expr(value=value):
                return cls.__parse_recursive(value)
            case ast.Attribute(value=value, attr=attr):
                return {
                    'type': 'attribute_lookup',
                    'target': cls.__parse_recursive(value),
                    'attribute': attr
                }
            case ast.Name(id=name):
                return {
                    'type': 'load_name',
                    'name': name
                }
            case ast.Constant(value=value):
                return {'type': 'constant', 'value': repr(value)}
            case ast.BinOp(left=left, op=op, right=right):
                return {
                    'type': 'binary_operation',
                    'left': cls.__parse_recursive(left),
                    'right': cls.__parse_recursive(right),
                    'operation': cls.__parse_operator(op)
                }
            case ast.Compare(left=left, ops=ops, comparators=comparators):
                assert len(ops) == 1
                assert len(comparators) == 1
                return {
                    'type': 'binary_operation',
                    'left': cls.__parse_recursive(left),
                    'right': cls.__parse_recursive(comparators[0]),
                    'operation': cls.__parse_operator(ops[0])
                }
            case ast.BoolOp(op=op, values=values):
                return cls.__make_binary_recursive(values,
                                                   cls.__parse_operator(op))
            case ast.UnaryOp(op=op, operand=operand):
                return {
                    'type': 'unary_operation',
                    'operand': cls.__parse_recursive(operand),
                    'operation': cls.__parse_operator(op)
                }
            case ast.Call(func=name, args=args):
                full_name = cls.__parse_recursive(name)
                args = [cls.__parse_recursive(arg) for arg in args]
                return {'type': 'function_call',
                        'name': full_name,
                        'arguments': args}
            case ast.Tuple(elts=elements):
                return {'type': 'tuple',
                        'elements': [cls.__parse_recursive(el)
                                     for el in elements]}
            case _:
                raise NotImplementedError(f'{node!r}')

    @classmethod
    def __make_binary_recursive(cls, nodes, operator):
        if len(nodes) == 2:
            return {
                'type': 'binary_operation',
                'left': cls.__parse_recursive(nodes[0]),
                'right': cls.__parse_recursive(nodes[1]),
                'operation': operator
            }
        return {
            'type': 'binary_operation',
            'left': cls.__parse_recursive(nodes[0]),
            'right': cls.__make_binary_recursive(nodes[1:], operator),
            'operation': operator
        }

    @classmethod
    def __parse_operator(cls, node: ast.AST) -> str:
        match node:
            case ast.Add():
                return 'add'
            case ast.Sub():
                return 'sub'
            case ast.Mult():
                return 'mul'
            case ast.Not():
                return 'not'
            case ast.Eq():
                return 'eq'
            case ast.Or():
                return 'logical_or'
            case ast.And():
                return 'logical_and'


##############################################################################
##############################################################################
# Writer class
##############################################################################


class CodeWriter:

    def __init__(self, stream: io.TextIOBase):
        self.__stream = stream
        self.__indent = 0

    def write(self, text: str, *, newline=True, indent=None):
        if newline:
            text += '\n'
        if indent is None:
            indent = self.__indent
        text = '    '*indent + text
        self.__stream.write(text)

    def write_blank(self):
        self.__stream.write('\n')

    @contextlib.contextmanager
    def increased_indent(self):
        self.__indent += 1
        yield
        self.__indent -= 1


##############################################################################
# Abstract Code Generator
##############################################################################


class AbstractCodeGenerator(abc.ABC):

    def __init__(self):
        self.__scopes = [Scope(ScopeType.Module, {}, [])]

    ###################################################################
    # Class Definitions

    @contextlib.contextmanager
    def define_class(self,
                     name: str,
                     bases: list[str],
                     doc_string: str = None):
        scope = Scope(scope_type=ScopeType.Class,
                      metadata={'name': name,
                                'bases': bases,
                                'doc': doc_string if doc_string else ''},
                      body=[])
        self.__scopes.append(scope)
        yield
        assert self.__scopes[-1] is scope, self.__scopes[-1]
        del self.__scopes[-1]
        definition = ClassDefinition(
            name=scope.metadata['name'],
            bases=scope.metadata['bases'],
            doc_string=scope.metadata['doc'],
            body=scope.body
        )
        self.__scopes[-1].body.append(definition)

    ###################################################################
    # Functions Definitions

    @contextlib.contextmanager
    def define_function(self,
                        name: str,
                        arguments: dict[str, str | None],
                        doc_string: str = None):
        scope = Scope(scope_type=ScopeType.Function,
                      metadata={'name': name,
                                'args': arguments,
                                'doc': doc_string if doc_string else ''},
                      body=[])
        self.__scopes.append(scope)
        yield
        assert self.__scopes[-1] is scope, self.__scopes[-1]
        del self.__scopes[-1]
        definition = FunctionDefinition(
            name=scope.metadata['name'],
            arguments=scope.metadata['args'],
            doc_string=scope.metadata['doc'],
            body=scope.body
        )
        self.__scopes[-1].body.append(definition)

    ###################################################################
    # Conditionals

    @contextlib.contextmanager
    def define_conditional(self):
        scope = Scope(scope_type=ScopeType.Conditional,
                      metadata={},
                      body=[])
        self.__scopes.append(scope)
        yield
        assert self.__scopes[-1] is scope, self.__scopes[-1]
        del self.__scopes[-1]
        (markers,
         bodies,
         else_body) = self.__extract_conditions_and_bodies_from_scope(scope)
        definition = Conditional(
            conditions=[marker.condition for marker in markers],
            bodies=bodies,
            else_body=else_body
        )
        self.__scopes[-1].body.append(definition)

    @staticmethod
    def __extract_conditions_and_bodies_from_scope(scope: Scope):
        if not isinstance(scope.body[0], _ConditionalMarker):
            raise ValueError('Expected conditional marker at index 0')
        markers = [scope.body[0]]
        bodies = []
        current_body = []
        found_else = False
        for item in scope.body[1:]:
            if isinstance(item, _ConditionalMarker):
                if found_else:
                    raise ValueError('Cannot have conditional after else')
                bodies.append(current_body)
                if not item.is_else:
                    markers.append(item)
                current_body = []
                found_else = item.is_else
            else:
                current_body.append(item)
        bodies.append(current_body)
        if found_else:
            else_body = bodies[-1]
            bodies = bodies[:-1]
        else:
            else_body = None
        return markers, bodies, else_body

    @contextlib.contextmanager
    def if_statement(self, condition: str):
        self.__scopes[-1].body.append(
            _ConditionalMarker(is_else=False,
                               condition=Expression.from_source(condition))
        )
        try:
            yield
        finally:
            pass

    @contextlib.contextmanager
    def else_statement(self):
        self.__scopes[-1].body.append(
            _ConditionalMarker(is_else=True, condition=None)
        )
        try:
            yield
        finally:
            pass

    ###################################################################
    # Misc

    def define_import(self, location: str, name: str):
        self.__scopes[-1].body.append(Import(location=location, name=name))

    def assign(self, name: str, value: str):
        expr = Expression.from_source(value)
        self.__scopes[-1].body.append(Assignment(name=name, value=expr))

    def call_function(self, name: str, args: list[str]):
        parsed_args = [Expression.from_source(arg) for arg in args]
        self.__scopes[-1].body.append(FunctionCall(name=name,
                                                   arguments=parsed_args))

    def return_value(self, expr: str):
        parsed = Expression.from_source(expr)
        self.__scopes[-1].body.append(Return(parsed))

    ###################################################################
    # Code Generation Methods

    def write_code_to_file(self, filename: str):
        assert len(self.__scopes) == 1
        with open(filename, 'w') as file:
            writer = CodeWriter(file)
            self.generate_body(self.__scopes[-1].body, writer)

    def generate_body(self, body: list[CodeObject], writer: CodeWriter):
        for item in body:
            self.__dispatch_generation(item, writer)

    def __dispatch_generation(self, obj: CodeObject, writer: CodeWriter):
        match obj:
            case FunctionDefinition(_, _, _, _) as func:
                self.generate_function(func, writer)
            case ClassDefinition(_, _, _, _) as cls:
                self.generate_class(cls, writer)
            case Conditional(_, _, _) as cond:
                self.generate_conditional(cond, writer)
            case Import(_, _) as imp:
                self.generate_import(imp, writer)
            case Assignment(_, _) as assign:
                self.generate_assignment(assign, writer)
            case FunctionCall(_, _) as call:
                self.generate_function_call(call, writer)
            case Return(_) as ret:
                self.generate_return(ret, writer)
            case _ as other:
                raise ValueError(f'Unsupported code object: {other}')

    @abc.abstractmethod
    def generate_class(self,
                       definition: ClassDefinition,
                       writer: CodeWriter):
        pass

    @abc.abstractmethod
    def generate_function(self,
                          definition: FunctionDefinition,
                          writer: CodeWriter):
        pass

    @abc.abstractmethod
    def generate_conditional(self,
                             definition: Conditional,
                             writer: CodeWriter):
        pass

    @abc.abstractmethod
    def generate_import(self,
                        import_statement: Import,
                        writer: CodeWriter):
        pass

    @abc.abstractmethod
    def generate_assignment(self,
                            assignment: Assignment,
                            writer: CodeWriter):
        pass

    @abc.abstractmethod
    def generate_function_call(self,
                               function_call: FunctionCall,
                               writer: CodeWriter):
        pass

    @abc.abstractmethod
    def generate_return(self, ret: Return, writer: CodeWriter):
        pass

    @abc.abstractmethod
    def generate_expression(self, exp: Expression) -> str:
        pass


##############################################################################
# Python Code Generator
##############################################################################


class PythonCodeGenerator(AbstractCodeGenerator):

    OPERATOR_MAP = {
        'add': '+',
        'sub': '-',
        'mul': '*',
        'div': '/',
        'mod': '%',
        'pow': '**',
        'eq': '==',
        'ne': '!=',
        'logical_and': 'and',
        'logical_or': 'or',
        'logical_not': 'not'
    }

    def generate_class(self,
                       definition: ClassDefinition,
                       writer: CodeWriter):
        bases = ', '.join(definition.bases)
        writer.write_blank()
        writer.write_blank()
        writer.write(f'class {definition.name}({bases}):')
        with writer.increased_indent():
            writer.write(f'"""{definition.doc_string}"""')
            self.generate_body(definition.body, writer)

    def generate_function(self,
                          definition: FunctionDefinition,
                          writer: CodeWriter):
        args = ', '.join(
            f'{name}: {data_type}' if data_type is not None else name
            for name, data_type in definition.arguments.items()
        )
        writer.write_blank()
        writer.write(f'def {definition.name}({args}):')
        with writer.increased_indent():
            writer.write(f'"""{definition.doc_string}"""')
            self.generate_body(definition.body, writer)

    def generate_conditional(self,
                             definition: Conditional,
                             writer: CodeWriter):
        statements = ['if'] + ['elif']*(len(definition.conditions) - 1)
        iterator = zip(statements, definition.conditions, definition.bodies)
        for statement, condition, body in iterator:
            cond = self.generate_expression(condition.tree)
            writer.write(f'{statement} {cond}:')
            with writer.increased_indent():
                self.generate_body(body, writer)
        if definition.else_body is not None:
            writer.write('else:')
            with writer.increased_indent():
                self.generate_body(definition.else_body, writer)

    def generate_import(self, import_statement: Import, writer: CodeWriter):
        writer.write(
            f'from {import_statement.location} import {import_statement.name}'
        )

    def generate_assignment(self, assignment: Assignment, writer: CodeWriter):
        expr = self.generate_expression(assignment.value.tree)
        writer.write(f'{assignment.name} = {expr}')

    def generate_function_call(self,
                               function_call: FunctionCall,
                               writer: CodeWriter):
        arguments = ", ".join(self.generate_expression(arg.tree)
                              for arg in function_call.arguments)
        writer.write(f'{function_call.name}({arguments})')

    def generate_return(self, ret: Return, writer: CodeWriter):
        expr = self.generate_expression(ret.value.tree)
        writer.write(f'return {expr}')

    def generate_expression(self, tree: dict) -> str:
        match tree:
            case {'type': 'attribute_lookup',
                  'target': target,
                  'attribute': attribute}:
                return f'{self.generate_expression(target)}.{attribute}'
            case {'type': 'load_name', 'name': name}:
                return name
            case {'type': 'constant', 'value': value}:
                return value
            case {'type': 'binary_operation',
                  'left': left,
                  'right': right,
                  'operation': operator}:
                return (f'({self.generate_expression(left)} '
                        f'{self.OPERATOR_MAP[operator]} '
                        f'{self.generate_expression(right)})')
            case {'type': 'unary_operation',
                  'operand': operand,
                  'operation': operator}:
                return (f'({self.OPERATOR_MAP[operator]} '
                        f'{self.generate_expression(operand)})')
            case {'type': 'function_call', 'name': name, 'arguments': args}:
                arguments = ", ".join(self.generate_expression(arg)
                                      for arg in args)
                return f'{self.generate_expression(name)}({arguments})'
            case {'type': 'tuple', 'elements': elements}:
                formatted = ', '.join(self.generate_expression(el)
                                      for el in elements)
                if len(elements) == 1:
                    formatted += ','
                return f'({formatted})'
            case _:
                raise ValueError(f'Unsupported expression: {tree}')
