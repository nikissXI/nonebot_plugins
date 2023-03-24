from pathlib import Path
from nonebot import get_bot, get_bots, get_driver
from pydantic import BaseModel, Extra
from nonebot.adapters import Bot
from typing import Optional, List


class Config(BaseModel, extra=Extra.ignore):
    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） ['1234','5678','6666']
    nya_music_bot_qqnum_list: List[str] = []  # 可选
    # 字体文件路径
    nya_music_menu_font_path: str = f"{Path(__file__).parent}/font/HYWenHei-85W.ttf"
    # 字体大小
    nya_music_menu_font_size: int = 18
    # 每页返回的结果数量
    nya_music_page_items: int = 10


class Global_var:
    # 处理消息的bot
    handle_bot: Optional[Bot] = None


driver = get_driver()
global_config = driver.config
pc = Config.parse_obj(global_config)
var = Global_var()


@driver.on_startup
async def _():
    """
    启动时执行
    """
    pass


# qq机器人连接时执行
@driver.on_bot_connect
async def _(bot: Bot):
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if pc.nya_music_bot_qqnum_list and bot.self_id in pc.nya_music_bot_qqnum_list:
        # 如果已经有bot连了
        if var.handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.nya_music_bot_qqnum_list.index(
                var.handle_bot.self_id
            )
            # 连过俩的bot qq 下标
            new_bot_id_index = pc.nya_music_bot_qqnum_list.index(bot.self_id)
            # 判断优先级，下标越低优先级越高
            if new_bot_id_index < handle_bot_id_index:
                var.handle_bot = bot

        # 没bot连就直接给
        else:
            var.handle_bot = bot

    # 不写就给第一个连的
    elif not pc.nya_music_bot_qqnum_list and not var.handle_bot:
        var.handle_bot = bot


# qq机器人断开时执行
@driver.on_bot_disconnect
async def _(bot: Bot):
    # 判断掉线的是否为handle bot
    if bot == var.handle_bot:
        # 如果有写bot qq列表
        if pc.nya_music_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id for bot_id in get_bots() if bot_id in pc.nya_music_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.nya_music_bot_qqnum_list.index(
                    available_bot_id_list[0]
                )
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.nya_music_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                var.handle_bot = get_bot(pc.nya_music_bot_qqnum_list[new_bot_index])
            else:
                var.handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif var.handle_bot:
            try:
                new_bot = get_bot()
                var.handle_bot = new_bot
            except ValueError:
                var.handle_bot = None
