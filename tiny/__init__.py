from .errors import TinyError
from .lexer import tokenize
from .parser import Parser
from .compiler import Compiler, disassemble
from .vm import VM


def compile_source(src):
    return Compiler().compile(Parser(tokenize(src)).parse())


def run_source(src, out=print, inp=input):
    VM(compile_source(src), out, inp).run()