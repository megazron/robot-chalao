"""Robot Chalao ki galtiyan, Hinglish mein.

Har error line/column yaad rakhta hai, ek Hinglish sandesh (`msg_hi`) deta hai,
aur bracket mein ek chhota English hint (`hint_en`) taaki naye programmer ko
samajh aaye. `__str__` sabko jodta hai: "Bhai, line 12: ... (hint)".

(Every error carries a line/col, a Hinglish message and a short English hint.)
"""
from __future__ import annotations


class RCError(Exception):
    """Sabhi Robot Chalao galtiyon ka baap (base of every error)."""

    def __init__(self, msg_hi: str, hint_en: str = "",
                 line: int | None = None, col: int | None = None):
        self.msg_hi = msg_hi
        self.hint_en = hint_en
        self.line = line
        self.col = col
        super().__init__(self.__str__())

    def __str__(self) -> str:
        where = "" if self.line is None else "line %d: " % self.line
        hint = " (%s)" % self.hint_en if self.hint_en else ""
        return "Bhai, %s%s%s" % (where, self.msg_hi, hint)


class RCSyntaxError(RCError):
    """Lexer ko koi akshar samajh nahi aaya (bad character / token)."""


class RCParseError(RCError):
    """Vyakaran galat hai -- kuchh missing ya galat jagah (grammar error)."""


class RCRuntimeError(RCError):
    """Chalte waqt kuchh galat ho gaya (runtime failure)."""


class RCNameError(RCError):
    """Aisi cheez use ki jo banayi hi nahi (undefined name)."""


class RCTypeError(RCError):
    """Galat kism ki cheez di gayi (wrong type)."""


class RCBackendError(RCError):
    """Backend yeh kaam nahi kar sakta (backend cannot do this)."""


class RCRosMissing(RCBackendError):
    """ROS 2 ya uska plugin install nahi hai (ROS not available).

    Iska matlab: `--simulate` chalao, ya ROS 2 setup source karo."""
