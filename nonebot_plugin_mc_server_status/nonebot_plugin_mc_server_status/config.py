from json import dump, load
from os import makedirs, path
from typing import List, Optional

from nonebot import get_bot, get_bots, get_driver, get_plugin_config
from nonebot.adapters import Bot
from pydantic import BaseModel


class Config(BaseModel):
    # 管理员的QQ号（别问我为什么）
    mc_status_admin_qqnum: List[int] = []  # 必填
    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） ['1234','5678','6666']
    mc_status_bot_qqnum_list: List[str] = []  # 可选
    # 数据文件名
    mc_status_data_filename: str = "mc_status_data.json"


class Var:
    # 处理消息的bot
    handle_bot: Optional[Bot] = None
    # {"123456": {"提肛": ["mc.hypixel.net:25565","java"]}}
    group_list = {}


driver = get_driver()
pc = get_plugin_config(Config)
var = Var()


@driver.on_startup
async def on_startup():
    if not path.exists(f"data"):
        makedirs(f"data")

    if not path.exists(f"data/{pc.mc_status_data_filename}"):
        save_file()
    else:
        load_file()


def load_file():
    with open(f"data/{pc.mc_status_data_filename}", "r", encoding="utf-8") as r:
        tmp_data = load(r)
        for i in tmp_data:
            var.group_list[int(i)] = tmp_data[i]


def save_file():
    with open(f"data/{pc.mc_status_data_filename}", "w", encoding="utf-8") as w:
        dump(var.group_list, w, indent=4, ensure_ascii=False)


# qq机器人连接时执行
@driver.on_bot_connect
async def on_bot_connect(bot: Bot):
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if pc.mc_status_bot_qqnum_list and bot.self_id in pc.mc_status_bot_qqnum_list:
        # 如果已经有bot连了
        if var.handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.mc_status_bot_qqnum_list.index(
                var.handle_bot.self_id
            )
            # 新连接的bot qq 下标
            new_bot_id_index = pc.mc_status_bot_qqnum_list.index(bot.self_id)
            # 判断优先级，下标越低优先级越高
            if new_bot_id_index < handle_bot_id_index:
                var.handle_bot = bot

        # 没bot连就直接给
        else:
            var.handle_bot = bot

    # 不写就给第一个连的
    elif not pc.mc_status_bot_qqnum_list and not var.handle_bot:
        var.handle_bot = bot


# qq机器人断开时执行
@driver.on_bot_disconnect
async def on_bot_disconnect(bot: Bot):
    # 判断掉线的是否为handle bot
    if bot == var.handle_bot:
        # 如果有写bot qq列表
        if pc.mc_status_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id for bot_id in get_bots() if bot_id in pc.mc_status_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.mc_status_bot_qqnum_list.index(
                    available_bot_id_list[0]
                )
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.mc_status_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                var.handle_bot = get_bot(pc.mc_status_bot_qqnum_list[new_bot_index])

            else:
                var.handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif var.handle_bot:
            try:
                new_bot = get_bot()
                var.handle_bot = new_bot
            except ValueError:
                var.handle_bot = None
