from dataclasses import dataclass
from typing import Callable
import functools
import ast

class LineDetectionNodeVisitor(ast.NodeVisitor):
    def __init__(self, start, end):
        super().__init__()
        self.start: int = start
        self.end: int = end
        self.start_stmt_expr: ast.stmt | ast.expr = None
        self.end_stmt_expr: ast.stmt | ast.expr = None

    def generic_visit(self, node):
        if isinstance(node, ast.expr) or isinstance(node, ast.stmt):
            if node.lineno == self.start:
                self.start_stmt_expr = node
            elif node.lineno == self.end:
                self.end_stmt_expr = node
        return super().generic_visit(node)


@dataclass
class Handler:
    on_error: Callable
    exceptions: tuple = (Exception, )

    def __call__(self, func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                return self.on_error(e)
        return wrapper