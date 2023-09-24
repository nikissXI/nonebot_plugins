from nonebot import on_message, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from .config import pc, var, login
from html import unescape
from nonebot.permission import SUPERUSER
from nonebot.matcher import Matcher
from ujson import loads

talk_cmd = pc.poe_ai_talk_cmd
talk_p_cmd = pc.poe_ai_talk_p_cmd
reset_cmd = pc.poe_ai_reset_cmd
enable_cmd = pc.poe_ai_group_enable_cmd
__plugin_meta__ = PluginMetadata(
    name="talk with poe ai",
    description="Nonebot2 基于poe cookie登录AI聊天插件",
    type="application",
    homepage="https://github.com/nikissXI/nonebot_plugins/tree/main/nonebot_plugin_poe_ai",
    supported_adapters={"~onebot.v11"},
    usage=f"""插件命令如下
{talk_cmd}   # 开始对话，默认群里@机器人也可以
{talk_p_cmd}   # 沉浸式对话（仅限私聊）
{reset_cmd}   # 重置对话（不会重置预设）
{enable_cmd}   # 如果关闭所有群启用，则用这个命令启用
""",
)


def get_id(event: MessageEvent) -> str:
    """获取会话id"""
    if isinstance(event, GroupMessageEvent):
        if pc.poe_ai_group_share:
            id = f"{(event.group_id)}-share"
        else:
            id = f"{event.user_id}"
    else:
        id = f"{event.user_id}"
    # 记录id
    if id not in var.session_data:
        var.session_data[id] = ""
    return id


async def rule_check(event: MessageEvent, bot: Bot) -> bool:
    """对话响应判断"""

    # 获取纯文本
    text = event.get_plaintext().strip()

    if isinstance(event, GroupMessageEvent):
        # 判断是否启用
        if (
            pc.poe_ai_all_group_enable is False
            and event.group_id not in var.enable_group_list
        ):
            return False

        if pc.poe_ai_bot_qqnum_list != ["all"] and bot != var.handle_bot:
            return False

        # 仅艾特但没发内容
        if event.is_tome() and pc.poe_ai_talk_at:
            if text:
                return True
            else:
                return False

        # 判断命令前缀
        return text[: len(talk_cmd)] == talk_cmd

    elif isinstance(event, PrivateMessageEvent):
        # 判断命令前缀
        return text[: len(talk_cmd)] == talk_cmd

    return False


async def rule_check2(event: MessageEvent, bot: Bot) -> bool:
    """其他命令判断"""
    if not (
        isinstance(event, GroupMessageEvent) or isinstance(event, PrivateMessageEvent)
    ):
        return False

    if pc.poe_ai_bot_qqnum_list == ["all"]:
        return True
    else:
        return bot == var.handle_bot


async def rule_admin(event: MessageEvent, bot: Bot) -> bool:
    if pc.poe_ai_bot_qqnum_list != ["all"] and bot != var.handle_bot:
        return False
    if not await SUPERUSER(bot, event):
        return False
    return True


async def get_answer(matcher: Matcher, event: MessageEvent, q: str) -> str:
    # 获取用户id
    id = get_id(event)

    # 根据配置是否发出提示
    if pc.poe_ai_reply_notice:
        await matcher.send("响应中...")

    eop_id = var.session_data[id]
    if not eop_id:
        resp = await var.httpx_client.post(
            "/bot/create", json={"model": "ChatGPT", "prompt": "", "alias": id}
        )
        if resp.status_code != 200:
            await matcher.finish("创建chat出错" + resp.text)

        eop_id: str = resp.json()["eop_id"]
        var.session_data[id] = eop_id

    answer = ""
    async with var.httpx_client.stream(
        "POST", f"/bot/{eop_id}/talk", json={"q": q}
    ) as response:
        if response.status_code == 401:
            if await login():
                return "先前登录凭证失效，已更新，请重试"
            else:
                await matcher.finish("先前登录凭证失效，更新失败，请检查用户名和密码")

        if response.status_code == 402:
            var.session_data[id] = ""
            return "会话已重置，请重试"

        elif response.status_code != 200:
            await matcher.finish(f"出错 {response.status_code}")

        async for chunk in response.aiter_lines():
            text = loads(chunk)
            if text["type"] == "response":
                answer += text["data"]
            if text["type"] == "error":
                await matcher.finish("生成回答出错" + text["data"])

    return answer


#################
### 响应器
#################
talk = on_message(rule=rule_check)
talk_p = on_fullmatch(talk_p_cmd, rule=rule_check2)
reset = on_fullmatch(reset_cmd, rule=rule_check2)
enable_group = on_fullmatch(enable_cmd, rule=rule_admin)


@talk.handle()
async def _(matcher: Matcher, event: MessageEvent):
    # 获取信息
    text = unescape(event.get_plaintext().strip())
    # 把命令前缀截掉
    if text[: len(talk_cmd)] == talk_cmd:
        text = text[len(talk_cmd) :]
    # 无内容
    if not text:
        await talk.finish(
            f"""插件命令如下
{talk_cmd} 【内容】 # 发送问题，群里@机器人接内容也可以
{talk_p_cmd}  # 进入沉浸式对话模式，仅私聊可用
{reset_cmd}  # 清空聊天记录
"""
        )

    answer = await get_answer(matcher, event, text)
    await talk.finish(answer, at_sender=True)


@talk_p.got("msg", prompt="进入沉浸式对话模式，发送“退出”结束对话")
async def _(matcher: Matcher, event: PrivateMessageEvent):
    # 获取信息
    text = unescape(event.get_plaintext().strip())
    if text == "退出":
        await talk_p.finish("Bye~")

    answer = await get_answer(matcher, event, text)
    await talk_p.reject(answer)


@reset.handle()
async def _(event: MessageEvent):
    # 获取用户id
    id = get_id(event)
    eop_id = var.session_data[id]
    if not eop_id:
        await reset.finish("没聊过", at_sender=True)

    # 删除
    resp = await var.httpx_client.delete(f"/bot/{eop_id}")
    if resp.status_code != 204:
        await reset.finish("删除chat出错" + resp.text)

    await reset.finish("已清空聊天记录", at_sender=True)


@enable_group.handle()
async def _(event: GroupMessageEvent):
    if pc.poe_ai_all_group_enable is True:
        await enable_group.finish("当前配置是所有群都启用，此命令无效")

    if event.group_id in var.enable_group_list:
        var.enable_group_list.remove(event.group_id)
        await enable_group.finish("poe ai已禁用")
    else:
        var.enable_group_list.append(event.group_id)
        await enable_group.finish("poe ai已启用")
