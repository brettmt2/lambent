from dataclasses import dataclass
from typing import Callable

@dataclass
class Lambent:
    on_error: Callable
    exceptions: tuple = (Exception, )

