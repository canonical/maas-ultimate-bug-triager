from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BugSummary(BaseModel):
    id: int
    title: str
    status: str
    importance: str
    owner: str
    date_created: datetime
    tags: list[str]


class Comment(BaseModel):
    author: str
    date: datetime
    content: str


class Attachment(BaseModel):
    id: int
    title: str
    content_type: str | None
    size: int | None


class BugDetail(BugSummary):
    description: str
    comments: list[Comment]
    attachments: list[Attachment]
