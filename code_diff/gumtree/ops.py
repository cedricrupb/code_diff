from dataclasses import dataclass
from typing import Any, Tuple

@dataclass
class EditOperation:
    target_node: Any

@dataclass
class Update(EditOperation):
    value: Any

@dataclass
class Insert(EditOperation):
    node: Tuple[str, Any]
    position: int

@dataclass
class Move(EditOperation):
    node: Any
    position: int

@dataclass
class Delete(EditOperation):
    pass