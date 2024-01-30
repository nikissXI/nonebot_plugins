from typing import Dict, List, Optional

from httpx import AsyncClient
from nonebot import get_bot, get_bots, get_driver
from nonebot.adapters import Bot
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # 配置文件版本号，不要改
    eop_ai_version: int = 1

    # eop后端url地址，如 https://api.eop.com
    eop_ai_base_addr: str = ""

    # eop登录账号密码
    eop_ai_user: str = ""
    eop_ai_passwd: str = ""

    # 代理地址
    eop_ai_http_proxy_addr: Optional[str] = None

    # AI回答输出类型，填1/2/3其中一个数字，1=文字，2=图片，3=图片+文字（文字在网页粘贴板）
    eop_ai_reply_type: int = 3
    # 图片输出时，图片的宽度
    eop_ai_img_width: int = 400
    # 处理消息时是否提示
    eop_ai_reply_notice: bool = False
    # 群聊是否共享会话
    eop_ai_group_share: bool = True
    # 是否默认允许所有群聊使用，否则需要使用命令启用
    eop_ai_all_group_enable: bool = False
    # 群聊中，机器人的回复是否艾特提问用户，如果eop_ai_group_share为false该选项强制为true
    eop_ai_reply_at_user: bool = True

    # 群聊艾特和发bot昵称是否响应（需要先启用该群的eop ai）
    eop_ai_talk_tome: bool = True
    # 如果关闭所有群聊使用，启用该群的命令
    eop_ai_group_enable_cmd: str = "/eopai"
    # 触发对话的命令前缀，群聊直接艾特也可以触发
    eop_ai_talk_cmd: str = "/talk"
    # 私聊沉浸式对话触发命令
    eop_ai_talk_p_cmd: str = "/hi"
    # 重置对话，就是清空聊天记录
    eop_ai_reset_cmd: str = "/reset"
    # AI回答输出类型切换，仅对使用命令的会话生效
    eop_ai_reply_type_cmd: str = "/reply"

    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） [1234, 5678, 6666]  ["all"]则全部响应
    eop_ai_bot_qqnum_list: List[str] = []  # 可选
    # 插件数据文件名
    eop_ai_data: str = "eop_ai.json"


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
    # 指定回复类型   id  :  int
    reply_type: Dict[str, int] = dict()
    # 会话锁
    session_lock: Dict[str, bool] = {}
    # 粘贴板的csrftoken缓存
    paste_csrftoken: Dict[str, str] = {}
    # httpx
    httpx_client = AsyncClient(
        base_url=pc.eop_ai_base_addr,
        headers={},
        timeout=20,
        proxies=pc.eop_ai_http_proxy_addr,
    )
    access_token = ""


var = Global_var()


# qq机器人连接时执行
@driver.on_bot_connect
async def _(bot: Bot):
    if pc.eop_ai_bot_qqnum_list == ["all"]:
        return
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if pc.eop_ai_bot_qqnum_list and bot.self_id in pc.eop_ai_bot_qqnum_list:
        # 如果已经有bot连了
        if var.handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.eop_ai_bot_qqnum_list.index(var.handle_bot.self_id)
            # 新连接的bot qq 下标
            new_bot_id_index = pc.eop_ai_bot_qqnum_list.index(bot.self_id)
            # 判断优先级，下标越低优先级越高
            if new_bot_id_index < handle_bot_id_index:
                var.handle_bot = bot

        # 没bot连就直接给
        else:
            var.handle_bot = bot

    # 不写就给第一个连的
    elif not pc.eop_ai_bot_qqnum_list and not var.handle_bot:
        var.handle_bot = bot


# qq机器人断开时执行
@driver.on_bot_disconnect
async def _(bot: Bot):
    if pc.eop_ai_bot_qqnum_list == ["all"]:
        return
    # 判断掉线的是否为handle bot
    if bot == var.handle_bot:
        # 如果有写bot qq列表
        if pc.eop_ai_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id for bot_id in get_bots() if bot_id in pc.eop_ai_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.eop_ai_bot_qqnum_list.index(available_bot_id_list[0])
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.eop_ai_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                var.handle_bot = get_bot(pc.eop_ai_bot_qqnum_list[new_bot_index])
            else:
                var.handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif var.handle_bot:
            try:
                new_bot = get_bot()
                var.handle_bot = new_bot
            except ValueError:
                var.handle_bot = None
