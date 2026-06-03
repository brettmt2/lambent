from validator import LineValidatorNodeVisitor
from transformer import ParentBodyNodeTransformer

from typing import Callable
import ast
import sys

class Lambent():
    def inject(self, func: Callable, start: int, end: int, on_error: Callable, exceptions: tuple = (Exception,)):
        validator = LineValidatorNodeVisitor(start=start, end=end, func=func)
        function_def_node, start_stmt, end_stmt = validator._validate()

        transformer = ParentBodyNodeTransformer(node=function_def_node,
                                                     start_stmt=start_stmt, 
                                                     end_stmt=end_stmt,
                                                     on_error=on_error)        

        new_tree = transformer.visit(validator.tree)
        ast.fix_missing_locations(new_tree)
        new_source = ast.unparse(new_tree)

        namespace = sys._getframe(1).f_globals
        exec(new_source, namespace)
        return namespace[func.__name__]