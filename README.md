# Tiny: a small programming language with its own compiler, virtual machine, IDE and Windows installer

A school project: design a small language, then build the tools around it.

## What is inside

- **The language "Tiny"**: variables, numbers / text / booleans, `if / else`, `while`, functions, recursion, built-in functions.
- **The compiler (Python)**: lexer, recursive-descent parser, semantic checker, bytecode generator.
- **The virtual machine**: stack based, with call frames, a recursion limit and an infinite-loop guard.
- **Tiny IDE (tkinter)**: syntax colours, live error warnings, Run / Bytecode / Tokens / Syntax Tree buttons, 20 built-in examples, dark and light themes.
- **A Windows installer** built with PyInstaller + Inno Setup.

## Quick start (Windows, PowerShell)

Needs Python 3.10 or newer (tkinter is included with the normal Python installer).

```powershell
git clone https://github.com/Wilsonmiya3/tiny-lang.git
cd tiny-lang
python tests\test_tiny.py                      # run the test suite (should say OK)
python main.py examples\factorial.tiny         # run a program
python gui.py                                  # open the IDE
```

Command line options:

```powershell
python main.py examples\hello.tiny --tokens    # lexer output
python main.py examples\hello.tiny --ast       # syntax tree
python main.py examples\hello.tiny --dis       # bytecode
```

## The language at a glance

Full reference and grammar: [docs/LANGUAGE.md](docs/LANGUAGE.md).

## Build the .exe and the installer

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

This creates `TinyIDE.exe` and `TinyIDE-Setup.exe` and copies them to `Desktop\compiler`.
Copy `TinyIDE-Setup.exe` to a flash drive to install the IDE on another Windows PC.

## Project layout

## Documentation

- [docs/LANGUAGE.md](docs/LANGUAGE.md): language reference, grammar, error kinds
- [docs/HOW_IT_WAS_BUILT.md](docs/HOW_IT_WAS_BUILT.md): design decisions, every command we used and why