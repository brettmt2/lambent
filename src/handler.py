from dataclasses import dataclass
from typing import Callable
import functools

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