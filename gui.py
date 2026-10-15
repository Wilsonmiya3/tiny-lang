"""Tiny IDE - a colourful editor for the Tiny language.  Run:  python gui.py [file.tiny]"""
import bisect
import os
import pprint
import re
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter import font as tkfont

from tiny import TinyError, tokenize, Parser, compile_source, disassemble, VM
from tiny.lexer import SPEC, KEYWORDS
from tiny.compiler import BUILTINS
from icon_gen import png_base64
from ide_data import THEMES, RUN_GREEN, RUN_GREEN_HOVER, GUIDE, EXAMPLES

if sys.platform == "win32":                      # crisp text on high-DPI screens
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

APP_NAME = "Tiny IDE"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.theme_name = "dark"
        self.t = THEMES["dark"]
        self.path = None
        self._saved = ""
        self.err_lines = set()
        self.first_error = None
        self._check_job = None
        self.size = 13

        self.f_code = tkfont.Font(family="Consolas", size=self.size)
        self.f_italic = tkfont.Font(family="Consolas", size=self.size, slant="italic")
        self.f_bold = tkfont.Font(family="Consolas", size=self.size, weight="bold")
        self.f_out = tkfont.Font(family="Consolas", size=self.size - 1)
        self.f_outb = tkfont.Font(family="Consolas", size=self.size - 1, weight="bold")
        self.f_ui = ("Segoe UI", 10)
        self.f_ui_b = ("Segoe UI", 10, "bold")

        self.geometry("1180x740")
        self.minsize(820, 540)
        try:
            self.iconphoto(True, tk.PhotoImage(data=png_base64(64)))
        except tk.TclError:
            pass

        self.build_ui()
        self.install_proxy()
        self.bind_keys()
        self.apply_theme()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            self.load_path(sys.argv[1])
        else:
            self.set_text(EXAMPLES["Factorial"])
        self.editor.focus_set()

    # ------------------------------------------------------------------ UI building
    def build_ui(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        # toolbar
        self.toolbar = tk.Frame(self, padx=8, pady=7)
        self.toolbar.pack(side="top", fill="x")
        self.btns, self.seps = [], []

        def btn(text, cmd, accent=None, accent_hover=None, side="left"):
            b = tk.Button(self.toolbar, text=text, command=cmd, relief="flat", bd=0, padx=10, pady=6,
                          cursor="hand2", font=self.f_ui_b)
            b.accent, b.accent_hover = accent, accent_hover
            b.pack(side=side, padx=2)
            b.bind("<Enter>", lambda e, b=b: b.config(bg=b._hover))
            b.bind("<Leave>", lambda e, b=b: b.config(bg=b._normal))
            self.btns.append(b)
            return b

        def sep():
            s = tk.Frame(self.toolbar, width=1)
            s.pack(side="left", fill="y", padx=8, pady=3)
            self.seps.append(s)

        self.theme_btn = btn("Light", self.toggle_theme, side="right")
        btn("A+", lambda: self.zoom(1), side="right")
        btn("A\u2212", lambda: self.zoom(-1), side="right")

        btn("New", self.cmd_new)
        btn("Open", self.cmd_open)
        btn("Save", self.cmd_save)
        sep()
        btn("\u25b6  Run  (F5)", self.run_code, RUN_GREEN, RUN_GREEN_HOVER)
        sep()
        btn("Bytecode", self.show_bytecode)
        btn("Tokens", self.show_tokens)
        btn("Syntax Tree", self.show_ast)
        sep()
        btn("Clear Output", self.clear_output)
        sep()
        mb = tk.Menubutton(self.toolbar, text="Examples  \u25be", relief="flat", bd=0, padx=10, pady=6,
                           cursor="hand2", font=self.f_ui_b)
        mb.accent = mb.accent_hover = None
        self.examples_menu = tk.Menu(mb, tearoff=0, font=self.f_ui)
        seen_error = False
        for name in EXAMPLES:
            if name.startswith("ERROR") and not seen_error:
                self.examples_menu.add_separator()
                seen_error = True
            self.examples_menu.add_command(label=name, command=lambda n=name: self.cmd_example(n))
        mb.config(menu=self.examples_menu)
        mb.pack(side="left", padx=2)
        mb.bind("<Enter>", lambda e: mb.config(bg=mb._hover))
        mb.bind("<Leave>", lambda e: mb.config(bg=mb._normal))
        self.btns.append(mb)
        btn("Guide", self.show_guide)

        # status bar
        self.statusbar = tk.Frame(self)
        self.statusbar.pack(side="bottom", fill="x")
        self.status = tk.Label(self.statusbar, anchor="w", padx=12, pady=5, font=self.f_ui_b, cursor="hand2")
        self.status.pack(side="left", fill="x", expand=True)
        self.status.bind("<Button-1>", lambda e: self.goto_line(self.first_error))
        self.posinfo = tk.Label(self.statusbar, anchor="e", padx=12, pady=5, font=self.f_ui)
        self.posinfo.pack(side="right")

        # split: editor on top, output below
        self.pane = tk.PanedWindow(self, orient="vertical", sashwidth=7, bd=0, sashrelief="flat")
        self.pane.pack(fill="both", expand=True)

        ef = self.ef = tk.Frame(self.pane)
        self.pane.add(ef, stretch="always", minsize=200)
        ef.rowconfigure(0, weight=1)
        ef.columnconfigure(1, weight=1)
        self.gutter = tk.Canvas(ef, width=58, highlightthickness=0, bd=0)
        self.gutter.grid(row=0, column=0, sticky="ns")
        self.editor = tk.Text(ef, wrap="none", undo=True, maxundo=-1, bd=0, relief="flat", highlightthickness=0,
                              padx=10, pady=8, insertwidth=2, font=self.f_code, spacing1=1, spacing3=1,
                              tabs=("4c",), yscrollcommand=self.on_yscroll)
        self.editor.grid(row=0, column=1, sticky="nsew")
        self.vbar = ttk.Scrollbar(ef, orient="vertical", style="Tiny.Vertical.TScrollbar",
                                  command=self.editor.yview)
        self.vbar.grid(row=0, column=2, sticky="ns")
        self.hbar = ttk.Scrollbar(ef, orient="horizontal", style="Tiny.Horizontal.TScrollbar",
                                  command=self.editor.xview)
        self.hbar.grid(row=1, column=1, sticky="ew")
        self.editor.config(xscrollcommand=self.hbar.set)

        of = self.of = tk.Frame(self.pane)
        self.pane.add(of, minsize=110, height=240)
        of.rowconfigure(1, weight=1)
        of.columnconfigure(0, weight=1)
        self.out_head = tk.Label(of, text="  OUTPUT", anchor="w", font=("Segoe UI", 9, "bold"), pady=4)
        self.out_head.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.output = tk.Text(of, wrap="word", bd=0, relief="flat", highlightthickness=0, padx=12, pady=8,
                              state="disabled", font=self.f_out, cursor="arrow")
        self.output.grid(row=1, column=0, sticky="nsew")
        self.ovbar = ttk.Scrollbar(of, orient="vertical", style="Tiny.Vertical.TScrollbar",
                                   command=self.output.yview)
        self.ovbar.grid(row=1, column=1, sticky="ns")
        self.output.config(yscrollcommand=self.ovbar.set)

        self.editor.bind("<Configure>", lambda e: self.draw_gutter())
        self.editor.bind("<<TextChanged>>", self.on_text_changed)
        self.editor.bind("<<Change>>", self.on_change)

    # --------------------------------------------------------- change-detection proxy
    def install_proxy(self):
        w = self.editor
        self._orig = w._w + "_orig"
        w.tk.call("rename", w._w, self._orig)
        w.tk.createcommand(w._w, self._proxy)

    def _proxy(self, *args):
        result = self.tk.call((self._orig,) + args)
        a0 = args[0] if args else ""
        if a0 in ("insert", "delete", "replace"):
            self.editor.event_generate("<<TextChanged>>", when="tail")
            self.editor.event_generate("<<Change>>", when="tail")
        elif (a0 in ("see",) or args[:3] == ("mark", "set", "insert")
              or args[:2] in (("xview", "moveto"), ("xview", "scroll"),
                              ("yview", "moveto"), ("yview", "scroll"))):
            self.editor.event_generate("<<Change>>", when="tail")
        return result

    def on_yscroll(self, a, b):
        self.vbar.set(a, b)
        self.draw_gutter()

    # ------------------------------------------------------------------ theming
    def apply_theme(self):
        t = self.t = THEMES[self.theme_name]
        self.configure(bg=t["bg"])
        self.toolbar.config(bg=t["bar"])
        for s in self.seps:
            s.config(bg=t["btn"])
        for b in self.btns:
            normal = b.accent or t["btn"]
            hover = b.accent_hover or t["btn_hover"]
            fg = "#ffffff" if b.accent else t["btn_fg"]
            b._normal, b._hover = normal, hover
            b.config(bg=normal, fg=fg, activebackground=hover, activeforeground=fg)
        self.theme_btn.config(text="Light" if self.theme_name == "dark" else "Dark")
        self.examples_menu.config(bg=t["panel"], fg=t["fg"], activebackground=t["select"],
                                  activeforeground=t["fg"], bd=0)
        self.statusbar.config(bg=t["bar"])
        self.posinfo.config(bg=t["bar"], fg=t["muted"])
        self.pane.config(bg=t["bar"])
        self.ef.config(bg=t["gutter"])
        self.of.config(bg=t["bar"])
        self.gutter.config(bg=t["gutter"])
        ed = self.editor
        ed.config(bg=t["editor"], fg=t["fg"], insertbackground=t["cursor"], selectbackground=t["select"],
                  selectforeground=t["fg"], inactiveselectbackground=t["select"])
        self.out_head.config(bg=t["bar"], fg=t["muted"])
        self.output.config(bg=t["out_bg"], fg=t["out_fg"], selectbackground=t["select"])
        for orient in ("Vertical", "Horizontal"):
            self.style.configure(f"Tiny.{orient}.TScrollbar", background=t["scroll"], troughcolor=t["trough"],
                                 bordercolor=t["trough"], lightcolor=t["scroll"], darkcolor=t["scroll"],
                                 arrowcolor=t["muted"], relief="flat")
            self.style.map(f"Tiny.{orient}.TScrollbar", background=[("active", t["scroll_active"])])

        # editor tags (order = priority, later wins)
        ed.tag_configure("errline", background=t["errline"])
        ed.tag_configure("comment", foreground=t["comment"], font=self.f_italic)
        ed.tag_configure("string", foreground=t["string"])
        ed.tag_configure("number", foreground=t["number"])
        ed.tag_configure("keyword", foreground=t["keyword"], font=self.f_bold)
        ed.tag_configure("builtin", foreground=t["builtin"])
        ed.tag_configure("funcname", foreground=t["funcname"], font=self.f_bold)
        ed.tag_configure("operator", foreground=t["operator"])
        ed.tag_configure("bad", foreground=t["bad"], background=t["bad_bg"], underline=True)
        ed.tag_configure("errtok", foreground=t["bad"], background=t["bad_bg"], underline=True)
        ed.tag_raise("sel")
        # output tags
        o = self.output
        o.tag_configure("out", foreground=t["out_fg"])
        o.tag_configure("info", foreground=t["muted"])
        o.tag_configure("ok", foreground=t["ok"], font=self.f_outb)
        o.tag_configure("err", foreground=t["bad"], font=self.f_outb)
        o.tag_configure("head", foreground=t["keyword"], font=self.f_outb)
        self.refresh_status()
        self.draw_gutter()

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.apply_theme()

    def zoom(self, delta):
        self.size = max(8, min(34, self.size + delta))
        for f, d in ((self.f_code, 0), (self.f_italic, 0), (self.f_bold, 0), (self.f_out, -1), (self.f_outb, -1)):
            f.configure(size=self.size + d)
        self.draw_gutter()

    # ------------------------------------------------------------------ key bindings
    def bind_keys(self):
        for seq in ("<F5>", "<Control-Return>"):
            self.bind(seq, lambda e: (self.run_code(), "break")[1])
        self.bind("<Control-s>", lambda e: (self.cmd_save(), "break")[1])
        self.bind("<Control-o>", lambda e: (self.cmd_open(), "break")[1])
        self.bind("<Control-n>", lambda e: (self.cmd_new(), "break")[1])
        self.bind("<Control-plus>", lambda e: self.zoom(1))
        self.bind("<Control-equal>", lambda e: self.zoom(1))
        self.bind("<Control-minus>", lambda e: self.zoom(-1))
        ed = self.editor
        ed.bind("<Control-MouseWheel>", lambda e: (self.zoom(1 if e.delta > 0 else -1), "break")[1])
        ed.bind("<Control-a>", lambda e: (ed.tag_add("sel", "1.0", "end-1c"), "break")[1])
        ed.bind("<Tab>", self.on_tab)
        ed.bind("<Return>", self.on_return)
        ed.bind("<KeyPress-braceright>", self.on_close_brace)

    def on_tab(self, e):
        self.editor.insert("insert", "    ")
        return "break"

    def on_return(self, e):
        line = self.editor.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group()
        if line.rstrip().endswith("{"):
            indent += "    "
        self.editor.insert("insert", "\n" + indent)
        self.editor.see("insert")
        return "break"

    def on_close_brace(self, e):
        before = self.editor.get("insert linestart", "insert")
        if before.strip() == "" and before.endswith("    "):
            self.editor.delete("insert-4c", "insert")

    # ------------------------------------------------------------------ text helpers
    def src(self):
        return self.editor.get("1.0", "end-1c")

    def set_text(self, content, path=None):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self.editor.edit_reset()
        self.editor.mark_set("insert", "1.0")
        self.path = path
        self._saved = content
        self.highlight()
        self.check_now()
        self.update_title()
        self.draw_gutter()

    @property
    def modified(self):
        return self.src() != self._saved

    def update_title(self):
        name = os.path.basename(self.path) if self.path else "Untitled"
        self.title(f"{name}{' *' if self.modified else ''} \u2014 {APP_NAME}")
        self.refresh_pos()

    # ------------------------------------------------------------------ highlighting & checking
    def highlight(self):
        ed = self.editor
        text = self.src()
        for tag in ("comment", "string", "number", "keyword", "builtin", "funcname", "operator", "bad"):
            ed.tag_remove(tag, "1.0", "end")
        starts = [0] + [m.end() for m in re.finditer("\n", text)]

        def idx(o):
            ln = bisect.bisect_right(starts, o) - 1
            return f"{ln + 1}.{o - starts[ln]}"

        ranges, prev_fn = {}, False
        for m in SPEC.finditer(text):
            kind = m.lastgroup
            if kind in ("SKIP", "NEWLINE"):
                continue
            tag = None
            if kind == "COMMENT": tag = "comment"
            elif kind == "NUMBER": tag = "number"
            elif kind == "STRING": tag = "string"
            elif kind == "OP": tag = "operator"
            elif kind == "BAD": tag = "bad"
            elif kind == "IDENT":
                w = m.group()
                if prev_fn: tag = "funcname"
                elif w in KEYWORDS: tag = "keyword"
                elif w in BUILTINS: tag = "builtin"
            prev_fn = kind == "IDENT" and m.group() == "fn"
            if tag:
                ranges.setdefault(tag, []).extend((idx(m.start()), idx(m.end())))
        for tag, r in ranges.items():
            ed.tag_add(tag, *r)

    def on_text_changed(self, e=None):
        self.highlight()
        self.update_title()
        if self._check_job:
            self.after_cancel(self._check_job)
        self._check_job = self.after(350, self.check_now)

    def on_change(self, e=None):
        self.draw_gutter()
        self.refresh_pos()

    def check_now(self):
        self._check_job = None
        ed = self.editor
        ed.tag_remove("errline", "1.0", "end")
        ed.tag_remove("errtok", "1.0", "end")
        self.err_lines, self.first_error, self.error_text = set(), None, None
        try:
            compile_source(self.src())
        except TinyError as e:
            line = e.line or 1
            self.err_lines.add(line)
            self.first_error = line
            self.error_text = f"Line {line}  \u2014  {e.kind} error: {e.msg}"
            ed.tag_add("errline", f"{line}.0", f"{line}.end+1c")
            m = re.search(r"'([^']+)'", e.msg)
            if m and e.kind == "Semantic":
                lt = ed.get(f"{line}.0", f"{line}.end")
                w = re.search(r"\b" + re.escape(m.group(1)) + r"\b", lt)
                if w:
                    ed.tag_add("errtok", f"{line}.{w.start()}", f"{line}.{w.end()}")
        self.refresh_status()
        self.draw_gutter()

    def refresh_status(self):
        t = self.t
        if getattr(self, "error_text", None):
            self.status.config(text="\u2716  " + self.error_text + "     (click to jump)", fg=t["bad"], bg=t["bar"])
        else:
            self.status.config(text="\u2714  No problems found", fg=t["ok"], bg=t["bar"])

    def refresh_pos(self):
        ln, col = self.editor.index("insert").split(".")
        self.posinfo.config(text=f"Ln {ln}, Col {int(col) + 1}")

    def draw_gutter(self):
        c, ed, t = self.gutter, self.editor, self.t
        c.delete("all")
        i, guard = ed.index("@0,0"), 0
        while guard < 600:
            guard += 1
            d = ed.dlineinfo(i)
            if d is None:
                break
            ln = int(i.split(".")[0])
            y, h = d[1], d[3]
            if ln in self.err_lines:
                c.create_oval(10, y + h / 2 - 5, 20, y + h / 2 + 5, fill=t["bad"], outline="")
            c.create_text(50, y + h / 2, anchor="e", text=str(ln), font=self.f_code,
                          fill=t["bad"] if ln in self.err_lines else t["gutter_fg"])
            nxt = ed.index(f"{i}+1line")
            if nxt == i:
                break
            i = nxt

    def goto_line(self, n):
        if n:
            self.editor.mark_set("insert", f"{n}.0")
            self.editor.see(f"{n}.0")
            self.editor.focus_set()

    # ------------------------------------------------------------------ output pane
    def out_line(self, text, tag="out"):
        o = self.output
        o.config(state="normal")
        o.insert("end", text + "\n", tag)
        o.see("end")
        o.config(state="disabled")

    def clear_output(self):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")

    def ask(self, prompt):
        value = simpledialog.askstring("Input", prompt or "Enter a value:", parent=self) or ""
        self.out_line(f"{prompt}{value}", "info")
        return value

    def run_code(self):
        self.clear_output()
        self.out_line("\u25b6 Running...", "info")
        t0 = time.perf_counter()
        try:
            prog = compile_source(self.src())
            VM(prog, out=lambda s: self.out_line(s, "out"), inp=self.ask).run()
            self.out_line(f"\u2714 Finished in {(time.perf_counter() - t0) * 1000:.0f} ms", "ok")
        except TinyError as e:
            self.out_line(f"\u2716 {e}", "err")
            self.goto_line(e.line)
        except Exception as e:                       # should not happen, but never crash the IDE
            self.out_line(f"\u2716 Internal error: {e}", "err")

    def _show(self, title, fn):
        self.clear_output()
        self.out_line(title, "head")
        try:
            self.out_line(fn(self.src()), "out")
        except TinyError as e:
            self.out_line(f"\u2716 {e}", "err")
            self.goto_line(e.line)

    def show_bytecode(self):
        self._show("BYTECODE", lambda s: disassemble(compile_source(s)))

    def show_tokens(self):
        self._show("TOKENS (lexer output)",
                   lambda s: "\n".join(f"line {t.line:<3} {t.kind:<8} {t.value!r}" for t in tokenize(s)))

    def show_ast(self):
        self._show("SYNTAX TREE (parser output)",
                   lambda s: pprint.pformat(Parser(tokenize(s)).parse(), width=90))

    def show_guide(self):
        w = tk.Toplevel(self)
        w.title("Tiny language guide")
        w.geometry("640x700")
        t = self.t
        w.configure(bg=t["bg"])
        txt = tk.Text(w, wrap="word", bd=0, padx=18, pady=14, font=("Consolas", 12), bg=t["editor"], fg=t["fg"])
        sb = ttk.Scrollbar(w, orient="vertical", style="Tiny.Vertical.TScrollbar", command=txt.yview)
        txt.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        txt.tag_configure("h", foreground=t["keyword"], font=("Consolas", 12, "bold"))
        for line in GUIDE.splitlines():
            head = line.strip() and line == line.upper() and not line.startswith(" ")
            txt.insert("end", line + "\n", "h" if head else "")
        txt.config(state="disabled")

    # ------------------------------------------------------------------ file commands
    def confirm_discard(self):
        if not self.modified:
            return True
        name = os.path.basename(self.path) if self.path else "Untitled"
        ans = messagebox.askyesnocancel("Unsaved changes", f"Save changes to {name}?", parent=self)
        if ans is None:
            return False
        if ans:
            return self.cmd_save()
        return True

    def cmd_new(self):
        if self.confirm_discard():
            self.set_text("")
            self.clear_output()

    def cmd_example(self, name):
        if self.confirm_discard():
            self.set_text(EXAMPLES[name])
            self.clear_output()
            self.out_line(f"Loaded example: {name}  \u2014  press Run (F5)", "info")

    def load_path(self, p):
        with open(p, encoding="utf-8") as f:
            self.set_text(f.read(), p)

    def cmd_open(self):
        if not self.confirm_discard():
            return
        p = filedialog.askopenfilename(filetypes=[("Tiny programs", "*.tiny"), ("All files", "*.*")])
        if p:
            self.load_path(p)

    def cmd_save(self):
        p = self.path or filedialog.asksaveasfilename(defaultextension=".tiny",
                                                      filetypes=[("Tiny programs", "*.tiny")])
        if not p:
            return False
        with open(p, "w", encoding="utf-8") as f:
            f.write(self.src())
        self.path, self._saved = p, self.src()
        self.update_title()
        self.out_line(f"Saved {p}", "info")
        return True

    def on_close(self):
        if self.confirm_discard():
            self.destroy()


if __name__ == "__main__":
    App().mainloop()