from collections.abc import Callable

from sqlalchemy import Enum as SAEnum


def enum_type(enum_class: type, *, name: str) -> SAEnum:
    return SAEnum(
        enum_class,
        name=name,
        values_callable=lambda enum_cls: [member.value for member in enum_cls],
    )
