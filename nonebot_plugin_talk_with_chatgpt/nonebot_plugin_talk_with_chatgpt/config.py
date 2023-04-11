from json import dump, load
from os import makedirs, path
from nonebot import get_bot, get_bots, get_driver
from nonebot.log import logger
from pydantic import BaseModel, Extra
from nonebot.adapters import Bot
from typing import Optional, List, Dict
from asyncio import Queue
from httpx import AsyncClient


class Config(BaseModel, extra=Extra.ignore):
    # access_token
    talk_with_chatgpt_accesstoken: str = ""
    # http代理
    talk_with_chatgpt_http_proxy: Optional[str] = None

    # 触发对话的命令前缀，群聊直接艾特也可以触发
    talk_with_chatgpt_start_cmd: str = "talk"
    # 重置对话，就是清空聊天记录
    talk_with_chatgpt_clear_cmd: str = "clear"
    # 设置预设
    talk_with_chatgpt_prompt_cmd: str = "prompt"
    # 处理消息时是否提示
    talk_with_chatgpt_reply_notice: bool = True
    # 群聊是否共享会话
    talk_with_chatgpt_group_share: bool = False

    # 请求超时时间
    talk_with_chatgpt_timeout: int = 60
    # chatgpt反代地址
    talk_with_chatgpt_api_addr: str = "https://bypass.churchless.tech/api/conversation"
    # chatgpt模型
    talk_with_chatgpt_api_model: str = "text-davinci-002-render-sha"

    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） [1234, 5678, 6666]
    talk_with_chatgpt_bot_qqnum_list: List[str] = []  # 可选
    # 插件数据文件名
    talk_with_chatgpt_data: str = "talk_with_chatgpt.json"


driver = get_driver()
global_config = driver.config
pc = Config.parse_obj(global_config)


class Global_var:
    # 处理消息的bot
    handle_bot: Optional[Bot] = None
    # 会话数据   qqnum/groupnum_qqnum  conversation_id   parent_msg_id   prompt
    session_data: Dict[str, List[str]] = dict()
    # 请求队列
    queue: Optional[Queue] = None
    # 异步task强引用
    background_tasks = set()
    # httpx请求对象
    httpx_client = AsyncClient(
        headers={
            "Authorization": f"Bearer {pc.talk_with_chatgpt_accesstoken}",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        },
        proxies=pc.talk_with_chatgpt_http_proxy,
        timeout=pc.talk_with_chatgpt_timeout,
    )


var = Global_var()


def read_data():
    """
    读取数据
    """
    with open(f"data/{pc.talk_with_chatgpt_data}", "r", encoding="utf-8") as r:
        var.session_data = load(r)


@driver.on_startup
async def _():
    """
    启动时执行
    """
    if not pc.talk_with_chatgpt_accesstoken:
        logger.critical(f"ChatGpt accessToken 未配置！")
    if not pc.talk_with_chatgpt_http_proxy:
        logger.warning(f"ChatGpt http proxy 未配置！")
    if path.exists(f"data/{pc.talk_with_chatgpt_data}"):
        read_data()
    else:
        if not path.exists("data"):
            makedirs("data")


@driver.on_shutdown
async def _():
    """
    关闭时执行
    """
    with open(f"data/{pc.talk_with_chatgpt_data}", "w", encoding="utf-8") as w:
        dump(
            var.session_data,
            w,
            indent=4,
            ensure_ascii=False,
        )


# qq机器人连接时执行
@driver.on_bot_connect
async def _(bot: Bot):
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if (
        pc.talk_with_chatgpt_bot_qqnum_list
        and bot.self_id in pc.talk_with_chatgpt_bot_qqnum_list
    ):
        # 如果已经有bot连了
        if var.handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.talk_with_chatgpt_bot_qqnum_list.index(
                var.handle_bot.self_id
            )
            # 新连接的bot qq 下标
            new_bot_id_index = pc.talk_with_chatgpt_bot_qqnum_list.index(bot.self_id)
            # 判断优先级，下标越低优先级越高
            if new_bot_id_index < handle_bot_id_index:
                var.handle_bot = bot

        # 没bot连就直接给
        else:
            var.handle_bot = bot

    # 不写就给第一个连的
    elif not pc.talk_with_chatgpt_bot_qqnum_list and not var.handle_bot:
        var.handle_bot = bot


# qq机器人断开时执行
@driver.on_bot_disconnect
async def _(bot: Bot):
    # 判断掉线的是否为handle bot
    if bot == var.handle_bot:
        # 如果有写bot qq列表
        if pc.talk_with_chatgpt_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id
                for bot_id in get_bots()
                if bot_id in pc.talk_with_chatgpt_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.talk_with_chatgpt_bot_qqnum_list.index(
                    available_bot_id_list[0]
                )
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.talk_with_chatgpt_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                var.handle_bot = get_bot(
                    pc.talk_with_chatgpt_bot_qqnum_list[new_bot_index]
                )
            else:
                var.handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif var.handle_bot:
            try:
                new_bot = get_bot()
                var.handle_bot = new_bot
            except ValueError:
                var.handle_bot = None
