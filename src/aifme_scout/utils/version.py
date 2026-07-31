"""Version helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Version:
    """Semantic version."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, value: str) -> "Version":
        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version string: {value}")
        try:
            return cls(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError as exc:
            raise ValueError(f"Invalid version string: {value}") from exc
