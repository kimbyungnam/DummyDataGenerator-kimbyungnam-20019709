def build_insert_sql(table_name, columns):
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join("?" for _ in columns)
    return f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'


def insert_row(conn, table, row, dry_run=False):
    """Insert a single row dict. Returns the row's primary key value.

    If the table has an auto-increment integer PK (absent from `row`), returns
    cursor.lastrowid. Otherwise returns the value of the declared PK column(s)
    already present in `row`.
    """
    columns = list(row.keys())
    sql = build_insert_sql(table.name, columns)
    values = [row[c] for c in columns]

    if dry_run:
        print(f"{sql}  -- {values}")
        auto_pk = table.single_integer_pk()
        if auto_pk is not None:
            return None
        pks = table.pk_columns()
        if len(pks) == 1:
            return row.get(pks[0].name)
        return None

    cursor = conn.execute(sql, values)
    auto_pk = table.single_integer_pk()
    if auto_pk is not None:
        return cursor.lastrowid
    pks = table.pk_columns()
    if len(pks) == 1:
        return row.get(pks[0].name)
    return None
