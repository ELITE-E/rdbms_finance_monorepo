from __future__ import annotations

from dataclasses import dataclass

from .ast import (
    Assignment,
    ColumnDef,
    ColumnRef,
    Condition,
    CreateIndex,
    CreateTable,
    Delete,
    Insert,
    JoinClause,
    Select,
    Statement,
    TypeSpec,
    Update,
    WhereClause,
)
from .errors import Position, SqlSyntaxError
from .lexer import Token, TokenType, tokenize


@dataclass
class Parser:
    tokens: list[Token]
    i: int = 0

    def peek(self, offset: int = 0) -> Token:
        j = self.i + offset
        if j >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[j]

    def at(self, typ: TokenType) -> bool:
        return self.peek().typ == typ

    def consume(self) -> Token:
        t = self.peek()
        self.i += 1
        return t

    def expect(self, typ: TokenType, msg: str) -> Token:
        t = self.peek()
        if t.typ != typ:
            raise SqlSyntaxError(msg, t.pos)
        return self.consume()

    def match(self, typ: TokenType) -> bool:
        if self.at(typ):
            self.consume()
            return True
        return False

    def parse_script(self) -> list[Statement]:
        """
        Parse one or more statements separated by semicolons.
        Trailing semicolons are allowed.
        """
        stmts: list[Statement] = []
        while not self.at(TokenType.EOF):
            # allow empty statements (e.g., ";;")
            if self.match(TokenType.SEMI):
                continue
            stmts.append(self.parse_statement())
            self.match(TokenType.SEMI)
        return stmts

    def parse_one(self) -> Statement:
        stmts = self.parse_script()
        if not stmts:
            raise SqlSyntaxError("Empty input", Position(1, 1))
        if len(stmts) > 1:
            raise SqlSyntaxError("Expected a single statement", self.peek().pos)
        return stmts[0]

    # ---------------- Statement dispatch ----------------

    def parse_statement(self) -> Statement:
        t = self.peek()

        if t.typ == TokenType.CREATE:
            return self.parse_create()

        if t.typ == TokenType.INSERT:
            return self.parse_insert()

        if t.typ == TokenType.SELECT:
            return self.parse_select()

        if t.typ == TokenType.UPDATE:
            return self.parse_update()

        if t.typ == TokenType.DELETE:
            return self.parse_delete()

        raise SqlSyntaxError(f"Unexpected token: {t.lexeme!r}", t.pos)

    # ---------------- CREATE ----------------

    def parse_create(self) -> Statement:
        self.expect(TokenType.CREATE, "Expected CREATE")

        if self.match(TokenType.TABLE):
            return self.parse_create_table_after_keyword()

        if self.match(TokenType.INDEX):
            return self.parse_create_index_after_keyword()

        raise SqlSyntaxError("Expected TABLE or INDEX after CREATE", self.peek().pos)

    def parse_create_table_after_keyword(self) -> CreateTable:
        table = self.expect(TokenType.IDENT, "Expected table name").value  # type: ignore[assignment]
        self.expect(TokenType.LPAREN, "Expected '(' after table name")

        cols: list[ColumnDef] = []
        cols.append(self.parse_column_def())

        while self.match(TokenType.COMMA):
            cols.append(self.parse_column_def())

        self.expect(TokenType.RPAREN, "Expected ')' after column definitions")
        return CreateTable(table_name=str(table), columns=cols)

    def parse_column_def(self) -> ColumnDef:
        col_name = self.expect(TokenType.IDENT, "Expected column name").value
        typ = self.parse_type_spec()

        not_null = False
        unique = False
        primary_key = False

        # constraints can appear in any order
        while True:
            if self.match(TokenType.NOT):
                self.expect(TokenType.NULL, "Expected NULL after NOT")
                not_null = True
                continue

            if self.match(TokenType.UNIQUE):
                unique = True
                continue

            if self.match(TokenType.PRIMARY):
                self.expect(TokenType.KEY, "Expected KEY after PRIMARY")
                primary_key = True
                continue

            break

        return ColumnDef(
            name=str(col_name),
            typ=typ,
            not_null=not_null,
            unique=unique,
            primary_key=primary_key,
        )

    def parse_type_spec(self) -> TypeSpec:
        """
        TYPE := IDENT [ '(' INT (',' INT)* ')' ]
        Example: VARCHAR(255)
        """
        type_name = self.expect(TokenType.IDENT, "Expected type name").value
        params: list[int] = []
        if self.match(TokenType.LPAREN):
            params.append(int(self.expect(TokenType.INT, "Expected integer type parameter").value))  # type: ignore[arg-type]
            while self.match(TokenType.COMMA):
                params.append(int(self.expect(TokenType.INT, "Expected integer type parameter").value))  # type: ignore[arg-type]
            self.expect(TokenType.RPAREN, "Expected ')' after type parameters")
        return TypeSpec(name=str(type_name).upper(), params=params)

    def parse_create_index_after_keyword(self) -> CreateIndex:
        idx_name = self.expect(TokenType.IDENT, "Expected index name").value
        self.expect(TokenType.ON, "Expected ON after index name")
        table = self.expect(TokenType.IDENT, "Expected table name").value

        self.expect(TokenType.LPAREN, "Expected '(' after table name")
        col = self.expect(TokenType.IDENT, "Expected column name").value
        self.expect(TokenType.RPAREN, "Expected ')' after column name")

        return CreateIndex(index_name=str(idx_name), table_name=str(table), column_name=str(col))

    # ---------------- INSERT ----------------

    def parse_insert(self) -> Insert:
        self.expect(TokenType.INSERT, "Expected INSERT")
        self.expect(TokenType.INTO, "Expected INTO after INSERT")
        table = self.expect(TokenType.IDENT, "Expected table name").value

        self.expect(TokenType.LPAREN, "Expected '(' before column list")
        cols = [str(self.expect(TokenType.IDENT, "Expected column name").value)]
        while self.match(TokenType.COMMA):
            cols.append(str(self.expect(TokenType.IDENT, "Expected column name").value))
        self.expect(TokenType.RPAREN, "Expected ')' after column list")

        self.expect(TokenType.VALUES, "Expected VALUES")
        self.expect(TokenType.LPAREN, "Expected '(' before values")
        vals = [self.parse_literal()]
        while self.match(TokenType.COMMA):
            vals.append(self.parse_literal())
        self.expect(TokenType.RPAREN, "Expected ')' after values")

        if len(cols) != len(vals):
            raise SqlSyntaxError("Number of columns does not match number of values", self.peek().pos)

        return Insert(table_name=str(table), columns=cols, values=vals)

    # ---------------- SELECT (+ JOIN, WHERE) ----------------

    def parse_select(self) -> Select:
        self.expect(TokenType.SELECT, "Expected SELECT")

        cols = self.parse_select_list()
        self.expect(TokenType.FROM, "Expected FROM")
        from_table = str(self.expect(TokenType.IDENT, "Expected table name").value)

        joins: list[JoinClause] = []
        while self.match(TokenType.JOIN):
            joins.append(self.parse_join_clause())

        where = None
        if self.match(TokenType.WHERE):
            where = self.parse_where_clause_after_where()

        return Select(columns=cols, from_table=from_table, joins=joins, where=where)

    def parse_select_list(self) -> list[ColumnRef] | None:
        # None represents "*"
        if self.match(TokenType.STAR):
            return None

        cols = [self.parse_column_ref()]
        while self.match(TokenType.COMMA):
            cols.append(self.parse_column_ref())
        return cols

    def parse_join_clause(self) -> JoinClause:
        table = str(self.expect(TokenType.IDENT, "Expected table name after JOIN").value)
        self.expect(TokenType.ON, "Expected ON in JOIN clause")
        left = self.parse_column_ref()
        self.expect(TokenType.EQ, "Expected '=' in JOIN condition")
        right = self.parse_column_ref()
        return JoinClause(table_name=table, left=left, right=right)

    # ---------------- UPDATE ----------------

    def parse_update(self) -> Update:
        self.expect(TokenType.UPDATE, "Expected UPDATE")
        table = str(self.expect(TokenType.IDENT, "Expected table name").value)
        self.expect(TokenType.SET, "Expected SET")

        assignments = [self.parse_assignment()]
        while self.match(TokenType.COMMA):
            assignments.append(self.parse_assignment())

        where = None
        if self.match(TokenType.WHERE):
            where = self.parse_where_clause_after_where()

        return Update(table_name=table, assignments=assignments, where=where)

    def parse_assignment(self) -> Assignment:
        col = str(self.expect(TokenType.IDENT, "Expected column name").value)
        self.expect(TokenType.EQ, "Expected '=' in assignment")
        val = self.parse_literal()
        return Assignment(column=col, value=val)

    # ---------------- DELETE ----------------

    def parse_delete(self) -> Delete:
        self.expect(TokenType.DELETE, "Expected DELETE")
        self.expect(TokenType.FROM, "Expected FROM after DELETE")
        table = str(self.expect(TokenType.IDENT, "Expected table name").value)

        where = None
        if self.match(TokenType.WHERE):
            where = self.parse_where_clause_after_where()

        return Delete(table_name=table, where=where)

    # ---------------- WHERE helpers ----------------

    def parse_where_clause_after_where(self) -> WhereClause:
        conds = [self.parse_condition()]
        while self.match(TokenType.AND):
            conds.append(self.parse_condition())
        return WhereClause(conditions=conds)

    def parse_condition(self) -> Condition:
        left = self.parse_column_ref()
        self.expect(TokenType.EQ, "Expected '=' in WHERE condition")
        right = self.parse_literal()
        return Condition(left=left, op="=", right=right)

    # ---------------- atoms ----------------

    def parse_column_ref(self) -> ColumnRef:
        """
        column_ref := IDENT | IDENT '.' IDENT
        """
        first = self.expect(TokenType.IDENT, "Expected identifier").value
        if self.match(TokenType.DOT):
            second = self.expect(TokenType.IDENT, "Expected identifier after '.'").value
            return ColumnRef(table=str(first), column=str(second))
        return ColumnRef(table=None, column=str(first))

    def parse_literal(self):
        t = self.peek()
        if t.typ == TokenType.INT:
            return int(self.consume().value)  # type: ignore[arg-type]
        if t.typ == TokenType.STRING:
            return str(self.consume().value)
        if t.typ == TokenType.BOOL:
            return bool(self.consume().value)
        raise SqlSyntaxError(" literal (INT, STRING, BOOL)", t.pos)


# -------- public helpers --------

def parse_sql(sql: str) -> Statement:
    tokens = tokenize(sql)
    return Parser(tokens).parse_one()


def parse_script(sql: str) -> list[Statement]:
    tokens = tokenize(sql)
    return Parser(tokens).parse_script()