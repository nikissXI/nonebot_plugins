from typing import Type, TypeVar

from nonebot.adapters.onebot.v11 import (
    Adapter,
    Event,
    NoticeEvent,
)
from typing_extensions import Literal
from pydantic import BaseModel
from nonebot.typing import overrides

Event_T = TypeVar("Event_T", bound=Type[Event])


def register_event(event: Event_T) -> Event_T:
    Adapter.add_custom_model(event)
    return event


class File(BaseModel):
    name: str
    size: int
    url: str

    class Config:
        extra = "allow"


@register_event
class OfflineUploadNoticeEvent(NoticeEvent):
    """离线文件上传事件"""

    notice_type: Literal["offline_file"]
    user_id: int
    file: File

    @overrides(NoticeEvent)
    def get_session_id(self) -> str:
        return str(self.user_id)

    @overrides(NoticeEvent)
    def get_user_id(self) -> str:
        return str(self.user_id)
