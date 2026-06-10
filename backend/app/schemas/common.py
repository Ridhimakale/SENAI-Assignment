from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


class ErrorBody(BaseModel):
    error_code: str
    message: str
    details: object = Field(default_factory=dict)


class ApiResponse(BaseModel, Generic[DataT]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = True
    data: DataT
    meta: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody
