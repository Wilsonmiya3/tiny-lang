import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tiny import run_source, TinyError


def run(src):
    out = []
    run_source(src, out=out.append)
    return out


class Tests(unittest.TestCase):
    def test_arith_precedence(self): self.assertEqual(run("print(2 + 3 * 4);"), ["14"])
    def test_division(self): self.assertEqual(run("print(10 / 2, 7 / 2);"), ["5 3.5"])
    def test_strings(self): self.assertEqual(run('print("a" + 1);'), ["a1"])
    def test_if_else(self): self.assertEqual(run("if (1 > 2) { print(1); } else { print(2); }"), ["2"])
    def test_while(self): self.assertEqual(run("let i=0; while (i<3) { print(i); i=i+1; }"), ["0", "1", "2"])
    def test_recursion(self):
        self.assertEqual(run("fn f(n){ if(n<=1){return 1;} return n*f(n-1);} print(f(5));"), ["120"])
    def test_forward_call(self):
        self.assertEqual(run("print(g()); fn g(){ return 7; }"), ["7"])
    def test_short_circuit(self):
        self.assertEqual(run("print(false and (1/0 == 1)); print(true or (1/0 == 1));"), ["false", "true"])
    def test_global_from_fn(self):
        self.assertEqual(run("let c=0; fn inc(){ c = c + 1; } inc(); inc(); print(c);"), ["2"])

    def test_errors(self):
        for src, kind in [("let x = ;", "Syntax"), ("print(y);", "Semantic"),
                          ("let a=1; let a=2;", "Semantic"), ("foo();", "Semantic"),
                          ("return 1;", "Semantic"), ('print("x);', "Lexical"),
                          ("print(1/0);", "Runtime"), ('print(1 - "a");', "Runtime"),
                          ("while (true) { }", "Runtime"),
                          ("fn f(n){ return f(n+1); } f(0);", "Runtime")]:
            with self.assertRaises(TinyError, msg=src) as cm:
                run(src)
            self.assertEqual(cm.exception.kind, kind, src)


if __name__ == "__main__":
    unittest.main()