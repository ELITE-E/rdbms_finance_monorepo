Step 1 — Tokenizer / Lexer (IMPLEMENTED)
Step Goal
Convert raw SQL-like strings into tokens (keywords, identifiers, literals, punctuation) with positions for good errors.

What was implemented
TokenType enum
Token dataclass
tokenize(sql) -> list[Token]
Syntax error on unterminated string / unknown characters