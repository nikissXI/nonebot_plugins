from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent
from nonebot.permission import SUPERUSER
from .config import pc, var

talk_cmd = pc.eop_ai_talk_cmd
talk_p_cmd = pc.eop_ai_talk_p_cmd
reset_cmd = pc.eop_ai_reset_cmd
enable_cmd = pc.eop_ai_group_enable_cmd


async def rule_check(event: MessageEvent, bot: Bot) -> bool:
    """对话响应判断"""

    # 获取纯文本
    text = event.get_plaintext().strip()

    if isinstance(event, GroupMessageEvent):
        # 判断是否启用
        if (
            pc.eop_ai_all_group_enable is False
            and event.group_id not in var.enable_group_list
        ):
            return False

        if pc.eop_ai_bot_qqnum_list != ["all"] and bot != var.handle_bot:
            return False

        # 仅艾特但没发内容
        if event.is_tome() and pc.eop_ai_talk_at:
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

    if pc.eop_ai_bot_qqnum_list == ["all"]:
        return True
    else:
        return bot == var.handle_bot


async def rule_admin(event: MessageEvent, bot: Bot) -> bool:
    if pc.eop_ai_bot_qqnum_list != ["all"] and bot != var.handle_bot:
        return False
    if not await SUPERUSER(bot, event):
        return False
    return True
