"""Colours, language guide and example programs for Tiny IDE."""

# --------------------------------------------------------------------------- themes
THEMES = {
    "dark": dict(
        bg="#1a1b26", bar="#16161e", panel="#1f2335", fg="#c0caf5", muted="#7982a9",
        btn="#2a2e45", btn_hover="#3a4068", btn_fg="#c0caf5",
        editor="#1a1b26", gutter="#16161e", gutter_fg="#565f89", select="#33467c", cursor="#c0caf5",
        keyword="#bb9af7", builtin="#7dcfff", string="#9ece6a", number="#ff9e64",
        comment="#565f89", funcname="#e0af68", operator="#89ddff",
        bad="#f7768e", bad_bg="#6b2437", errline="#2d1f2f", ok="#9ece6a", warn="#e0af68",
        out_bg="#11121a", out_fg="#c0caf5", scroll="#2a2e45", scroll_active="#3a4068", trough="#16161e"),
    "light": dict(
        bg="#eef0f6", bar="#e1e4ee", panel="#f6f7fb", fg="#2b2f3a", muted="#6b7390",
        btn="#d6dae8", btn_hover="#c4c9dd", btn_fg="#2b2f3a",
        editor="#ffffff", gutter="#eceef5", gutter_fg="#98a0b8", select="#bcd2ff", cursor="#2b2f3a",
        keyword="#7c3aed", builtin="#0e7490", string="#15803d", number="#c2410c",
        comment="#8a94ad", funcname="#a16207", operator="#0369a1",
        bad="#b91c1c", bad_bg="#fecaca", errline="#ffe4e6", ok="#15803d", warn="#b45309",
        out_bg="#f8fafc", out_fg="#1e293b", scroll="#c4c9dd", scroll_active="#aab1cc", trough="#eceef5"),
}
RUN_GREEN, RUN_GREEN_HOVER = "#2ea043", "#3fb950"

GUIDE = """TINY LANGUAGE GUIDE

Every statement ends with a semicolon ;

COMMENTS
    // this is a comment

VARIABLES
    let age = 20;          create a variable
    age = age + 1;         change it later

VALUES
    numbers   5   3.14
    text      "hello"
    booleans  true   false

OPERATORS
    maths        +  -  *  /  %
    compare      ==  !=  <  <=  >  >=
    logic        and   or   not
    join text    "Score: " + 10

DECISIONS
    if (x > 5) { print("big"); }
    else if (x > 2) { print("medium"); }
    else { print("small"); }

LOOPS
    while (i <= 10) { i = i + 1; }

FUNCTIONS
    fn add(a, b) { return a + b; }
    print(add(2, 3));

BUILT-IN FUNCTIONS
    print(a, b, ...)   show values
    input("Question")  ask the user (returns text)
    int(x)             turn text into a whole number
    str(x)             turn a value into text
    len(text)          number of characters

COLOURS IN THE EDITOR
    purple   keywords (let, fn, if, while ...)
    cyan     built-in functions
    green    text in quotes
    orange   numbers
    grey     comments
    RED      something the language does not accept
             (red line + red dot in the margin = error on that line)

SHORTCUTS
    F5 or Ctrl+Enter   run          Ctrl+S   save
    Ctrl+O   open                   Ctrl+N   new
    Ctrl + mouse wheel   zoom
"""

EXAMPLES = {
"Hello World": """print("Hello, World!");
""",
"Add two numbers": """let a = 12;
let b = 30;
print("Sum =", a + b);
""",
"Add numbers typed by user": """let a = int(input("First number: "));
let b = int(input("Second number: "));
print("Sum =", a + b);
""",
"Subtract, multiply, divide": """let a = 20;
let b = 4;
print("a - b =", a - b);
print("a * b =", a * b);
print("a / b =", a / b);
print("a % b =", a % b);
""",
"Multiplication table": """let n = 7;
let i = 1;
while (i <= 10) {
    print(n, "x", i, "=", n * i);
    i = i + 1;
}
""",
"Factorial": """fn fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
print("5! =", fact(5));
print("10! =", fact(10));
""",
"Fibonacci": """fn fib(n) {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}
let i = 0;
while (i < 10) {
    print("fib(" + i + ") =", fib(i));
    i = i + 1;
}
""",
"Sum of 1 to N": """let n = 100;
let total = 0;
let i = 1;
while (i <= n) {
    total = total + i;
    i = i + 1;
}
print("Sum of 1 to", n, "=", total);
""",
"Even or odd": """fn check(n) {
    if (n % 2 == 0) { return "even"; }
    return "odd";
}
print(7, "is", check(7));
print(10, "is", check(10));
""",
"Prime number check": """fn is_prime(n) {
    if (n < 2) { return false; }
    let d = 2;
    while (d * d <= n) {
        if (n % d == 0) { return false; }
        d = d + 1;
    }
    return true;
}
let i = 1;
while (i <= 30) {
    if (is_prime(i)) { print(i, "is prime"); }
    i = i + 1;
}
""",
"Power (x to the n)": """fn power(x, n) {
    let result = 1;
    let i = 0;
    while (i < n) {
        result = result * x;
        i = i + 1;
    }
    return result;
}
print("2 ^ 10 =", power(2, 10));
""",
"Largest of three": """fn biggest(a, b, c) {
    let m = a;
    if (b > m) { m = b; }
    if (c > m) { m = c; }
    return m;
}
print("Largest =", biggest(14, 92, 37));
""",
"GCD": """fn gcd(a, b) {
    while (b != 0) {
        let t = b;
        b = a % b;
        a = t;
    }
    return a;
}
print("gcd(48, 18) =", gcd(48, 18));
""",
"Celsius to Fahrenheit": """fn to_f(c) {
    return c * 9 / 5 + 32;
}
print("100 C =", to_f(100), "F");
print("37 C =", to_f(37), "F");
""",
"FizzBuzz": """let i = 1;
while (i <= 15) {
    if (i % 15 == 0) { print("FizzBuzz"); }
    else if (i % 3 == 0) { print("Fizz"); }
    else if (i % 5 == 0) { print("Buzz"); }
    else { print(i); }
    i = i + 1;
}
""",
"String length": """let word = "compiler";
print(word, "has", len(word), "letters");
""",
"ERROR demo: missing semicolon": """let x = 5
print(x);
""",
"ERROR demo: unknown variable": """let price = 100;
print(total);
""",
"ERROR demo: bad character": """let a = 10 @ 5;
print(a);
""",
"ERROR demo: divide by zero (runtime)": """let a = 10;
let b = 0;
print(a / b);
""",
}