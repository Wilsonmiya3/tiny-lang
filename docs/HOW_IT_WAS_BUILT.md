# How this project was built (and why)

This document records what was built, the decisions behind it, and the exact commands used, so the whole project can be explained and reproduced.

## 1. The goal

A school project: design a small programming language and build a compiler application for it, usable on Windows and installable from a flash drive.

## 2. Design decisions

| Decision | Why |
|----------|-----|
| Python 3 | Quick to write and easy to read. The standard library has everything needed (`re`, `tkinter`, `unittest`), so there are no dependencies. |
| Compile to bytecode and run it on a virtual machine | A real compiler back end. The bytecode can be printed (Bytecode button / `--dis`), which is ideal for a demo and a report. |
| Syntax tree as plain tuples `(kind, line, ...)` | Simple, printable, and every node carries its line number for error messages. |
| Recursive-descent parser | One method per grammar rule. Operator precedence is a chain of methods (`or` -> `and` -> equality -> comparison -> term -> factor -> unary). |
| Two-pass compiler | Pass 1 collects function names and argument counts, so functions can be called before they are defined and argument counts are checked before the program runs. Pass 2 generates code. |
| Four error kinds, always with a line | Lexical, Syntax, Semantic, Runtime. Errors are caught where they first become detectable. |
| Safety limits | Recursion depth 500 and a 5,000,000 step limit, so a student's infinite loop shows an error instead of freezing the app. |

## 3. The pipeline, stage by stage

| Stage | File | Input -> output | Key technique |
|-------|------|-----------------|---------------|
| 1 Lexer | `tiny/lexer.py` | text -> tokens | One regular expression with a named group per token kind (comment, number, string, identifier, operator, ...). Anything unmatched is a Lexical error. |
| 2 Parser | `tiny/parser.py` | tokens -> syntax tree | Recursive descent, one method per grammar rule. |
| 3 Compiler | `tiny/compiler.py` | tree -> bytecode | Scope stack for `let` / blocks, jump patching for `if` / `while` / `and` / `or`. |
| 4 VM | `tiny/vm.py` | bytecode -> output | Value stack, call frames for functions, a dictionary of variables per frame. |

### VM instruction set

| Instruction | Meaning |
|-------------|---------|
| `PUSH v` / `POP` | put a constant on the stack / discard the top |
| `LOAD x` / `DEFINE x` / `STORE x` | read a variable / create it / change it |
| `ADD SUB MUL DIV MOD` | arithmetic on the top two values |
| `EQ NE LT LE GT GE` | comparisons |
| `NEG` / `NOT` | unary minus / logical not |
| `JMP n` / `JF n` | jump / jump if false |
| `JF_KEEP n` / `JT_KEEP n` | short-circuit `and` / `or` (keep the value when jumping) |
| `CALL f` / `CALLB f` | call a Tiny function / a built-in |
| `RET` / `HALT` | return from a function / stop the program |

## 4. Testing

- `tests/test_tiny.py` has 10 unit tests: arithmetic precedence, division, strings, if/else, while, recursion, forward calls, short-circuit logic, globals inside functions, and ten error cases that check each error is reported with the right kind.
- Every example program in the IDE's Examples menu was run automatically through the compiler to confirm it gives the expected output (or the expected error for the "ERROR demo" ones).
- The IDE was exercised in a virtual (headless) display to check colours, error marking, both themes and the buttons.
- The Windows build (`build.ps1`) and the installer script could not be run in that environment. They use the documented options of PyInstaller and Inno Setup, and if a step fails, the red message in PowerShell says which one.

## 5. Setting up on Windows: commands and why

| Command | What it does | Why |
|---------|--------------|-----|
| `winget install Python.Python.3.12` | installs Python | Python is the only requirement. (Python 3.13 also works.) |
| `python --version` | prints the version | confirms Python is on the PATH. Open a new PowerShell window after installing. |
| `cd $HOME\Documents\tinylang` | go to the project | all other commands run from the project folder. |
| `Expand-Archive tinylang.zip ...` | unzips the project | did not work, because the browser download was not in `Downloads`. We switched to writing the files directly from PowerShell. |
| `function W($p,$t){ [IO.File]::WriteAllText((Join-Path $PWD $p),$t,(New-Object Text.UTF8Encoding $false)) }` | helper that writes text to a file | `Join-Path $PWD` uses PowerShell's current folder (.NET has its own current folder). UTF-8 without a byte-order mark keeps Python happy. |
| `W 'file.py' @'` ... `'@` | writes a file from a pasted block | a single-quoted here-string keeps the text exactly as typed (no `$` or backtick processing). |
| `python tests\test_tiny.py` | runs the tests | should end with `OK`. |
| `python main.py examples\hello.tiny --tokens` / `--ast` / `--dis` | shows each compiler stage | tokens (lexer), syntax tree (parser), bytecode (compiler). |
| `python gui.py` | opens the IDE | |

## 6. The IDE: how its features work

- **Syntax colours.** The editor reuses the lexer's own regular expression, so the editor and the compiler always agree on what a keyword, number or string is. Characters the language does not accept are matched by the lexer's `BAD` group and painted red immediately.
- **Live error warnings.** 350 ms after you stop typing, the whole program is compiled. A `TinyError` carries its line number, so the IDE shades the line red, puts a red dot in the margin and writes the message in the status bar (click it to jump to the line). For "unknown variable" errors the offending name is underlined.
- **Detecting edits.** A Tk text box has no single event for "the text changed". The IDE renames the widget's internal command, forwards every call, and fires its own virtual events on insert, delete and cursor movement.
- **Line numbers.** A small canvas next to the editor draws the numbers using `dlineinfo` to find where each visible line is.
- **Themes.** All colours live in one dictionary per theme (`ide_data.py`); `apply_theme()` recolours every widget and text tag.
- **Convenience.** Auto-indent after `{`, Tab inserts four spaces, `}` de-indents, Ctrl+mouse-wheel zoom, F5 to run, Ctrl+S / O / N, a prompt to save unsaved changes.

## 7. Packaging: exe and installer

`build.ps1` does five steps:

| Step | Command | Why |
|------|---------|-----|
| 1 | `python -m pip install pyinstaller` | PyInstaller bundles Python and the program into one `.exe`. |
| 2 | `python make_ico.py` | creates `assets\tiny.ico`. The icon is drawn by `icon_gen.py` in pure Python (no image library, no pasted binary data). |
| 3 | `python -m PyInstaller --noconfirm --clean --onefile --windowed --name TinyIDE --icon assets\tiny.ico gui.py` | `--onefile` gives a single exe, `--windowed` hides the black console window, `--name` names it, `--icon` sets the icon, `--clean --noconfirm` avoid stale builds. |
| 4 | `winget install -e --id JRSoftware.InnoSetup`, then `ISCC.exe installer.iss` | Inno Setup (free) builds `TinyIDE-Setup.exe` from `installer.iss`. |
| 5 | copy to `Desktop\compiler` | the folder asked for: the exe, the installer and the examples. |

Key choices in `installer.iss`:

- `PrivilegesRequired=lowest` with `PrivilegesRequiredOverridesAllowed=dialog`: installs without admin rights (useful on school computers), or for all users if the person chooses.
- `{autopf}` resolves to the correct Program Files folder for either mode, and `HKA` registry keys follow the same mode.
- Tasks add an optional desktop shortcut and an optional `.tiny` file association (double-click a `.tiny` file to open it in the IDE).
- The installer also creates a Start menu entry and an uninstaller.

## 8. Things that went wrong, and the fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `Expand-Archive` could not find the zip | the file had not been downloaded to `Downloads` | write the project files straight from PowerShell with the `W` helper |
| `The term '♠Get-ChildItem' is not recognized` | a stray character was pasted before the command | paste with right-click and clear the line with Ctrl+C first |
| `Select-Object : A parameter cannot be found that matches parameter name 'Path'` | the same command was pasted twice onto one line | paste once and wait for the prompt |
| The IDE sample printed only `fact(1)` and `fact(4)` | the sample text in the editor had been edited (`i = i + 3`) | pick the example again from the Examples menu |

## 9. Publishing to GitHub: commands and why

| Command | Why |
|---------|-----|
| `git init -b main` | turns the folder into a repository with a branch called `main` |
| `git config user.name` / `user.email` | commits need an author name and email |
| `git add .` | stage every file (`.gitignore` keeps build output out) |
| `git status` | check what is about to be committed |
| `git commit -m "..."` | save the snapshot |
| `winget install GitHub.cli` then `gh auth login` | the GitHub command-line tool signs in through the browser, so no passwords or tokens are typed |
| `gh repo create tiny-lang --public --source . --remote origin --push` | creates the repository on GitHub, links it and uploads the code in one step |

Build output (`build/`, `dist/`, `installer_output/`, `*.spec`) is not committed because it is generated. The installer can instead be attached to a GitHub Release.

## 10. Ideas to extend the language

- `for` loops, arrays / lists, string indexing
- more built-ins (`sqrt`, `abs`, `random`)
- `break` / `continue`
- compile to a real target (C, JavaScript, or x86 assembly) instead of bytecode