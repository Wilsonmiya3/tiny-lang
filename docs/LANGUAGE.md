# Tiny language reference

Every statement ends with a semicolon `;`. Whitespace and newlines do not matter.

## Basics

| Type    | Examples          |
|---------|-------------------|
| number  | `5`, `3.14`       |
| text    | `"hello"`         |
| boolean | `true`, `false`   |

Text escapes: `\n` (new line), `\t` (tab), `\"` (quote), `\\` (backslash).

## Operators (lowest to highest precedence)

| Level | Operators |
|-------|-----------|
| 1 | `or` |
| 2 | `and` |
| 3 | `==` `!=` |
| 4 | `<` `<=` `>` `>=` |
| 5 | `+` `-` |
| 6 | `*` `/` `%` |
| 7 | unary `-` and `not` |
| 8 | function calls, parentheses |

- `+` joins text when either side is text: `"Score: " + 10` gives `Score: 10`.
- `/` gives a whole number when the division is exact (`10 / 2` is `5`), otherwise a decimal (`7 / 2` is `3.5`).
- `and` / `or` short-circuit: the right side is only evaluated when needed.

## Decisions and loops

The brackets around the condition are optional grouping: `if x > 5 { ... }` also works. Blocks `{ }` create a new scope, so a variable declared inside a block is not visible outside it.

## Functions

- Functions are declared at the top level only.
- A function can be called before the line where it is defined.
- A function can read and change the program's global variables.
- A function without `return` gives back `nil`.
- Recursion is allowed (depth limit 500).

## Built-in functions

| Function | Meaning |
|----------|---------|
| `print(a, b, ...)` | show values separated by spaces |
| `input("question")` | ask the user, returns text |
| `int(x)` | text or number to a whole number |
| `str(x)` | any value to text |
| `len(text)` | number of characters |

## Grammar (EBNF)

## Error kinds

Every error shows its kind and the line number.

| Kind | Found by | Examples |
|------|----------|----------|
| Lexical | lexer | unexpected character `@`, unterminated string |
| Syntax | parser | missing `;`, missing `}`, expected an expression |
| Semantic | compiler (before running) | unknown variable, variable already declared, unknown function, wrong number of arguments, `return` outside a function |
| Runtime | virtual machine (while running) | division by zero, wrong types (`1 - "a"`), too much recursion, infinite loop (limit 5,000,000 steps) |