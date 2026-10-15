"""Stage 4 - VIRTUAL MACHINE: executes the bytecode with a value stack and call frames."""
from .errors import TinyError

MAX_DEPTH = 500


def fmt(v):
    if v is None: return "nil"
    if v is True: return "true"
    if v is False: return "false"
    return str(v)


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


class VM:
    def __init__(self, program, out=print, inp=input, max_steps=5_000_000):
        self.p, self.out, self.inp, self.max_steps = program, out, inp, max_steps

    def err(self, msg, line):
        return TinyError("Runtime", msg, line)

    def binop(self, op, a, b, line):
        if op == "EQ": return a == b and is_num(a) == is_num(b)
        if op == "NE": return not (a == b and is_num(a) == is_num(b))
        if op == "ADD" and (isinstance(a, str) or isinstance(b, str)):
            return fmt(a) + fmt(b)
        if op in ("LT", "LE", "GT", "GE") and isinstance(a, str) and isinstance(b, str):
            pass
        elif not (is_num(a) and is_num(b)):
            raise self.err(f"cannot apply '{op}' to {type(a).__name__} and {type(b).__name__}", line)
        if op == "ADD": return a + b
        if op == "SUB": return a - b
        if op == "MUL": return a * b
        if op in ("DIV", "MOD") and b == 0:
            raise self.err("division by zero", line)
        if op == "DIV":
            return a // b if isinstance(a, int) and isinstance(b, int) and a % b == 0 else a / b
        if op == "MOD": return a % b
        return {"LT": a < b, "LE": a <= b, "GT": a > b, "GE": a >= b}[op]

    def builtin(self, name, args, line):
        if name == "print":
            self.out(" ".join(fmt(a) for a in args)); return None
        if name == "len":
            if not isinstance(args[0], str): raise self.err("len() needs a string", line)
            return len(args[0])
        if name == "str": return fmt(args[0])
        if name == "int":
            try: return int(float(args[0])) if isinstance(args[0], str) else int(args[0])
            except (ValueError, TypeError):
                raise self.err(f"cannot convert {fmt(args[0])!r} to int", line)
        if name == "input":
            return self.inp(fmt(args[0]) if args else "")

    def run(self):
        stack, frames, glob = [], [], {}
        code, ip, locs, steps = self.p.main, 0, glob, 0
        while True:
            op, arg, line = code.instrs[ip]
            ip += 1
            steps += 1
            if steps > self.max_steps:
                raise self.err("execution limit exceeded (infinite loop?)", line)
            if op == "PUSH": stack.append(arg)
            elif op == "POP": stack.pop()
            elif op == "LOAD":
                if arg in locs: stack.append(locs[arg])
                elif arg in glob: stack.append(glob[arg])
                else: raise self.err(f"variable '{arg}' has no value yet", line)
            elif op == "DEFINE": locs[arg] = stack.pop()
            elif op == "STORE":
                v = stack.pop()
                if arg in locs: locs[arg] = v
                elif arg in glob: glob[arg] = v
                else: raise self.err(f"variable '{arg}' has no value yet", line)
            elif op == "NEG":
                v = stack.pop()
                if not is_num(v): raise self.err("cannot negate a non-number", line)
                stack.append(-v)
            elif op == "NOT": stack.append(not stack.pop())
            elif op in ("ADD", "SUB", "MUL", "DIV", "MOD", "EQ", "NE", "LT", "LE", "GT", "GE"):
                b = stack.pop(); a = stack.pop()
                stack.append(self.binop(op, a, b, line))
            elif op == "JMP": ip = arg
            elif op == "JF":
                if not stack.pop(): ip = arg
            elif op == "JF_KEEP":
                if not stack[-1]: ip = arg
                else: stack.pop()
            elif op == "JT_KEEP":
                if stack[-1]: ip = arg
                else: stack.pop()
            elif op == "CALLB":
                name, n = arg
                args = stack[len(stack) - n:]
                del stack[len(stack) - n:]
                stack.append(self.builtin(name, args, line))
            elif op == "CALL":
                name, n = arg
                fn = self.p.funcs[name]
                args = stack[len(stack) - n:]
                del stack[len(stack) - n:]
                if len(frames) >= MAX_DEPTH:
                    raise self.err("stack overflow (too much recursion)", line)
                frames.append((code, ip, locs))
                code, ip, locs = fn, 0, dict(zip(fn.params, args))
            elif op == "RET":
                code, ip, locs = frames.pop()
            elif op == "HALT":
                return