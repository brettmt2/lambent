from dataclasses import dataclass
from typing import Callable
import functools
import ast
from errors import LambentLineDetectionError

class LineValidatorNodeVisitor(ast.NodeVisitor):
    def __init__(self, start, end, func):
        super().__init__()
        self.start: int = start
        self.end: int = end
        self.start_stmt: ast.stmt = None
        self.end_stmt: ast.stmt = None
        self.func: Callable = func

    def generic_visit(self, node):
        if isinstance(node, ast.stmt):
            if node.lineno == self.start and self.start_stmt is None:
                self.start_stmt = node
            elif node.lineno == self.end and self.end_stmt is None:
                self.end_stmt = node
        return super().generic_visit(node)
    
    def _lineno_input_validate(self):
        if self.start_stmt is None:
            raise LambentLineDetectionError(f"Start line index out of range for {self.func.__name__}.")
        if self.end_stmt is None:
            raise LambentLineDetectionError(f"End line index out of range for {self.func.__name__}.")
        if self.start > self.end:
            raise LambentLineDetectionError(f"Start line is greater than end line for {self.func.__name__}.")

    # validate that both line end is within indent of line start
    def _lineno_instance_validate(self):
        if isinstance(self.start_stmt, ast.If):
            if self.end_stmt.col_offset != self.start_stmt.col_offset:
                raise LambentLineDetectionError(f"End line input is not within start line block")
            if self.end_stmt.lineno <= self.start_stmt.end_lineno:
                raise LambentLineDetectionError(f"End line number must be after block statement")

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