from collections.abc import Generator

type ValidValue = str | int | float | bool

__all__ = ["ResultSet"]

class ResultSet:
    def get_points(
        self,
        measurement: str | None = None,
        tags: dict[str, ValidValue] | None = None,
    ) -> Generator[dict[str, str]]: ...
