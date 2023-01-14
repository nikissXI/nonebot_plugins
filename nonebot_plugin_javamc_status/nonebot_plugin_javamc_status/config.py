from json import dump, load
from os import makedirs, path
from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # 机器人的QQ号（由于开发者多gocq连接，所以有这个设置）
    mc_status_bot_qqnum: str = "0"  # 必填
    # 管理员的QQ号（别问我为什么）
    mc_status_admin_qqnum: int = 0  # 必填
    # 数据文件名
    mc_status_data_filename: str = "mc_status_data.json"


driver = get_driver()
global_config = driver.config
plugin_config = Config.parse_obj(global_config)
group_list = {}  # {"123456": {"提肛": ["mc.hypixel.net:25565","java"]}}


@driver.on_startup
async def on_startup():
    if not path.exists(f"data"):
        makedirs(f"data")

    if not path.exists(f"data/{plugin_config.mc_status_data_filename}"):
        save_file()
    else:
        load_file()


def load_file():
    with open(
        f"data/{plugin_config.mc_status_data_filename}", "r", encoding="utf-8"
    ) as r:
        tmp_data = load(r)
        for i in tmp_data:
            group_list[int(i)] = tmp_data[i]


def save_file():
    with open(
        f"data/{plugin_config.mc_status_data_filename}", "w", encoding="utf-8"
    ) as w:
        dump(group_list, w, indent=4, ensure_ascii=False)
