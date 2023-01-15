from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） ['1234','5678','6666']
    easy_translate_bot_qqnum_list: list[str] = []  # 可选


plugin_config = Config.parse_obj(get_driver().config)
