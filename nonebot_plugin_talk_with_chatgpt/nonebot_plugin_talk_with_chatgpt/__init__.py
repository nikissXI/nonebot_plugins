from nonebot import on_message, on_fullmatch, on_regex
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from .config import pc, var
from .data_handle import req_chatgpt
from nonebot.params import RegexGroup

start_cmd = pc.talk_with_chatgpt_start_cmd
clear_cmd = pc.talk_with_chatgpt_clear_cmd
prompt_cmd = pc.talk_with_chatgpt_prompt_cmd

__plugin_meta__ = PluginMetadata(
    name="talk with chatgpt",
    description="一个简单的基于accessToken验证的ChatGpt对话插件",
    usage=f"""插件命令如下
{start_cmd}  # 开始对话，群里@机器人也可以
{clear_cmd}  # 重置对话（不会重置预设）
{prompt_cmd}  # 设置预设（人格），设置后会重置对话
""",
)


def get_id(event: MessageEvent) -> str:
    if isinstance(event, GroupMessageEvent):
        if pc.talk_with_chatgpt_group_share:
            id = f"{event.group_id}-share"
        else:
            id = f"{event.group_id}-{event.user_id}"
    elif isinstance(event, PrivateMessageEvent):
        id = str(event.user_id)
    else:
        id = ""
    # 记录id
    if id not in var.session_data:
        var.session_data[id] = ["", "", ""]
    return id


async def check_bot(event: MessageEvent, bot: Bot) -> bool:
    # bot判断
    return bot == var.handle_bot and (
        isinstance(event, GroupMessageEvent) or isinstance(event, PrivateMessageEvent)
    )


async def rule_check(event: MessageEvent, bot: Bot) -> bool:
    # bot判断
    if bot != var.handle_bot:
        return False
    # 获取纯文本
    text = event.get_plaintext().strip()

    if isinstance(event, GroupMessageEvent):
        # 仅艾特但没发内容
        if event.is_tome():
            if text:
                return True
            else:
                return False

        return text[: len(start_cmd)] == start_cmd

    elif isinstance(event, PrivateMessageEvent):
        # 判断前缀
        return text[: len(start_cmd)] == start_cmd

    return False


talk = on_message(rule=rule_check)


@talk.handle()
async def _(event: MessageEvent):
    # 获取用户id
    id = get_id(event)
    # 获取信息
    text = event.get_plaintext().strip()
    # 把命令前缀截掉
    if text[: len(start_cmd)] == start_cmd:
        text = text[len(start_cmd) :]
    # 无内容
    if not text:
        await prompt.finish(
            f"""插件命令如下
{start_cmd} 【内容】 # 开始对话，群里@机器人也可以
{clear_cmd}  # 重置对话（不会重置预设）
{prompt_cmd}  # 设置预设（人格），设置后会重置对话"""
        )
    # 根据配置是否发出提示
    if pc.talk_with_chatgpt_reply_notice:
        await talk.send("响应中...")
    result = await req_chatgpt(id, text)
    await talk.finish(result, at_sender=True)


clear = on_fullmatch(clear_cmd, rule=check_bot)


@clear.handle()
async def _(event: MessageEvent):
    # 获取用户id
    id = get_id(event)
    # 清空会话id
    var.session_data[id][0] = ""
    var.session_data[id][1] = ""
    await clear.finish("已重置会话", at_sender=True)


prompt = on_regex(rf"^{prompt_cmd}\s*([\s\S]*)?", rule=check_bot)


@prompt.handle()
async def _(event: MessageEvent, mp=RegexGroup()):
    # 获取用户id
    id = get_id(event)
    # 未提供参数
    if not mp[0]:
        user_prompt = var.session_data[id][2] if var.session_data[id][2] else "<未设置>"
        await prompt.finish(
            f"{prompt_cmd} 重置  # 重置预设\n{prompt_cmd} 【预设信息】  # 设置预设\n当前预设：\n{user_prompt}",
            at_sender=True,
        )
    text = mp[0].strip()
    # 重置
    if text.strip() == "重置":
        var.session_data[id] = ["", "", ""]
        await prompt.finish("已重置预设", at_sender=True)
    # 设置
    var.session_data[id][2] = text
    await prompt.send("设置中，请稍后...", at_sender=True)
    result = await req_chatgpt(id, text)
    await prompt.finish(f"<已设置预设>\n{result}", at_sender=True)
