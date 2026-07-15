class DummyDataGenError(Exception):
    """Base error for dummydatagen."""


class CycleError(DummyDataGenError):
    def __init__(self, cycle_tables):
        self.cycle_tables = cycle_tables
        super().__init__(
            f"Circular foreign key dependency detected among tables: {sorted(cycle_tables)}"
        )


class UnsupportedTypeError(DummyDataGenError):
    pass


class UniqueRetryExceeded(DummyDataGenError):
    def __init__(self, table, column, attempts):
        super().__init__(
            f"Could not generate a unique value for {table}.{column} after {attempts} attempts"
        )


class EmptyFKPoolError(DummyDataGenError):
    def __init__(self, table, column, referenced_table):
        super().__init__(
            f"Cannot generate rows for {table}.{column}: referenced table "
            f"'{referenced_table}' has no rows. Populate it first (check --tables/--rows)."
        )
