class TinyError(Exception):
    """Any error in a Tiny program: Lexical, Syntax, Semantic or Runtime."""
    def __init__(self, kind, msg, line=None):
        self.kind, self.msg, self.line = kind, msg, line
        loc = f" (line {line})" if line else ""
        super().__init__(f"{kind} error{loc}: {msg}")