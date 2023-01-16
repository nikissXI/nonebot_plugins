from json import dump, load
from os import makedirs, path
from pathlib import Path
from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, Extra
from nonebot.adapters import Bot


class Config(BaseModel, extra=Extra.ignore):
    # 使用用户qq号 [1234, 5678]
    nya_cook_user_list: list[int] = []
    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） ['1234','5678','6666']
    nya_cook_bot_qqnum_list: list[str] = []  # 可选
    # 插件数据文件名
    nya_cook_data_filename: str = "nya_cook_data.json"
    # 字体文件路径
    nya_cook_menu_font_path: str = f"{Path(__file__).parent}/font/HYWenHei-85W.ttf"


class Global_var:
    # 菜谱数据  {id : tuple[菜名，内容]}
    cook_menu_data_dict: dict[str, tuple[str, str]] = {}


driver = get_driver()
global_config = driver.config
pc = Config.parse_obj(global_config)
var = Global_var()
handle_bot: None | Bot = None


def read_data():
    """
    读取数据
    """
    with open(f"data/{pc.nya_cook_data_filename}", "r", encoding="utf-8") as r:
        var.cook_menu_data_dict.clear()
        var.cook_menu_data_dict = load(r)


def save_data():
    """
    保存数据
    """
    with open(f"data/{pc.nya_cook_data_filename}", "w", encoding="utf-8") as w:
        dump(
            var.cook_menu_data_dict,
            w,
            indent=4,
            ensure_ascii=False,
        )


@driver.on_startup
async def on_startup():
    """
    启动时执行
    """
    if path.exists(f"data/{pc.nya_cook_data_filename}"):
        read_data()
    else:
        if not path.exists("data"):
            makedirs("data")
        save_data()
