"""`chalao repl`: ek interactive Hinglish shell.

Line-by-line likho aur chalao. Jo hukum block kholta hai (agar, jab tak, har,
kaam, koshish) uske baad prompt badal jaata hai jab tak `khatam` se block band
nahi hota. `madad` type karke Hinglish help; `bye` ya Ctrl-D se bahar.

(An interactive Hinglish shell. Multi-line blocks buffer until `khatam` balances.
`madad` = help, `bye` = quit.)
"""
from __future__ import annotations

from .errors import RCError
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import parse

_OPENERS = ("agar", "jab", "har", "kaam", "koshish", "sun", "action")

_HELP = """Robot Chalao REPL -- kuch hukum:
  maano x = 5                     ek cheez banao
  dikhao x                        chhaapo
  robot jodo "ur5"                robot se juro
  ghar jao                        arm ghar bhejo
  jao pose(0.4, 0.1, 0.2)         pose pe jao
  aage chalo 1 meter              base ko aage
  agar x > 3 toh ... khatam       shart
  har cup cups mein karo ... khatam   loop
  band karo                       e-stop
  madad                           yeh help
  bye                             bahar niklo
"""


def _head(line):
    """First word, with short aliases (try, bas, ...) made canonical."""
    words = line.split("#", 1)[0].split()
    return Lexer._SHORT.get(words[0], words[0]) if words else ""


def _opens_block(line):
    return _head(line) in _OPENERS


def run_repl(simulate=True, config=None):
    """REPL chalao. Default simulate=True taaki bina ROS ke bhi chale."""
    interp = Interpreter(config=config, simulate=simulate)
    print("Robot Chalao " + ("(--simulate)" if simulate else "(live)")
          + " -- 'madad' se help, 'bye' se bahar")
    buffer = []
    depth = 0
    while True:
        prompt = "chalao... " if buffer else "chalao> "
        try:
            line = input(prompt)
        except KeyboardInterrupt:
            # Ctrl-C drops a half-typed block; on an empty prompt it quits
            if buffer:
                print("\n(block chhod diya)")
                buffer, depth = [], 0
                continue
            print("\nbye!")
            return 0
        except EOFError:
            print("\nbye!")
            return 0
        stripped = line.strip()
        if not buffer and stripped in ("bye", "nikal", "exit"):
            print("bye!")
            return 0
        if not buffer and stripped == "madad":
            print(_HELP)
            continue
        if not buffer and not stripped:
            continue

        buffer.append(line)
        if _opens_block(line):
            depth += 1
        if _head(line) == "khatam" and depth > 0:
            depth -= 1
        if depth > 0:
            continue

        src = "\n".join(buffer)
        buffer = []
        try:
            prog = parse(src)
            interp.run(prog)
        except RCError as e:
            print(e)
        except Exception as e:  # noqa: BLE001
            print("Bhai, kuch gadbad: %s" % e)
