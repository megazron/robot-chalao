"""Robot Chalao ka lexer: source text -> tokens.

Yeh akshar-dar-akshar padhta hai aur tokens banata hai: numbers, strings,
identifiers/keywords, operators, aur har line ke ant par ek NEWLINE. `#` se
line ke ant tak comment. Har token apni line aur column yaad rakhta hai.

(Hand-written tokenizer. Keywords stay IDENT tokens; the parser matches them by
text. `#` starts a comment. Newlines are significant -- they end statements.)
"""
from __future__ import annotations

from dataclasses import dataclass

from .errors import RCSyntaxError


class TokenType:
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENT = "IDENT"
    OP = "OP"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


# Multi-char operators first so we match the longest.
_TWO = ("==", "!=", "<=", ">=")
_ONE = set("()[]{}=<>+-*/%,:.?")


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

    def __repr__(self) -> str:
        return "Token(%s, %r, L%d:C%d)" % (self.type, self.value, self.line, self.col)


class Lexer:
    """`Lexer(src).tokenize()` ek list of Token deta hai (EOF ke saath)."""

    def __init__(self, src: str):
        self.src = src
        self.i = 0
        self.line = 1
        self.col = 1
        self.depth = 0  # bracket nesting: newlines inside ( [ { are ignored
        self.tokens: list[Token] = []

    def _peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.src[j] if j < len(self.src) else ""

    def _advance(self) -> str:
        ch = self.src[self.i]
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _add(self, ttype: str, value: str, line: int, col: int) -> None:
        self.tokens.append(Token(ttype, value, line, col))

    def tokenize(self) -> list[Token]:
        while self.i < len(self.src):
            ch = self._peek()

            # comment: # ... end of line
            if ch == "#":
                while self.i < len(self.src) and self._peek() != "\n":
                    self._advance()
                continue

            # newline is significant -- except inside ( [ { where it is ignored
            if ch == "\n":
                line, col = self.line, self.col
                self._advance()
                if self.depth > 0:
                    continue
                # collapse runs of blank lines into a single NEWLINE
                if self.tokens and self.tokens[-1].type != TokenType.NEWLINE:
                    self._add(TokenType.NEWLINE, "\\n", line, col)
                continue

            # skip other whitespace (including \r and \t)
            if ch in " \t\r":
                self._advance()
                continue

            # line continuation with backslash
            if ch == "\\" and self._peek(1) == "\n":
                self._advance()
                self._advance()
                continue

            line, col = self.line, self.col

            # string
            if ch == '"':
                self.tokens.append(self._string(line, col))
                continue

            # number (a leading digit; unary minus handled by the parser)
            if ch.isdigit() or (ch == "." and self._peek(1).isdigit()):
                self.tokens.append(self._number(line, col))
                continue

            # identifier / keyword
            if ch.isalpha() or ch == "_":
                self.tokens.append(self._ident(line, col))
                continue

            # two-char operator
            two = ch + self._peek(1)
            if two in _TWO:
                self._advance()
                self._advance()
                self._add(TokenType.OP, two, line, col)
                continue

            # one-char operator
            if ch in _ONE:
                self._advance()
                if ch in "([{":
                    self.depth += 1
                elif ch in ")]}":
                    self.depth = max(0, self.depth - 1)
                self._add(TokenType.OP, ch, line, col)
                continue

            raise RCSyntaxError(
                msg_hi="yeh akshar %r samajh nahi aaya" % ch,
                hint_en="unexpected character", line=line, col=col)

        # a trailing NEWLINE makes statement parsing uniform
        if self.tokens and self.tokens[-1].type != TokenType.NEWLINE:
            self._add(TokenType.NEWLINE, "\\n", self.line, self.col)
        self._add(TokenType.EOF, "", self.line, self.col)
        return self.tokens

    def _string(self, line: int, col: int) -> Token:
        self._advance()  # opening quote
        buf = []
        while True:
            if self.i >= len(self.src):
                raise RCSyntaxError(
                    msg_hi="string band nahi hui (\" missing)",
                    hint_en="unterminated string", line=line, col=col)
            ch = self._advance()
            if ch == "\\":
                nxt = self._advance() if self.i < len(self.src) else ""
                buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                continue
            if ch == '"':
                break
            buf.append(ch)
        return Token(TokenType.STRING, "".join(buf), line, col)

    def _number(self, line: int, col: int) -> Token:
        buf = []
        seen_dot = False
        while self.i < len(self.src):
            ch = self._peek()
            if ch.isdigit():
                buf.append(self._advance())
            elif ch == "." and not seen_dot and self._peek(1).isdigit():
                seen_dot = True
                buf.append(self._advance())
            else:
                break
        return Token(TokenType.NUMBER, "".join(buf), line, col)

    def _ident(self, line: int, col: int) -> Token:
        buf = []
        while self.i < len(self.src):
            ch = self._peek()
            if ch.isalnum() or ch == "_":
                buf.append(self._advance())
            else:
                break
        return Token(TokenType.IDENT, "".join(buf), line, col)


def tokenize(src: str) -> list[Token]:
    """Chhota helper: source string -> tokens."""
    return Lexer(src).tokenize()
