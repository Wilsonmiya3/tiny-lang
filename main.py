"""Command-line front end:  python main.py program.tiny [--tokens] [--ast] [--dis]"""
import argparse, pprint, sys
from tiny import TinyError, tokenize, Parser, compile_source, disassemble, VM

ap = argparse.ArgumentParser(description="Tiny language compiler + VM")
ap.add_argument("file")
ap.add_argument("--tokens", action="store_true", help="show lexer output")
ap.add_argument("--ast", action="store_true", help="show syntax tree")
ap.add_argument("--dis", action="store_true", help="show bytecode")
a = ap.parse_args()

src = open(a.file, encoding="utf-8").read()
try:
    if a.tokens:
        for t in tokenize(src): print(t)
    if a.ast:
        pprint.pprint(Parser(tokenize(src)).parse(), width=100)
    prog = compile_source(src)
    if a.dis:
        print(disassemble(prog))
    elif not (a.tokens or a.ast):
        VM(prog).run()
except TinyError as e:
    print(e, file=sys.stderr)
    sys.exit(1)