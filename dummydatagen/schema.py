import sqlite3
from dataclasses import dataclass, field


@dataclass
class ColumnInfo:
    name: str
    decl_type: str
    affinity: str
    not_null: bool
    is_pk: bool
    pk_seq: int
    default_value: object


@dataclass
class ForeignKeyInfo:
    from_column: str
    to_table: str
    to_column: str


@dataclass
class TableInfo:
    name: str
    columns: list = field(default_factory=list)
    foreign_keys: list = field(default_factory=list)
    unique_columns: set = field(default_factory=set)

    def pk_columns(self):
        return [c for c in self.columns if c.is_pk]

    def single_integer_pk(self):
        """Return the ColumnInfo for a single-column INTEGER PK (rowid alias), else None."""
        pks = self.pk_columns()
        if len(pks) == 1 and pks[0].affinity == "INTEGER":
            return pks[0]
        return None


def get_type_affinity(decl_type):
    """Implements SQLite's type affinity rules (see sqlite.org/datatype3.html)."""
    t = (decl_type or "").upper()
    if "INT" in t:
        return "INTEGER"
    if "CHAR" in t or "CLOB" in t or "TEXT" in t:
        return "TEXT"
    if "BLOB" in t or t == "":
        return "BLOB"
    if "REAL" in t or "FLOA" in t or "DOUB" in t:
        return "REAL"
    return "NUMERIC"


def get_table_names(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def get_columns(conn, table):
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    columns = []
    for cid, name, decl_type, notnull, dflt_value, pk in rows:
        columns.append(
            ColumnInfo(
                name=name,
                decl_type=decl_type,
                affinity=get_type_affinity(decl_type),
                not_null=bool(notnull),
                is_pk=bool(pk),
                pk_seq=pk,
                default_value=dflt_value,
            )
        )
    return columns


def get_foreign_keys(conn, table):
    rows = conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
    fks = []
    for row in rows:
        # id, seq, table, from, to, on_update, on_delete, match
        _id, _seq, to_table, from_col, to_col = row[0], row[1], row[2], row[3], row[4]
        fks.append(ForeignKeyInfo(from_column=from_col, to_table=to_table, to_column=to_col))
    return fks


def get_unique_columns(conn, table):
    """Return single-column UNIQUE-indexed column names for a table."""
    unique_cols = set()
    index_rows = conn.execute(f'PRAGMA index_list("{table}")').fetchall()
    for row in index_rows:
        # seq, name, unique, origin, partial
        index_name, is_unique = row[1], row[2]
        if not is_unique:
            continue
        info_rows = conn.execute(f'PRAGMA index_info("{index_name}")').fetchall()
        if len(info_rows) == 1:
            unique_cols.add(info_rows[0][2])  # column name
    return unique_cols


def load_schema(conn):
    schema = {}
    for table in get_table_names(conn):
        schema[table] = TableInfo(
            name=table,
            columns=get_columns(conn, table),
            foreign_keys=get_foreign_keys(conn, table),
            unique_columns=get_unique_columns(conn, table),
        )
    return schema
