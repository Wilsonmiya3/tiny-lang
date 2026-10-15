"""Stage 3 - COMPILER: semantic checks + bytecode generation.

Each instruction is [opcode, argument, source_line].
"""
from .errors import TinyError

BUILTINS = {"print": (0, 99), "len": (1, 1), "str": (1, 1), "int": (1, 1), "input": (0, 1)}
BINOPS = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD", "==": "EQ",
          "!=": "NE", "<": "LT", "<=": "LE", ">": "GT", ">=": "GE"}


class Code:
    def __init__(self, name, params):
        self.name, self.params, self.instrs = name, params, []

    def emit(self, op, arg=None, line=0):
        self.instrs.append([op, arg, line])
        return len(self.instrs) - 1


class Program:
    def __init__(self, main, funcs):
        self.main, self.funcs = main, funcs


class Compiler:
    def compile(self, ast):
        stmts = ast[2]
        self.funcs, self.sigs = {}, {}
        for s in stmts:                       # pass 1: collect function signatures
            if s[0] == "fn":
                if s[2] in self.sigs or s[2] in BUILTINS:
                    raise TinyError("Semantic", f"function '{s[2]}' is already defined", s[1])
                self.sigs[s[2]] = len(s[3])
        self.global_names = set()
        self._collect_lets(stmts)
        self.code, self.in_fn, self.scopes = Code("<main>", []), False, [set()]
        for s in stmts:                       # pass 2: generate code
            if s[0] == "fn":
                self.compile_fn(s)
            else:
                self.stmt(s)
        self.code.emit("HALT")
        main = self.code
        return Program(main, self.funcs)

    def _collect_lets(self, stmts):
        for s in stmts:
            if s[0] == "let": self.global_names.add(s[2])
            elif s[0] == "if":
                self._collect_lets(s[3]); self._collect_lets(s[4] or [])
            elif s[0] in ("while", "block"):
                self._collect_lets(s[3] if s[0] == "while" else s[2])

    def compile_fn(self, s):
        _, line, name, params, body = s
        saved = (self.code, self.in_fn, self.scopes)
        self.code, self.in_fn, self.scopes = Code(name, params), True, [set(params)]
        self.body(body)
        self.code.emit("PUSH", None, line)
        self.code.emit("RET", None, line)
        self.funcs[name] = self.code
        self.code, self.in_fn, self.scopes = saved

    # ---- scope helpers
    def declared(self, name):
        return any(name in sc for sc in self.scopes)

    def visible(self, name, line):
        if self.declared(name) or (self.in_fn and name in self.global_names):
            return
        raise TinyError("Semantic", f"variable '{name}' used before it is declared", line)

    def body(self, stmts):
        self.scopes.append(set())
        for s in stmts:
            self.stmt(s)
        self.scopes.pop()

    # ---- statements
    def stmt(self, s):
        k, line = s[0], s[1]
        c = self.code
        if k == "let":
            self.expr(s[3])
            if self.declared(s[2]):
                raise TinyError("Semantic", f"variable '{s[2]}' is already declared", line)
            self.scopes[-1].add(s[2])
            c.emit("DEFINE", s[2], line)
        elif k == "assign":
            self.visible(s[2], line)
            self.expr(s[3])
            c.emit("STORE", s[2], line)
        elif k == "expr":
            self.expr(s[2]); c.emit("POP", None, line)
        elif k == "block":
            self.body(s[2])
        elif k == "if":
            self.expr(s[2])
            jf = c.emit("JF", None, line)
            self.body(s[3])
            if s[4] is not None:
                jend = c.emit("JMP", None, line)
                c.instrs[jf][1] = len(c.instrs)
                self.body(s[4])
                c.instrs[jend][1] = len(c.instrs)
            else:
                c.instrs[jf][1] = len(c.instrs)
        elif k == "while":
            start = len(c.instrs)
            self.expr(s[2])
            jf = c.emit("JF", None, line)
            self.body(s[3])
            c.emit("JMP", start, line)
            c.instrs[jf][1] = len(c.instrs)
        elif k == "return":
            if not self.in_fn:
                raise TinyError("Semantic", "'return' outside of a function", line)
            if s[2] is None: c.emit("PUSH", None, line)
            else: self.expr(s[2])
            c.emit("RET", None, line)

    # ---- expressions
    def expr(self, e):
        k, line, c = e[0], e[1], self.code
        if k in ("num", "str", "bool"):
            c.emit("PUSH", e[2], line)
        elif k == "var":
            self.visible(e[2], line); c.emit("LOAD", e[2], line)
        elif k == "un":
            self.expr(e[3]); c.emit("NEG" if e[2] == "-" else "NOT", None, line)
        elif k == "bin":
            self.expr(e[3]); self.expr(e[4]); c.emit(BINOPS[e[2]], None, line)
        elif k == "logic":   # short-circuit
            self.expr(e[3])
            j = c.emit("JF_KEEP" if e[2] == "and" else "JT_KEEP", None, line)
            self.expr(e[4])
            c.instrs[j][1] = len(c.instrs)
        elif k == "call":
            name, args = e[2], e[3]
            if name in BUILTINS:
                lo, hi = BUILTINS[name]
                if not lo <= len(args) <= hi:
                    raise TinyError("Semantic", f"'{name}' got {len(args)} argument(s)", line)
            elif name in self.sigs:
                if self.sigs[name] != len(args):
                    raise TinyError("Semantic",
                        f"function '{name}' expects {self.sigs[name]} argument(s) but got {len(args)}", line)
            else:
                raise TinyError("Semantic", f"unknown function '{name}'", line)
            for a in args:
                self.expr(a)
            c.emit("CALLB" if name in BUILTINS else "CALL", (name, len(args)), line)


def disassemble(program):
    out = []
    for code in [program.main] + list(program.funcs.values()):
        out.append(f"== {code.name}({', '.join(code.params)}) ==")
        for i, (op, arg, line) in enumerate(code.instrs):
            out.append(f"{i:4}  L{line:<3} {op:<8} {'' if arg is None else repr(arg)}")
        out.append("")
    return "\n".join(out)