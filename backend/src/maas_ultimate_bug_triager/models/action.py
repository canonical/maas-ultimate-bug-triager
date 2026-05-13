from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    ADD_COMMENT = "ADD_COMMENT"
    SET_STATUS = "SET_STATUS"
    SET_IMPORTANCE = "SET_IMPORTANCE"
    ADD_TAG = "ADD_TAG"
    REMOVE_TAG = "REMOVE_TAG"


class AddCommentAction(BaseModel):
    type: Literal[ActionType.ADD_COMMENT] = ActionType.ADD_COMMENT
    content: str


class SetStatusAction(BaseModel):
    type: Literal[ActionType.SET_STATUS] = ActionType.SET_STATUS
    status: str


class SetImportanceAction(BaseModel):
    type: Literal[ActionType.SET_IMPORTANCE] = ActionType.SET_IMPORTANCE
    importance: str


class AddTagAction(BaseModel):
    type: Literal[ActionType.ADD_TAG] = ActionType.ADD_TAG
    tag: str


class RemoveTagAction(BaseModel):
    type: Literal[ActionType.REMOVE_TAG] = ActionType.REMOVE_TAG
    tag: str


Action = Annotated[
    Union[
        AddCommentAction,
        SetStatusAction,
        SetImportanceAction,
        AddTagAction,
        RemoveTagAction,
    ],
    Field(discriminator="type"),
]


class AnalysisResponse(BaseModel):
    bug_id: int
    is_triaged: bool
    reasoning: str
    suggested_actions: list[Action]


class ActionsRequest(BaseModel):
    actions: list[Action]


class ApplyActionsResponse(BaseModel):
    bug_id: int
    applied: list[str]
    errors: list[dict]
