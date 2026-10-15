"""Stage 1 - LEXER: turns source text into a list of tokens."""
import re
from collections import namedtuple
from .errors import TinyError

Token = namedtuple("Token", "kind value line")

KEYWORDS = {"let", "fn", "if", "else", "while", "return",
            "true", "false", "and", "or", "not"}

SPEC = re.compile(r"""
 (?P<COMMENT>//[^\n]*)
|(?P<NUMBER>\d+(?:\.\d+)?)
|(?P<STRING>"(?:\\.|[^"\\\n])*")
|(?P<IDENT>[A-Za-z_]\w*)
|(?P<OP>==|!=|<=|>=|[+\-*/%<>=(){},;])
|(?P<NEWLINE>\n)
|(?P<SKIP>[ \t\r]+)
|(?P<BAD>.)
""", re.X)

ESC = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def tokenize(src):
    tokens, line = [], 1
    for m in SPEC.finditer(src):
        kind, text = m.lastgroup, m.group()
        if kind == "NEWLINE":
            line += 1
        elif kind in ("SKIP", "COMMENT"):
            continue
        elif kind == "NUMBER":
            tokens.append(Token("NUMBER", float(text) if "." in text else int(text), line))
        elif kind == "STRING":
            val = re.sub(r"\\(.)", lambda mm: ESC.get(mm.group(1), mm.group(1)), text[1:-1])
            tokens.append(Token("STRING", val, line))
        elif kind == "IDENT":
            tokens.append(Token(text if text in KEYWORDS else "IDENT", text, line))
        elif kind == "OP":
            tokens.append(Token(text, text, line))
        else:
            msg = "unterminated string" if text == '"' else f"unexpected character {text!r}"
            raise TinyError("Lexical", msg, line)
    tokens.append(Token("EOF", None, line))
    return tokens