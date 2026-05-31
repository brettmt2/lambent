import ast
import inspect

from typing import Callable

class ParentBodyNodeTransformer(ast.NodeTransformer):
    def __init__(self, node: ast.FunctionDef, start_stmt: ast.stmt, end_stmt: ast.stmt, on_error: Callable, exceptions: tuple = (Exception,)):
        super().__init__()
        self.start_idx = node.body.index(start_stmt)
        self.end_idx = node.body.index(end_stmt)
        self.slice = node.body[self.start_idx:self.end_idx + 1]
        self.exceptions = exceptions

        source = inspect.getsource(on_error)
        func_def = ast.parse(source).body[0]
        self.handler_body = func_def.body

    def visit_FunctionDef(self, node: ast.FunctionDef):
        try_node = ast.Try(
            body=self.slice,
            handlers=[
                ast.ExceptHandler(
                    type=ast.Name(id='Exception', ctx=ast.Load()),
                    name='e',
                    body=self.handler_body
                )
            ],
            orelse=[],
            finalbody=[]
        )
        
        ast.copy_location(try_node, self.slice[0])
        ast.fix_missing_locations(try_node)
        node.body = node.body[:self.start_idx] + [try_node] + node.body[self.end_idx + 1:]

        return node