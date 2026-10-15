"""Stage 2 - PARSER: recursive descent, tokens -> AST (tuples: (kind, line, ...))."""
from .errors import TinyError


def describe(tok):
    return "end of file" if tok.kind == "EOF" else repr(tok.value)


class Parser:
    def __init__(self, tokens):
        self.t, self.i = tokens, 0

    # ---- helpers
    def peek(self, k=0):
        return self.t[min(self.i + k, len(self.t) - 1)]

    def at(self, *kinds):
        return self.peek().kind in kinds

    def next(self):
        tok = self.peek()
        if tok.kind != "EOF":
            self.i += 1
        return tok

    def expect(self, kind, what):
        tok = self.peek()
        if tok.kind != kind:
            line = self.t[self.i - 1].line if kind == ";" and self.i > 0 else tok.line
            raise TinyError("Syntax", f"expected {what} but found {describe(tok)}", line)
        return self.next()

    # ---- statements
    def parse(self):
        stmts = []
        while not self.at("EOF"):
            stmts.append(self.statement(top=True))
        return ("program", 1, stmts)

    def block(self):
        self.expect("{", "'{'")
        stmts = []
        while not self.at("}", "EOF"):
            stmts.append(self.statement())
        self.expect("}", "'}' to close the block")
        return stmts

    def statement(self, top=False):
        t = self.peek()
        k = t.kind
        if k == "fn":
            if not top:
                raise TinyError("Syntax", "functions can only be declared at the top level", t.line)
            return self.fn()
        if k == "let":
            self.next()
            name = self.expect("IDENT", "a variable name").value
            self.expect("=", "'='")
            e = self.expr()
            self.expect(";", "';'")
            return ("let", t.line, name, e)
        if k == "if":
            return self.if_stmt()
        if k == "while":
            self.next()
            c = self.expr()
            return ("while", t.line, c, self.block())
        if k == "return":
            self.next()
            e = None if self.at(";") else self.expr()
            self.expect(";", "';'")
            return ("return", t.line, e)
        if k == "{":
            return ("block", t.line, self.block())
        if k == "IDENT" and self.peek(1).kind == "=":
            name = self.next().value
            self.next()
            e = self.expr()
            self.expect(";", "';'")
            return ("assign", t.line, name, e)
        e = self.expr()
        self.expect(";", "';'")
        return ("expr", t.line, e)

    def if_stmt(self):
        t = self.next()
        cond = self.expr()
        then = self.block()
        els = None
        if self.at("else"):
            self.next()
            els = [self.if_stmt()] if self.at("if") else self.block()
        return ("if", t.line, cond, then, els)

    def fn(self):
        t = self.next()
        name = self.expect("IDENT", "a function name").value
        self.expect("(", "'('")
        params = []
        if not self.at(")"):
            params.append(self.expect("IDENT", "a parameter name").value)
            while self.at(","):
                self.next()
                params.append(self.expect("IDENT", "a parameter name").value)
        self.expect(")", "')'")
        if len(set(params)) != len(params):
            raise TinyError("Syntax", f"duplicate parameter in function '{name}'", t.line)
        return ("fn", t.line, name, params, self.block())

    # ---- expressions (lowest precedence first)
    def binary(self, sub, ops, node="bin"):
        left = sub()
        while self.peek().kind in ops:
            op = self.next()
            left = (node, op.line, op.kind, left, sub())
        return left

    def expr(self):       return self.binary(self.and_, ("or",), "logic")
    def and_(self):       return self.binary(self.equality, ("and",), "logic")
    def equality(self):   return self.binary(self.comparison, ("==", "!="))
    def comparison(self): return self.binary(self.term, ("<", "<=", ">", ">="))
    def term(self):       return self.binary(self.factor, ("+", "-"))
    def factor(self):     return self.binary(self.unary, ("*", "/", "%"))

    def unary(self):
        t = self.peek()
        if t.kind in ("-", "not"):
            self.next()
            return ("un", t.line, t.kind, self.unary())
        return self.call()

    def call(self):
        t = self.peek()
        if t.kind == "IDENT" and self.peek(1).kind == "(":
            self.next(); self.next()
            args = []
            if not self.at(")"):
                args.append(self.expr())
                while self.at(","):
                    self.next()
                    args.append(self.expr())
            self.expect(")", "')'")
            return ("call", t.line, t.value, args)
        return self.primary()

    def primary(self):
        t = self.next()
        if t.kind == "NUMBER": return ("num", t.line, t.value)
        if t.kind == "STRING": return ("str", t.line, t.value)
        if t.kind in ("true", "false"): return ("bool", t.line, t.kind == "true")
        if t.kind == "IDENT": return ("var", t.line, t.value)
        if t.kind == "(":
            e = self.expr()
            self.expect(")", "')'")
            return e
        raise TinyError("Syntax", f"expected an expression but found {describe(t)}", t.line)