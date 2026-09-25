from datetime import datetime
from typing import Literal

type ValidValue = str | int | float | bool

def quote_ident(value: str) -> str: ...
def make_line(
    measurement: str,
    tags: dict[str, str] | None = None,
    fields: dict[str, ValidValue] | None = None,
    time: str | datetime | None = None,
    precision: Literal["n", "u", "ms", "s", "m", "h"] | None = None,
) -> str: ...
