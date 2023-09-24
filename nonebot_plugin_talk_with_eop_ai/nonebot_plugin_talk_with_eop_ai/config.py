from ujson import dump, load
from os import makedirs, path
from nonebot import get_bot, get_bots, get_driver
from nonebot.log import logger
from pydantic import BaseModel, Extra
from nonebot.adapters import Bot
from typing import Optional, List, Dict
from asyncio import Queue
from httpx import AsyncClient
from hashlib import sha256


class Config(BaseModel, extra=Extra.ignore):
    # auth
    poe_ai_user: str = ""
    poe_ai_passwd: str = ""
    # base url
    poe_ai_base_url: str = "https://api.eop.nikiss.top"

    # 处理消息时是否提示
    poe_ai_reply_notice: bool = False
    # 群聊是否共享会话
    poe_ai_group_share: bool = True
    # 是否默认允许所有群聊使用，否则需要使用命令启用
    poe_ai_all_group_enable: bool = False

    # 群聊艾特是否响应
    poe_ai_talk_at: bool = False
    # 触发对话的命令前缀，群聊直接艾特也可以触发
    poe_ai_talk_cmd: str = "/talk"
    # 私聊沉浸式对话触发命令
    poe_ai_talk_p_cmd: str = "/hi"
    # 重置对话，就是清空聊天记录
    poe_ai_reset_cmd: str = "/reset"
    # 如果关闭所有群聊使用，启用该群的命令
    poe_ai_group_enable_cmd: str = "/poeai"

    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） [1234, 5678, 6666]  ["all"]则全部响应
    poe_ai_bot_qqnum_list: List[str] = []  # 可选
    # 插件数据文件名
    poe_ai_data: str = "poe_ai.json"


driver = get_driver()
global_config = driver.config
pc = Config.parse_obj(global_config)


class Global_var:
    # 处理消息的bot
    handle_bot: Optional[Bot] = None
    # 启用群
    enable_group_list: List[int] = []
    # 会话数据   qqnum/groupnum_qqnum  :  eop id
    session_data: Dict[str, str] = dict()
    # 请求队列
    queue: Optional[Queue] = None
    # 异步task强引用
    background_tasks = set()
    # httpx
    httpx_client = AsyncClient(
        base_url=pc.poe_ai_base_url,
        headers={},
        timeout=20,
    )
    access_token = ""


var = Global_var()


def read_data():
    """
    读取数据
    """
    with open(f"data/{pc.poe_ai_data}", "r", encoding="utf-8") as r:
        (
            var.enable_group_list,
            var.session_data,
        ) = load(r)


async def login() -> bool:
    hash_object = sha256()
    hash_object.update(pc.poe_ai_passwd.encode("utf-8"))
    resp = await var.httpx_client.post(
        "/user/login", json={"user": pc.poe_ai_user, "passwd": hash_object.hexdigest()}
    )
    if resp.status_code == 200:
        var.access_token = (resp.json())["access_token"]
        var.httpx_client.headers.update({"Authorization": f"Bearer {var.access_token}"})
        return True

    else:
        var.access_token = ""
        logger.error(f"登陆失败 {resp.text}")
        return False


@driver.on_startup
async def _():
    """
    启动时执行
    """
    if path.exists(f"data/{pc.poe_ai_data}"):
        read_data()
    else:
        if not path.exists("data"):
            makedirs("data")

    await login()


@driver.on_shutdown
async def _():
    """
    关闭时执行
    """
    with open(f"data/{pc.poe_ai_data}", "w", encoding="utf-8") as w:
        dump(
            [
                var.enable_group_list,
                var.session_data,
            ],
            w,
            indent=4,
            ensure_ascii=False,
        )


# qq机器人连接时执行
@driver.on_bot_connect
async def _(bot: Bot):
    if pc.poe_ai_bot_qqnum_list == ["all"]:
        return
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if pc.poe_ai_bot_qqnum_list and bot.self_id in pc.poe_ai_bot_qqnum_list:
        # 如果已经有bot连了
        if var.handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.poe_ai_bot_qqnum_list.index(var.handle_bot.self_id)
            # 新连接的bot qq 下标
            new_bot_id_index = pc.poe_ai_bot_qqnum_list.index(bot.self_id)
            # 判断优先级，下标越低优先级越高
            if new_bot_id_index < handle_bot_id_index:
                var.handle_bot = bot

        # 没bot连就直接给
        else:
            var.handle_bot = bot

    # 不写就给第一个连的
    elif not pc.poe_ai_bot_qqnum_list and not var.handle_bot:
        var.handle_bot = bot


# qq机器人断开时执行
@driver.on_bot_disconnect
async def _(bot: Bot):
    if pc.poe_ai_bot_qqnum_list == ["all"]:
        return
    # 判断掉线的是否为handle bot
    if bot == var.handle_bot:
        # 如果有写bot qq列表
        if pc.poe_ai_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id for bot_id in get_bots() if bot_id in pc.poe_ai_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.poe_ai_bot_qqnum_list.index(available_bot_id_list[0])
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.poe_ai_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                var.handle_bot = get_bot(pc.poe_ai_bot_qqnum_list[new_bot_index])
            else:
                var.handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif var.handle_bot:
            try:
                new_bot = get_bot()
                var.handle_bot = new_bot
            except ValueError:
                var.handle_bot = None
