from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MemoFormData:
    title: str
    content: str


@dataclass(frozen=True, slots=True)
class MemoDTO:
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
