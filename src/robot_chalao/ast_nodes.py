"""Robot Chalao ke AST nodes (abstract syntax tree).

Parser in nodes ka ped banata hai; interpreter aur transpiler ise ghoomte hain.
Har node apni source line yaad rakhta hai taaki galti ki jagah bata sake.

(The parser builds a tree of these; the interpreter and transpiler walk it.
Every node remembers its source line for error messages.)
"""
from __future__ import annotations

from dataclasses import dataclass, field


# --------------------------------------------------------------- statements
@dataclass
class Program:
    body: list
    line: int = 0


@dataclass
class Let:
    name: str
    expr: object
    line: int = 0


@dataclass
class Print:
    exprs: list
    line: int = 0


@dataclass
class Return:
    expr: object | None
    line: int = 0


@dataclass
class ExprStmt:
    expr: object
    line: int = 0


@dataclass
class If:
    cond: object
    then: list
    orelse: list  # empty list if no `warna`
    line: int = 0


@dataclass
class While:
    cond: object
    body: list
    line: int = 0


@dataclass
class ForEach:
    var: str
    iterable: object
    body: list
    line: int = 0


@dataclass
class FuncDef:
    name: str
    params: list
    body: list
    line: int = 0


@dataclass
class Try:
    body: list
    err_name: str | None
    handler: list
    line: int = 0


@dataclass
class Import:
    path: str
    line: int = 0


@dataclass
class Break:
    line: int = 0


@dataclass
class Timer:
    period: object
    unit: str
    body: list
    line: int = 0


@dataclass
class Subscribe:
    topic: object
    type_name: str
    var: str
    body: list
    line: int = 0


@dataclass
class ActionSend:
    name: object
    goal: object
    progress_var: str | None
    body: list
    line: int = 0


# --------------------------------------------------------------- expressions
@dataclass
class Num:
    value: float
    line: int = 0


@dataclass
class Str:
    value: str
    line: int = 0


@dataclass
class Bool:
    value: bool
    line: int = 0


@dataclass
class Ident:
    name: str
    line: int = 0


@dataclass
class ListLit:
    items: list
    line: int = 0


@dataclass
class DictLit:
    pairs: list  # list of (key_expr, value_expr)
    line: int = 0


@dataclass
class Call:
    name: str
    args: list
    line: int = 0


@dataclass
class Member:
    obj: object
    attr: str
    line: int = 0


@dataclass
class BinOp:
    op: str
    left: object
    right: object
    line: int = 0


@dataclass
class UnaryOp:
    op: str
    operand: object
    line: int = 0


@dataclass
class TypedCtor:
    kind: str  # "pose" | "twist" | "joints"
    args: list
    line: int = 0


@dataclass
class RobotCommand:
    """Har Hinglish robot hukum yahin aakar rukta hai.

    `method` bilkul ek Backend method ka naam hai, `args` uske kwargs,
    `selector` (optional) kaunsa robot (multi-robot ke liye)."""

    method: str
    args: dict = field(default_factory=dict)
    selector: str | None = None
    line: int = 0
