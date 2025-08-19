import datetime
import uuid
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

from pydantic import BaseModel, ConfigDict

T = TypeVar('T')


class BaseResponseSchema(BaseModel, Generic[T]):
    data: Optional[T] = None
    success: bool = True
    message: str = ""
    status_code: int = 200


class BaseResponseSchemaExt(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    data: Optional[list[T]] = None
    current_page: int = 0
    page_size: int = 0
    total: int = 0
    success: bool = True
    message: str = ""
    status_code: int = 200

class BaseCursorResponseSchema(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    data: Optional[list[T]] = None
    cursor: Optional[str] = None
    has_more: bool = False
    success: bool = True
    message: str = ""
    status_code: int = 200


