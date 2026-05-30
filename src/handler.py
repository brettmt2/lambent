from dataclasses import dataclass
from typing import Callable
import functools
import ast
from errors import LambentLineDetectionError
import inspect

class LineValidatorNodeVisitor(ast.NodeVisitor):
    def __init__(self, start, end, func):
        if end < start:
            raise LambentLineDetectionError("End line must be >= start.")
        if start < 2:
            raise LambentLineDetectionError("Start line must come after function definition.")
        
        super().__init__()
        self.start: int = start
        self.end: int = end
        self.start_stmt: ast.stmt = None
        self.end_stmt: ast.stmt = None
        self.func: Callable = func
        self.function_def_node: ast.FunctionDef = None

        source = inspect.getsource(func)
        self.tree = ast.parse(source)
        self._validate()

    def generic_visit(self, node: ast.AST):
        if self.function_def_node is None and isinstance(node, ast.FunctionDef):
            self.function_def_node = node

        if isinstance(node, ast.stmt):
            if node.lineno == self.start:
                self.start_stmt = node
            
            if node.lineno == self.end:
                self.end_stmt = node
                
        return super().generic_visit(node)
    
    def _stmt_function_index_validation(self):
        if self.start_stmt is None:
            raise LambentLineDetectionError(f"Starting lineno input {self.start} is not in range of function {self.func.__name__} ({self.function_def_node.end_lineno} lines).")
        if self.end_stmt is None:
            raise LambentLineDetectionError(f"Ending lineno input {self.end} is not in range of function {self.func.__name__} ({self.function_def_node.end_lineno} lines).")   
    
    def _stmt_indentation_validation(self):
        s_col = self.start_stmt.col_offset
        e_col = self.end_stmt.col_offset

        if s_col != e_col:
            raise LambentLineDetectionError(f"Statements are not on the same indentation level: {s_col}, {e_col}.")
        
    def _validate(self):
        self.visit(self.tree)
        self._stmt_function_index_validation()
        self._stmt_indentation_validation()

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