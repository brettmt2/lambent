import ast
import inspect
from typing import Callable

from errors import LambentLineDetectionError

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
        
    def _print_debug(self):
        print(f"start_stmt: {ast.unparse(self.start_stmt)}")
        print(f"end_stmt: {ast.unparse(self.end_stmt)}")
        print(f"function_def_node: {ast.unparse(self.function_def_node)}")

    def generic_visit(self, node: ast.AST):
        if self.function_def_node is None and isinstance(node, ast.FunctionDef):
            self.function_def_node = node

        for child in ast.iter_child_nodes(node):
            child._parent = node

        if isinstance(node, ast.stmt):
            if node.lineno == self.start and self.start_stmt is None:
                self.start_stmt = node

            if node.lineno == self.end and self.end_stmt is None:
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
            self._print_debug()
            raise LambentLineDetectionError(f"Statements are not on the same indentation level: {s_col}, {e_col}.")
        
    def _stmt_block_validation(self):
        block_stmts = (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef, ast.ClassDef)
        # end statement must be a non block statement
        if isinstance(self.end_stmt, block_stmts):
            self._print_debug()
            raise LambentLineDetectionError(f"End statement cannot be a block statement: (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef, ast.ClassDef).")

    def _stmt_parent_block_validation(self):
        # two statements must be in the same block
        if self.start_stmt._parent != self.end_stmt._parent:
            self._print_debug()
            raise LambentLineDetectionError("Statements must have the same parent.")

    def _validate(self):
        self.visit(self.tree)
        offset = self.function_def_node.lineno - 1
        self.start += offset
        self.end += offset
        
        self._stmt_function_index_validation() # assumes start < end and start < 2
        self._stmt_indentation_validation() # assumes start and end stmts exist
        self._stmt_block_validation() # assumes start and end stmts have same col offset
        self._stmt_parent_block_validation()  # assumes end_stmt is not a block statement
        
        return self.function_def_node, self.start_stmt, self.end_stmt
    
class StringValidatorNodeVisitor(ast.NodeVisitor):
    def __init__(self, start_str, end_str, func):
        super().__init__()
        self.start_stmt_unparsed: str = start_str
        self.end_stmt_unparsed: str = end_str
        self.start_stmt: ast.stmt = None
        self.end_stmt: ast.stmt = None
        self.func: Callable = func
        self.function_def_node: ast.FunctionDef = None
        self.start_stmt_lineno: int = None
        self.end_stmt_lineno: int = None

        source = inspect.getsource(func)
        self.tree = ast.parse(source)

    def _print_debug(self):
        print(f"start_stmt: {ast.unparse(self.start_stmt)}")
        print(f"end_stmt: {ast.unparse(self.end_stmt)}")
        print(f"function_def_node: {ast.unparse(self.function_def_node)}")

    def generic_visit(self, node: ast.AST):
        if self.function_def_node is None and isinstance(node, ast.FunctionDef):
            self.function_def_node = node

        for child in ast.iter_child_nodes(node):
            child._parent = node

        if isinstance(node, ast.stmt):
            if ast.unparse(node) == self.start_stmt_unparsed and self.start_stmt is None:
                self.start_stmt = node
                self.start_stmt_lineno = node.lineno

            if ast.unparse(node) == self.end_stmt_unparsed and self.end_stmt is None:
                self.end_stmt = node
                self.end_stmt_lineno = node.lineno
                
        return super().generic_visit(node)
    
    def _stmt_function_index_validation(self):
        if self.start_stmt is None:
            raise LambentLineDetectionError(f"Starting statement input '{self.start_stmt_unparsed}' is not found in function {self.func.__name__}.")
        if self.end_stmt is None:
            raise LambentLineDetectionError(f"Ending statement input '{self.end_stmt_unparsed}' is not found in function {self.func.__name__}.")
        
    def _stmt_position_validation(self): # validates if start <= end
        if self.end_stmt_lineno < self.start_stmt_lineno:
            raise LambentLineDetectionError("End line must be >= start.")
        if self.start_stmt_lineno < 2:
            raise LambentLineDetectionError("Start line must come after function definition.")
            
    def _stmt_block_validation(self):
        block_stmts = (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef, ast.ClassDef)
        # end statement must be a non block statement
        if isinstance(self.end_stmt, block_stmts):
            self._print_debug()
            raise LambentLineDetectionError(f"End statement cannot be a block statement: (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef, ast.ClassDef).")

    def _stmt_indentation_validation(self):
        s_col = self.start_stmt.col_offset
        e_col = self.end_stmt.col_offset

        if s_col != e_col:
            raise LambentLineDetectionError(f"Statements are not on the same indentation level: {s_col}, {e_col}.")

    def _stmt_parent_block_validation(self):
        # two statements must be in the same block
        if self.start_stmt._parent != self.end_stmt._parent:
            self._print_debug()
            raise LambentLineDetectionError("Statements must have the same parent.")

    def _validate(self):
        self.visit(self.tree)
        self._stmt_function_index_validation()
        self._stmt_position_validation() # assumes each statement was found and exists in function
        self._stmt_block_validation() # assumes start <= end
        self._stmt_indentation_validation()
        self._stmt_parent_block_validation() # assumes stmts are at the same offset
        print('successfully validated string inputs for the function')
