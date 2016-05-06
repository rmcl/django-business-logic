# -*- coding: utf-8 -*-
#

from .. import signals
from .log import Logger
from .frame import Frame
from .node import Node, NodeCacheHolder
from .result import Result
from .variable import Variable, VariableDefinition


class ContextConfig:
    defaults = dict(
            logging=False,
            debug=False,
            cache=True,
            )

    def __init__(self, **kwargs):
        for k, v in self.defaults.items():
            kwargs.setdefault(k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)


class Context(NodeCacheHolder):
    def __init__(self, **kwargs):
        self.config = ContextConfig(**kwargs)
        self.result = Result()
        self.result.save()
        self._vars = {}
        self.frames = []

        signals.block_interpret_enter.connect(self.block_interpret_enter,
                sender=self)
        signals.block_interpret_leave.connect(self.block_interpret_leave,
                sender=self)

        signals.interpret_enter.connect(self.interpret_enter,
                sender=self)
        signals.interpret_leave.connect(self.interpret_leave,
                sender=self)

        self.logger = Logger()
        if self.config.logging:
            signals.interpret_enter.connect(self.logger.interpret_enter,
                    sender=self)
            signals.interpret_leave.connect(self.logger.interpret_leave,
                    sender=self)

    def _frame(self):
        if not self.frames:
            return None
        return self.frames[-1]

    frame = property(_frame)

    def block_interpret_enter(self, **kwargs):
        self.frames.append(Frame())

    def block_interpret_leave(self, **kwargs):
        self.frames.pop()

    def single_statement_interpret_leave(self, **kwargs):
        node = kwargs['node']
        if node == self._single_statement_node:
            self.frames.pop()

    def interpret_enter(self, **kwargs):
        if not self.frames:
            node = kwargs['node']
            self._single_statement_node = node
            signals.interpret_leave.connect(self.single_statement_interpret_leave,
                sender=self)
            self.frames.append(Frame())

    def interpret_leave(self, **kwargs):
        pass

    def get_children(self, node):
        if not self.config.cache:
            return node.get_children().all()

        return super(Context, self).get_children(node)

    def get_variable(self, variable_definition):
        assert isinstance(variable_definition, VariableDefinition)

        if variable_definition.name.find('.') == -1:
            try:
                return self._vars[variable_definition.name]
            except KeyError:
                return Variable.Undefined()

        attrs = variable_definition.name.split('.')

        try:
            current = self._vars[attrs[0]]
        except KeyError:
            return Variable.Undefined()

        for attr in attrs[1:]:
            try:
                current = getattr(current, attr)
            except AttributeError:
                return Variable.Undefined()

        return current

    def set_variable(self, variable_definition, value):
        assert isinstance(variable_definition, VariableDefinition)
        self._vars[variable_definition.name] = value

__all__ = ('Context', )
