from __future__ import annotations

from sqlalchemy.types import UserDefinedType


class Vector(UserDefinedType):
    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **kw) -> str:
        return f"VECTOR({self.dimensions})"

    def bind_processor(self, dialect):  # type: ignore[override]
        def process(value):
            if value is None:
                return None
            return [float(item) for item in value]

        return process

    def result_processor(self, dialect, coltype):  # type: ignore[override]
        def process(value):
            if value is None:
                return None
            return [float(item) for item in value]

        return process
