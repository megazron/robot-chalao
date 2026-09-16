import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from robot_chalao.errors import RCSyntaxError            # noqa: E402
from robot_chalao.lexer import TokenType, tokenize        # noqa: E402


def types(src):
    return [t.type for t in tokenize(src) if t.type != TokenType.NEWLINE][:-1]


def test_number_int_and_float():
    toks = [t for t in tokenize("5 3.14") if t.type == TokenType.NUMBER]
    assert [t.value for t in toks] == ["5", "3.14"]


def test_string_with_escape():
    toks = [t for t in tokenize('"hi \\"there\\""') if t.type == TokenType.STRING]
    assert toks[0].value == 'hi "there"'


def test_comment_is_skipped():
    toks = tokenize("maano x = 5  # this is a note\n")
    assert all("note" not in t.value for t in toks)


def test_two_char_operators():
    ops = [t.value for t in tokenize("a == b != c <= d >= e") if t.type == TokenType.OP]
    assert ops == ["==", "!=", "<=", ">="]


def test_line_and_col_tracked():
    toks = tokenize("maano\nx")
    assert toks[0].line == 1
    xtok = [t for t in toks if t.value == "x"][0]
    assert xtok.line == 2


def test_newline_between_statements():
    toks = tokenize("dikhao 1\ndikhao 2\n")
    assert sum(1 for t in toks if t.type == TokenType.NEWLINE) == 2


def test_newlines_ignored_inside_brackets():
    src = "maano p = [\n1,\n2,\n3\n]\n"
    nl = sum(1 for t in tokenize(src) if t.type == TokenType.NEWLINE)
    assert nl == 1  # only the final one, not the ones inside [ ]


def test_bad_character_is_hinglish_error():
    with pytest.raises(RCSyntaxError) as e:
        tokenize("maano x = @")
    assert "Bhai" in str(e.value)


def test_unterminated_string():
    with pytest.raises(RCSyntaxError):
        tokenize('dikhao "open')


def test_eof_token_present():
    assert tokenize("x")[-1].type == TokenType.EOF
