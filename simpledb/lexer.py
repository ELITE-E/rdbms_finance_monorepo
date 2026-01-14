from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .errors import Position, SqlSyntaxError


class TokenType(Enum):
    # Special
    EOF = auto()

    # Identifiers + literals
    IDENT = auto()
    INT = auto()
    STRING = auto()
    BOOL = auto()

    # Symbols
    LPAREN = auto()   # (
    RPAREN = auto()   # )
    COMMA = auto()    # ,
    SEMI = auto()     # ;
    EQ = auto()       # =
    STAR = auto()     # *
    DOT = auto()      # .

    # Keywords (Phase 1)
    CREATE = auto()
    TABLE = auto()
    INDEX = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    AND = auto()
    UPDATE = auto()
    SET = auto()
    DELETE = auto()
    JOIN = auto()
    ON = auto()
    PRIMARY = auto()
    KEY = auto()
    UNIQUE = auto()
    NOT = auto()
    NULL = auto()


KEYWORDS: dict[str, TokenType] = {
    "CREATE": TokenType.CREATE,
    "TABLE": TokenType.TABLE,
    "INDEX": TokenType.INDEX,
    "INSERT": TokenType.INSERT,
    "INTO": TokenType.INTO,
    "VALUES": TokenType.VALUES,
    "SELECT": TokenType.SELECT,
    "FROM": TokenType.FROM,
    "WHERE": TokenType.WHERE,
    "AND": TokenType.AND,
    "UPDATE": TokenType.UPDATE,
    "SET": TokenType.SET,
    "DELETE": TokenType.DELETE,
    "JOIN": TokenType.JOIN,
    "ON": TokenType.ON,
    "PRIMARY": TokenType.PRIMARY,
    "KEY": TokenType.KEY,
    "UNIQUE": TokenType.UNIQUE,
    "NOT": TokenType.NOT,
    "NULL": TokenType.NULL,
}


@dataclass(frozen=True)
class Token:
    typ: TokenType
    lexeme: str
    value: object | None
    pos: Position


def tokenize(sql: str) -> list[Token]:
    tokens: list[Token] = []

    i = 0
    line = 1
    col = 1

    def cur_pos() -> Position:
        return Position(line=line, col=col)

    def advance(n: int = 1) -> None:
        nonlocal i, line, col
        for _ in range(n):
            if i >= len(sql):
                return
            ch = sql[i]
            i += 1
            if ch == "\n":
                line += 1
                col = 1
            else:
                col += 1

    def peek(offset: int = 0) -> str:
        j = i + offset
        if j >= len(sql):
            return ""
        return sql[j]

    while i < len(sql):
        ch = peek(0)

        # whitespace
        if ch.isspace():
            advance(1)
            continue

        # symbols
        if ch == "(":
            tokens.append(Token(TokenType.LPAREN, ch, None, cur_pos()))
            advance(1)
            continue
        if ch == ")":
            tokens.append(Token(TokenType.RPAREN, ch, None, cur_pos()))
            advance(1)
            continue
        if ch == ",":
            tokens.append(Token(TokenType.COMMA, ch, None, cur_pos()))
            advance(1)
            continue
        if ch == ";":
            tokens.append(Token(TokenType.SEMI, ch, None, cur_pos()))
            advance(1)
            continue
        if ch == "=":
            tokens.append(Token(TokenType.EQ, ch, None, cur_pos()))
            advance(1)
            continue
        if ch == "*":
            tokens.append(Token(TokenType.STAR, ch, None, cur_pos()))
            advance(1)
            continue
        if ch == ".":
            tokens.append(Token(TokenType.DOT, ch, None, cur_pos()))
            advance(1)
            continue

        # string literal: '...'
        if ch == "'":
            start = cur_pos()
            advance(1)  # consume opening quote
            buf = []
            while True:
                if i >= len(sql):
                    raise SqlSyntaxError("Unterminated string literal", start)
                c = peek(0)
                if c == "'":
                    advance(1)  # closing quote
                    break
                buf.append(c)
                advance(1)
            s = "".join(buf)
            tokens.append(Token(TokenType.STRING, f"'{s}'", s, start))
            continue

        # integer literal
        if ch.isdigit():
            start = cur_pos()
            j = i
            while j < len(sql) and sql[j].isdigit():
                j += 1
            lex = sql[i:j]
            tokens.append(Token(TokenType.INT, lex, int(lex), start))
            advance(j - i)
            continue

        # identifier / keyword / boolean
        if ch.isalpha() or ch == "_":
            start = cur_pos()
            j = i
            while j < len(sql) and (sql[j].isalnum() or sql[j] == "_"):
                j += 1
            lex = sql[i:j]
            upper = lex.upper()

            if upper == "TRUE":
                tokens.append(Token(TokenType.BOOL, lex, True, start))
            elif upper == "FALSE":
                tokens.append(Token(TokenType.BOOL, lex, False, start))
            elif upper in KEYWORDS:
                tokens.append(Token(KEYWORDS[upper], lex, upper, start))
            else:
                tokens.append(Token(TokenType.IDENT, lex, lex, start))

            advance(j - i)
            continue

        # unknown
        raise SqlSyntaxError(f"Unexpected character: {ch!r}", cur_pos())

    tokens.append(Token(TokenType.EOF, "", None, Position(line=line, col=col)))
    return tokens