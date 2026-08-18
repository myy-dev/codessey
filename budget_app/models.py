"""가계부 데이터 모델."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Transaction:
    """수입 또는 지출 한 건을 표현한다."""

    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """JSON 직렬화가 가능한 딕셔너리로 변환한다."""
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transaction:
        """저장된 딕셔너리에서 거래 객체를 만든다."""
        raw_tags = data.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            date=str(data["date"]),
            amount=int(data["amount"]),
            category=str(data["category"]),
            memo=str(data.get("memo", "")),
            tags=tuple(str(tag) for tag in raw_tags),
        )


@dataclass(frozen=True, slots=True)
class RecurringRule:
    """매월 반복해서 생성할 거래 규칙."""

    id: str
    type: str
    category: str
    amount: int
    day: int
    memo: str = ""
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """JSON 직렬화가 가능한 딕셔너리로 변환한다."""
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecurringRule:
        """저장된 딕셔너리에서 반복 규칙 객체를 만든다."""
        raw_tags = data.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            category=str(data["category"]),
            amount=int(data["amount"]),
            day=int(data["day"]),
            memo=str(data.get("memo", "")),
            tags=tuple(str(tag) for tag in raw_tags),
        )
